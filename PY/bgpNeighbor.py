#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals


import re
import argparse
import pdb
import io
import os
import sys
import pyparsing as pp
import glob
from time import  strftime , localtime
import yaml
from pprint import pprint as ppr
from connexion import runActionCache , runListData , getHostsFromEnv , equipement
from ParsingShow import  ParseBgpTableXRStr , ParseBgpTableNxOSStr , ParseBgpTableXRAdvStr
import shutil

YML_PATH_BGPNEIGH="/home/d83071/yaml/bgpneigh/"
BCK_YML_PATH_BGPNEIGH="/home/d83071/yaml/bgpneigh/backup"

TMP="/home/d83071/TMP/BGPNEIGH/"


class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)
Loader__.add_constructor('!include', Loader__.include)

def saveFile(file,path):

	if not os.path.exists(file):
		return
	timestamp=strftime("%Y%m%d_%Hh%Mm%Ss", localtime())
	splitFilename=os.path.splitext(file)
	filenameBase=os.path.basename(file)
	extension=splitFilename[-1]
	newFileName=path+'/'+filenameBase+timestamp+extension
	shutil.copyfile(file, newFileName)
	

class bgpNeighbor(object):
	def __init__(self,hostname,ipNeighbor,vrf,renew=False,verbose=False):
		self.hostname=hostname
		self.ip=ipNeighbor
		ipStr=self.ip.replace('.','-')
		self.vrf=vrf
		self.ymlBgpNeighbor=YML_PATH_BGPNEIGH+self.hostname+'_'+self.vrf+'_'+ipStr+'.yml'
		self.attributeToSave=['hostname','ip','os','routes','advertisedRoutes']
		self.verbose=verbose
		
		if os.path.isfile(self.ymlBgpNeighbor):
			self.load()
		else:
			self.resync()
			renew=False
		if renew:
			self.resync()
	
	def __repr__(self):
		return f'{self.hostname}/{self.vrf}/{self.ip}'
	
	def __str__(self):
		return f'{self.hostname}/{self.vrf}/{self.ip}'		
	def getVersion(self):
		
		timeout=30
		dataList=[ {"hostname":self.hostname , 'commande':['sh version'] , "directory":TMP} ]
		versionsDict=runListData(dataList,verbose=False,timeout=100,parser=None)
		versions=versionsDict[self.hostname]['sh version']
		
		return versions	
	
	def getOS(self):
		version=self.getVersion()
		self.os='UNKNOWN'
		if  'XR Software' in version:
			self.os='XR'
		elif 'NX-OS' in version:
			self.os='NXOS'
		
	def save(self):
		saveFile(self.ymlBgpNeighbor,BCK_YML_PATH_BGPNEIGH)
		
		ctnNeigh={}
		
		for attr in self.__dir__():
			if attr in self.attributeToSave:
				valueToSave=getattr(self,attr)
				ctnNeigh[attr]=valueToSave
					
				
		print(f'Saving Data for {self.hostname}/{self.vrf}/{self.ip}:{self.ymlBgpNeighbor}... ')
		with open(self.ymlBgpNeighbor,'w') as yml_w:
			yaml.dump(ctnNeigh,yml_w ,default_flow_style=False)
		
	def load(self):
		dataYml={}
		with open(self.ymlBgpNeighbor, 'r') as yml__:
			dataYaml=yaml.load(yml__,Loader__)
			
		for attr,value in dataYaml.items():
			setattr(self,attr,value)
	
	def getBGPTableAdv(self):
		advertisedRoutes=[]
		commandCur=[]
		
		if self.os=='XR':
			commandCur=f'show bgp vrf {self.vrf} neighbors {self.ip} advertised-routes'
			parserCur=lambda y: ParseBgpTableXRAdvStr(y).asList()
		elif self.os=='NXOS':
			commandCur=f'show ip bgp vrf {self.vrf} neighbors {self.ip} advertised-routes'
			parserCur=lambda y: ParseBgpTableNxOSStr(y).asDict()['GRT']
		else:
			print('Unknown OS')
			return
		
		dataList=[ {"hostname":self.hostname, 'commande': commandCur, "directory":TMP} ]		
		
		advertisedRoutes=runListData(dataList,verbose=self.verbose,timeout=120,parser=parserCur)
		return advertisedRoutes[self.hostname]
		
	def getBGPTableRcv(self):
		advertisedRoutes=[]
		commandCur=[]
		
		if self.os=='XR':
			commandCur=f'show bgp vrf {self.vrf} neighbors {self.ip} routes'
			parserCur=lambda y: ParseBgpTableXRStr(y).asDict()[self.vrf]
		elif self.os=='NXOS':
			commandCur=f'show ip bgp vrf {self.vrf} neighbors {self.ip} routes'
			parserCur=lambda y: ParseBgpTableNxOSStr(y).asDict()['GRT']
		else:
			print('Unknown OS')
			return
		
		dataList=[ {"hostname":self.hostname, 'commande': commandCur, "directory":TMP} ]		
		
		routes=runListData(dataList,verbose=self.verbose,timeout=120,parser=parserCur)
		
		return routes[self.hostname]
		
	def getAllPrefixList(self,filterNH=[]):
	
		if filterNH and self.os=='XR':
			prefixesAdv=[ entry[0] for entry in self.advertisedRoutes if entry[2][0] not in filterNH] 
			prefixesRcv=[ entry[0] for entry in self.routes ]
			
		else:
			prefixesAdv=[ entry[0] for entry in self.advertisedRoutes ] 
			prefixesRcv=[ entry[0] for entry in self.routes ]			
		
		return {'routes':prefixesRcv, 'advertised-routes':prefixesAdv}
		
		
		
	def resync(self):
		self.getOS()
		self.advertisedRoutes=self.getBGPTableAdv()
		self.routes=self.getBGPTableRcv()
		self.save()
		
if __name__ == '__main__':
	"Extract BGP Neighbor informations"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-r","--router",action="store",help="Router hostname",required=True)
	parser.add_argument("-i","--ipaddress",action="store",help="BGP Neighbor Ipaddress",required=True)
	parser.add_argument("-v","--vrf" ,action="store", help="VRF",required=True)
	parser.add_argument("-s","--sync",action="store_true",default=False ,help="resync fabric data ",required=False)
	parser.add_argument("-V","--Verbose",action="store_true",dest='verbose',default=False ,help="resync fabric data ",required=False)

	args = parser.parse_args()
	
	BGPNeigh= bgpNeighbor(args.router,args.ipaddress,args.vrf,renew=args.sync,verbose=args.verbose)


		
		
	
		