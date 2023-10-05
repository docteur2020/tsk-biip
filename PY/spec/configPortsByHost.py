#!/bin/python3.8

import argparse
import pdb
import re
from pprint import pprint as ppr
import sys
import os

sys.path.insert(0,'/home/d83071/py')

from vxlanFabricConfig import equipmentConfig

DIR_CONFIG="/home/d83071/CONF"
DIR_TEMPLATE="/home/d83071/TEMPLATE/J2"
TEMPLATE={'mtu':'mtu-n9k.j2','vlan':'vlan-ios.j2'}

def initDataFile(file,param=None):
	
	result={}
	listPorts=[]
	entries=[]
	with open(file) as file_r:
		entries=file_r.read().split('\n')

	if param:
		otherParam=initParameters(param)
			
	for entry in entries:	
		lineLst=entry.split()
		hostname=lineLst[0]
		port=lineLst[1]
		
		if len(lineLst)==3:
			description=lineLst[2]
		else:
			description=""
		
		if hostname not in result:
			result[hostname]=[]
			
		
		
		if param:
			dataCur={'port':port , 'description':description}
			dataCur.update(otherParam)
			result[hostname].append(dataCur)
		else:
			result[hostname].append({'port':port , 'description':description})
		for hostname in result:
			result[hostname].sort(key=lambda y:y['port'])
		
	return result

def initParameters(params):
	paramDct={}
	for param in params:
		curList=param.split(':')
		paramDct[curList[0]]=curList[1]
		
	return paramDct
	
def genConfig(action,datas,params=None):

	config={}
	model=TEMPLATE[action]
	for hostname in datas:
		dataCur={'hostname': hostname  }
		if action=='mtu' or action=='vlan':
			dataCur.update({'ports': datas[hostname] })
		cfgObj=equipmentConfig('generic',dataCur,model)
		config[hostname]=cfgObj.getConfig()
	
	return config
	
def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
		
def writeCfg(configs,tag,directory='GENERIC'):
	dirCur=DIR_CONFIG+'/'+ directory +'/'+tag.upper()
	if not os.path.exists(dirCur):
		os.makedirs(dirCur)
		
	for leaf in configs:
		writeConfig(configs[leaf],dirCur+'/'+leaf.upper()+'.CFG')
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-f',"--file", help="Format:Host Port",required=True)
	parser.add_argument('-a',"--action", help="Action matching a Template for config ",required=True)
	parser.add_argument('-p',"--parameter",action="append",help="parameter:value",required=False)
	parser.add_argument("-t", "--tag",  action="store",help="tag to save result")

	args = parser.parse_args()
	
	if args.parameter:
		initDataFile=initDataFile(args.file,args.parameter)
	else:
		initDataFile=initDataFile(args.file)
	
	cfgHostname=genConfig(args.action,initDataFile)
	

	if args.tag:
		writeCfg(cfgHostname,args.tag)
	

			
