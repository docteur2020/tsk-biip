#!/usr/bin/env python3.8
# coding: utf-8

import os
from time import  strftime , localtime , ctime
import sys
import pickle
import glob
import argparse
import pdb
import pprint
from ParsingShow import ParsePortChannelCisco , ParseStatusCisco , ParseSwitchPortString , ParsePortChannelCiscoFile , ParseStatusCiscoFile , ParseSwitchPort , ParseMacCisco, ParseMacCiscoFile , ParseShFexString , ParseShFex ,ParseBgpTable ,ParseBgpTableString, ParseIpRouteStr, ParseIpRoute
from connexion import *
from dictdiffer import diff
from ruamel.yaml import YAML

COMMANDES={ 'PORT-CHANNEL':{ 'commandes':'sh port-channel summary' , 'parserStr':ParsePortChannelCisco,'parserFile':ParsePortChannelCiscoFile } ,\
			'STATUS':{ 'commandes':'sh interface status' , 'parserStr':ParseStatusCisco,'parserFile':ParseStatusCiscoFile} ,\
			'SWITCHPORT':{ 'commandes':'sh interface switchport' , 'parserStr':ParseSwitchPortString,'parserFile':ParseSwitchPort},\
			'FEX':{ 'commandes':'sh fex' , 'parserStr':ParseShFexString,'parserFile':ParseShFex},\
			'MAC':{ 'commandes':'sh mac address-table','parserStr':ParseMacCisco,'parserFile':ParseMacCiscoFile},\
			'ROUTE':{ 'commandes':'sh ip route','parserStr':ParseIpRouteStr,'parserFile':ParseIpRoute},\
			'ROUTE-XR':{ 'commandes':'sh route','parserStr':ParseIpRouteStr,'parserFile':ParseIpRoute},\
			'BGPTABLE':{'commandes':'sh ip bgp','parserStr':ParseBgpTableString,'parserFile':ParseBgpTable}}



DEFAULT_CACHE_DIR='/home/x112097/TMP/CACHE'

def print_diff(list_diff):
	resultat=[]
	for entry in list_diff:
		resultat.append(entry)
				
	return resultat
				
