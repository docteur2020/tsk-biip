#!/usr/bin/env python3.8
# coding: utf-8



import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
import csv
from getIfStatus import groupInterface
import io
import os

CONFIG_DIR='/home/d83071/CONF/SHUT/'

def readCsv(csvFilename):
	result=[]

	with open(csvFilename, newline='') as csvFile:
		spamreader = csv.reader(csvFile, delimiter=';', quotechar='|')
		for row in spamreader:
			result.append([ t.strip() for t in row] )
				
	return result
	
	
def parseSortIf(ifs):
	#pdb.set_trace()
	#return int(ifs.replace('Eth','').replace('/',''))
	
	return ifs

def groupIfByHostname(intercos,notGrouped=False):
	ifByHost={}
	for interco in intercos:
		hostA=interco[0]
		hostB=interco[2]
		ifA=interco[1]
		ifB=interco[3]
		
		if hostA not in ifByHost:
			ifByHost[hostA]=[]
		if hostB not in ifByHost:
			ifByHost[hostB]=[]			
		
		if ifA not in ifByHost[hostA]:
			ifByHost[hostA].append(ifA)
			
		if ifB not in ifByHost[hostB]:
			ifByHost[hostB].append(ifB)	
			
	if notGrouped:
		return ifByHost
			
	ifByHostGrouped={ key:groupInterface(value)   for key,value in ifByHost.items()}
	
	return ifByHostGrouped
	
def getConfig(ifByHostGrouped,activate=True):
	configByHost={}
	ioStreamByHost={}
	for hostname in ifByHostGrouped:
		ioStreamByHost[hostname]=io.StringIO()
		for ifs in ifByHostGrouped[hostname]:
			ioStreamByHost[hostname].write(f'interface {ifs}\n')	
			ioStreamByHost[hostname].write(f' no switchport\n')
			if activate:
				ioStreamByHost[hostname].write(f' no shut\n\n')
			else:
				ioStreamByHost[hostname].write(f' shut\n\n')
		configByHost[hostname]=ioStreamByHost[hostname].getvalue()
		ioStreamByHost[hostname].close()
	return configByHost

def writeCfg(configByHost,directory):
	for hostname in configByHost:
		fichier=directory+'/'+hostname+'.CFG'
		with open(fichier,'w+') as Configfile:
			Configfile.write(configByHost[hostname])
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument("-c","--csv",action="store",help="hostname",required=True)
	group.add_argument("--shutdown",action="store_true",default=True, help="get shut down config")
	group.add_argument("--activate",action="store_true",default=False,help="get no shut down config")
	parser.add_argument("-d","--directory",action="store",default='TMP',help="directory to save config",required=True)
	args = parser.parse_args()
	
	interco=readCsv(args.csv)
	ifByHostGrouped=groupIfByHostname(interco)
	configByHost= getConfig(ifByHostGrouped,activate=args.activate or args.shutdown)
	dirCur=CONFIG_DIR+args.directory
	if not os.path.exists(dirCur):
		os.makedirs(dirCur)
	writeCfg(configByHost,dirCur)