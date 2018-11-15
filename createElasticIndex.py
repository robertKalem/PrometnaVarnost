'''
==============================
Title: createElasticIndex
Author: Robert Kalem
Date: 15 Nov 2018
==============================

This is a script for parsing and importing data to Elasticsearch index.

Usage: 
    python3 createElasticIndex.py indexName pathToData

Arguments pathToData and indexName are optional, 
    the default path is "./Podatki" and default indexName is "prometnavarnost".

Argument indexName will be converted to lowercase, due to Elasticsearch regulations.
'''

import sys
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, streaming_bulk
import os
es=Elasticsearch([{'host':'localhost','port':'9200'}])

es

if (len(sys.argv)>1):
    indexName = sys.argv[1].lower()
else:
    indexName = "prometnavarnost"

if (len(sys.argv)>2):
    pathToData = sys.argv[2]
else:
    pathToData = "./Podatki"


def date_to_date(Date):
    calendar = Date.split(".")
    newDate = calendar[2]+"-"+calendar[1]+"-"+calendar[0]
    return newDate


def import_data(myPath, index_name, doc_type_name="en"):

    i=1
    lineNum=0
    subfolders = [dI for dI in os.listdir(myPath) if os.path.isdir(os.path.join(myPath,dI))]

    for folder in subfolders:
        if folder.startswith('pn'):
            year = folder[2:]
            # tu notri so vneseni vsi podatki za posamezno leto

            # for loop cez file s podatki (2011-2017) // za ostale bo drugacno iskanje
            # v letu 2014 je prometna nesreca z 92 udelezenci, kar povzroci error v ELasticsearchu
            # zato to leto zaenkrat prefiltriram
            if (year >= '2011' and year != '2014'):
                dataFiles = [fI for fI in os.listdir(myPath+'/'+folder) if os.path.isfile(os.path.join(myPath+'/'+folder, fI))]
                for each in dataFiles:
                    if each[12:] == 'dogodki.txt':
                        
                        file = open( myPath+'/'+folder+'/'+each, 'r', encoding='utf-8', errors='ignore')
                        dogodkiLines = file.readlines()

                        file = open( myPath+'/'+folder+'/'+each[:12]+'osebe.txt', 'r', encoding='utf-8', errors='ignore')
                        osebeLines = file.readlines()

                        lineNum = 0
                        osebeLineIndex = 1      # vrstice z indexom 0 ne potrebujemo

                        for line in dogodkiLines:
                            
                            print("Parsing line: \n", line)

                            if(lineNum!=0):     # prvo vrstico vedno preskocimo
                                dataList = line.split('$')

                                FIOStevilkaZadeve = dataList[0]
                                KlasifikacijaNesrece = dataList[1]
                                UpravnaEnota = dataList[2]
                                DatumPN = date_to_date(dataList[3])
                                UraPN = dataList[4]
                                VNaselju = dataList[5]
                                Lokacija = dataList[6]
                                VrstaCesteNaselja = dataList[7]
                                SifraCesteNaselja = dataList[8]
                                TekstCesteNaselja = dataList[9]
                                SifraOdsekaUlice = dataList[10]
                                TekstOdsekaUlice = dataList[11]
                                StacionazaDogodka = dataList[12]
                                OpisKraja = dataList[13]
                                VzrokNesrece = dataList[14]
                                TipNesrece = dataList[15]
                                VremenskeOkoliscine = dataList[16]
                                StanjePrometa = dataList[17]
                                StanjeVozisca = dataList[18]
                                VrstaVozisca = dataList[19]
                                GeoKoordinataX = int(dataList[20])
                                GeoKoordinataY = int(dataList[21])
            
                                indexDodajanegaPovzrocitelja = 1        # za locevanje povzrociteljev PN
                                indexDodajanegaUdelezenca = 1           # za locevanje udelezencev PN

                                udelezenci = {}                         # slovar udelezencev
                                povzrocitelji = {}                      # slovar povzrociteljev

                                while osebeLines[osebeLineIndex].split("$")[0] == FIOStevilkaZadeve:  

                                    osebeDataList = osebeLines[osebeLineIndex].split("$")

                                    if (osebeDataList[1] == "POVZROITELJ"):
                                        povzrocitelji['Povzrocitelj'+str(indexDodajanegaPovzrocitelja)] =  { 
                                            "Starost" : int(osebeDataList[2]),
                                            "Spol" : osebeDataList[3],
                                            "UEStalnegaPrebivalisca" : osebeDataList[4],
                                            "Drzavljanstvo" : osebeDataList[5],
                                            "PoskodbaUdelezenca" : osebeDataList[6],
                                            "VrstaUdelezenca" : osebeDataList[7],
                                            "UporabaVarnostnegaPasu" : osebeDataList[8],
                                            "VozniskiStazVLetih" : int(osebeDataList[9]),
                                            "VozniskiStazVMesecih" : int(osebeDataList[10]),
                                            "VrednostAlkotesta" : float(osebeDataList[11].replace(',', '.')),
                                            "VrednostStrokovnegaPregleda" : float(osebeDataList[12].replace(',', '.'))
                                        }
                                        indexDodajanegaPovzrocitelja += 1

                                    elif (osebeDataList[1] == "UDELEENEC"):
                                        udelezenci['Udelezenec'+str(indexDodajanegaUdelezenca)] =  {
                                            "Starost" : int(osebeDataList[2]),
                                            "Spol" : osebeDataList[3],
                                            "UEStalnegaPrebivalisca" : osebeDataList[4],
                                            "Drzavljanstvo" : osebeDataList[5],
                                            "PoskodbaUdelezenca" : osebeDataList[6],
                                            "VrstaUdelezenca" : osebeDataList[7],
                                            "UporabaVarnostnegaPasu" : osebeDataList[8],
                                            "VozniskiStazVLetih" : int(osebeDataList[9]),
                                            "VozniskiStazVMesecih" : int(osebeDataList[10]),
                                            "VrednostAlkotesta" : float(osebeDataList[11].replace(',', '.')),
                                            "VrednostStrokovnegaPregleda" : float(osebeDataList[12].replace(',', '.'))
                                        }
                                        indexDodajanegaUdelezenca += 1

                                    if (osebeLineIndex+1 != len(osebeLines) ):
                                        osebeLineIndex+=1
                                    else:
                                        break;

                                yield {
                                    "_index": index_name,
                                    "_type": "dogodek",
                                    "Leto":  int(year),
                                    "StevilkaZadeve": int(FIOStevilkaZadeve),
                                    "KlasifikacijaNesrece": KlasifikacijaNesrece,
                                    "UpravnaEnota": UpravnaEnota,
                                    "DatumPN": DatumPN,
                                    "UraPN": int(UraPN),
                                    "VNaselju": VNaselju,
                                    "Lokacija": Lokacija,
                                    "VrstaCesteNaselja": VrstaCesteNaselja,
                                    "SifraCesteNaselja": SifraCesteNaselja,
                                    "TekstCesteNaselja": TekstCesteNaselja,
                                    "SifraOdsekaUlice": int(SifraOdsekaUlice),
                                    "TekstOdsekaUlice": TekstOdsekaUlice,
                                    "StacionazaDogodka": int(StacionazaDogodka),
                                    "OpisKraja": OpisKraja,
                                    "VzrokNesrece": VzrokNesrece,
                                    "TipNesrece": TipNesrece,
                                    "VremenskeOkoliscine": VremenskeOkoliscine,
                                    "StanjePrometa": StanjePrometa,
                                    "StanjeVozisca": StanjeVozisca,
                                    "VrstaVozisca": VrstaVozisca,
                                    "GeoKoordinataX": GeoKoordinataX,   #formatting?
                                    "GeoKoordinataY": GeoKoordinataY,   #formatting?
                                    "SteviloUdelezencev": indexDodajanegaPovzrocitelja+indexDodajanegaUdelezenca-2,
                                    "Povzrocitelj" : povzrocitelji,     # slovar, ki vsebuje slovarje
                                    "Udelezenec" : udelezenci           # slovar, ki vsebuje slovarje
                                    }
                                i+=1
                            lineNum+=1

                    
output, _ = bulk(es, import_data(pathToData, indexName))
print('Indexed %d elements' % output)