class Cache(object):
	def __init__(self,tag,suffix=".db",targetDir=DEFAULT_CACHE_DIR,initValue=None):
		
		self.tag=tag
		self.targetDir="%s/%s"%(targetDir,tag)
		
		if not os.path.exists(self.targetDir):
			os.makedirs(self.targetDir)

		self.suffix=suffix
		
		if initValue:
			self.save(initValue)
			
		if self.isOK():
			self.value=self.load()
		else:
			self.value=None
			
	def isOK(self,aging=0):
	

		if glob.glob(self.targetDir+'/*.db'):
			if aging:
				age_cur=self.get_age()
			
				if age_cur>aging:
					file_cur=self.get_last_dump()
					print(f'{file_cur}:Cache too old than {aging}s')
					return False
					
				'stop'
			return True
		else:
			return False
		
	
	def load(self,fileCache=None):
	
		if fileCache:
			loadFile=fileCache
		else:
			loadFile=self.get_last_dump()
			
		try:
			f=open(loadFile,'rb')
		except:
			raise ValueError("/!\\ Je ne parviens pas a ouvrir le fichier DB '%s' /!\\"%loadFile)
	
	
		if 'jsonpickle' in sys.modules.keys():
			# On utilise json par defaut sauf si pas present
			try:
				jsonObj=f.read()
				db=jsonpickle.decode(jsonObj)
			except:
				raise ValueError("/!\\ Erreur lors du chargement del DB : pas bon format ? /!\\")
		else:
			try:
				db=pickle.load(f)
			except:
				raise ValueError (f"/!\\ Erreur lors du chargement de la DB {f} : pas bon format ? /!\\")
	
		f.close()
	
		return db
		
	@staticmethod
	def readDB(filedb):
		try:
			f=open(filedb,'rb')
		except:
			raise ValueError("/!\\ Je ne parviens pas a ouvrir le fichier DB '%s' /!\\"%filedb)
	
	
		if 'jsonpickle' in sys.modules.keys():
			# On utilise json par defaut sauf si pas present
			try:
				jsonObj=f.read()
				db=jsonpickle.decode(jsonObj)
			except:
				raise ValueError("/!\\ Erreur lors du chargement del DB : pas bon format ? /!\\")
		else:
			try:
				db=pickle.load(f)
			except:
				raise ValueError ("/!\\ Erreur lors du chargement de la DB : pas bon format ? /!\\")
				
		pprint.pprint(db)
		
		
			
		f.close()
		
		return db
		
	@staticmethod
	def readDB__only(filedb):
		try:
			f=open(filedb,'rb')
		except:
			raise ValueError("/!\\ Je ne parviens pas a ouvrir le fichier DB '%s' /!\\"%filedb)
	
	
		if 'jsonpickle' in sys.modules.keys():
			# On utilise json par defaut sauf si pas present
			try:
				jsonObj=f.read()
				db=jsonpickle.decode(jsonObj)
			except:
				raise ValueError("/!\\ Erreur lors du chargement del DB : pas bon format ? /!\\")
		else:
			try:
				db=pickle.load(f)
			except:
				raise ValueError ("/!\\ Erreur lors du chargement de la DB : pas bon format ? /!\\")
				
			
		f.close()
		
		return db
	
	def save(self,value):
		timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		self.target="%s/cache%s%s"%(self.targetDir,timestamp,self.suffix)
		if os.path.exists(self.target):
			try:
				os.remove(self.target)
			except:
				pass
		try:
			f=open(self.target,'wb')
		except:
			raise ValueError("/!\\ Impossible de creer le fichier de DB /!\\ : "+self.target)
	
		if 'jsonpickle' in sys.modules.keys():
			try:
				jsonObj=jsonpickle.encode(value)
				f.write(jsonObj)
			except:
				f.close() 
				raise ValueError("/!\\ Pb lors du dump de la DB /!\\")
		else:
			try:
				pickle.dump(value,f)
			except:
				f.close()
				raise ValueError("/!\\ Pb lors du dump de la DB /!\\")
		f.close()
		
	def get_last_dump(self):
		return max(glob.glob(self.targetDir+'/*.db'),key=os.path.getctime)
		
	def get_timestamp(self):
		return ctime(os.path.getmtime(max(glob.glob(self.targetDir+'/*.db'),key=os.path.getctime)))
		
	def getValue(self):
		return self.value
		
	def get_age(self):
		file_cur=self.get_last_dump()
		return time.time() - os.path.getmtime(file_cur)
		
	def __str__(self):
		return str(self.value)
		
	def __repr__(self):
		return str(self.value)
		
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("--tag", action="store",help="tag du cache",required=False)
	group1.add_argument("--read", action="store",help="Lecture d'un cache",required=False)
	group1.add_argument("--diff", action="store",help="Lecture d'un cache pour différence",required=False)
	parser.add_argument("-P", "--Print",action="store_true",help="Affichage",required=False)
	parser.add_argument("--set-from-commande",dest='hostname',default=None,action="store",help="Equipement sur lequel lancer la commande",required=False)
	parser.add_argument("--set-from-file",dest='outputFile',default=None,action="store",help="Fichier à parser",required=False)
	parser.add_argument("--vrf",action="store",help="action ",required=False)
	parser.add_argument("-a","--action",action="store",help="action ",required=False)
	parser.add_argument("--other",action="store",help="Uniquement avec diff autre cache pour comparaison",required=False)
	parser.add_argument("--save-as-yaml",dest='saveyaml',action="store",help="Save to yaml file, only with --read",required=False)
	args = parser.parse_args()
	
	if args.tag:
		if ( args.outputFile or args.hostname) and not args.action:
			raise argparse.ArgumentTypeError('les options --set-... nécessite une action')
	
		elif args.action:
			if args.action not in COMMANDES.keys():
				raise ValueError('Action non supportée\nLes actions supportés sont:'+ "\n - ".join([ com for com in COMMANDES.keys()]) )
				
		cache__=Cache(args.tag)
			
		if args.Print:
			pprint.pprint(str(cache__))
		
		if args.hostname:
			if not args.vrf:
				value_cur=comSbe.ResultCommande.getCommande(args.hostname,COMMANDES[args.action]['commandes'],COMMANDES[args.action]['parserStr'])
			else:
				value_cur=comSbe.ResultCommande.getCommande(args.hostname,COMMANDES[args.action]['commandes']+" vrf "+args.vrf,COMMANDES[args.action]['parserStr'])			
			cache__.save(value_cur)
			
		if args.outputFile:
			value_cur=COMMANDES[args.action]['parserFile'](args.outputFile)
			cache__.save(value_cur)
			
	elif args.read:
		Cache.readDB(args.read)
		
		if args.saveyaml:
			cache_cur=Cache.readDB__only(args.read)
			with open(args.saveyaml, 'w') as outfile:
				yaml=YAML()
				yaml.indent(mapping=4, sequence=6, offset=3)
				yaml.dump(cache_cur, outfile)
		
		
	elif args.diff:
		if args.other:
			cache1=Cache.readDB__only(args.diff)
			cache2=Cache.readDB__only(args.other)
			pprint.pprint(print_diff(diff(cache1,cache2)))
		else:
			raise argparse.ArgumentTypeError('--diff nécessite --other')
	


