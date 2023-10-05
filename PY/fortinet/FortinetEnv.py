#!/usr/bin/env python3.8
# coding: utf-8


import argparse
from pprint import pprint as ppr
from ParserFortinet import *
from netaddr import IPNetwork , iter_iprange
from time import gmtime, strftime , localtime
import sys
sys.path.insert(0,'/home/d83071/py')
import cache as cc
import os
import yaml
from ruamel.yaml import YAML
from itertools import product

PATH_POL_DUMP="/home/d83071/yaml/fortinet/pol"
PATH_RESULT_DUMP="/home/d83071/yaml/fortinet/result"
	
yaml.Dumper.ignore_aliases = lambda *args : True

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet
		
class FortinetFwError(Exception):
	"Classe Exception pour grep-ip"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		self.message[0]=u'Vdom unknown:'+value1
		super(FortinetFwError, self).__init__(self.message[code])
		
def saveResult(result,saveName):
		suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
		filename=PATH_RESULT_DUMP+'/'+saveName+suffix
		with open(filename,'w') as yml_w:
			 yaml.dump(result,yml_w ,default_flow_style=False)


class FortinetFw(object):

	def __init__(self,FileConfig="",dump="",caching=False,path=PATH_POL_DUMP,dataDict={}):
		"Constructor"
		self.pathPolDump=path
		if FileConfig:
			self.fwName=os.path.basename(FileConfig).split('.')[0]
			self.tag="POLICY_FORTINET_"+self.fwName
			self.config=FileConfig
			cachePolFw=cc.Cache(self.tag)
			dataPolFw=cachePolFw.getValue()
			if not caching:
				self.address=ParseFortigateAddr(FileConfig,mode='file')
				self.grpAddr=ParseFortigateGrpAddr(FileConfig,mode='file')
				self.rules=ParseFortigateRule(FileConfig,mode='file')
				self.staticRoutes=ParseFortigateStaticRoute(FileConfig,mode='file')
				self.interfaces=ParseFortigateInterface(FileConfig,mode='file')
				cachePolFw.save({'address': self.address, 'groups': self.grpAddr, 'rules': self.rules,'static_routes':self.staticRoutes,'interfaces':self.interfaces})
			else:
				if cachePolFw.isOK():
					print('Cache Info Policy is used for',self.fwName)
					self.address=dataPolFw['address']
					self.grpAddr=dataPolFw['groups']
					self.rules=dataPolFw['rules']
					self.interfaces=dataPolFw['interfaces']
					try:
						self.staticRoutes=dataPolFw['static_routes']
					except KeyError as E:
						print(E)
						self.staticRoutes=ParseFortigateStaticRoute(FileConfig,mode='file')
						cachePolFw.save({'address': self.address, 'groups': self.grpAddr, 'rules': self.rules,'static_routes':self.staticRoutes,'interfaces':self.interfaces})
				else:
					self.address=ParseFortigateAddr(FileConfig,mode='file')
					self.grpAddr=ParseFortigateGrpAddr(FileConfig,mode='file')
					self.rules=ParseFortigateRule(FileConfig,mode='file')
					self.staticRoutes=ParseFortigateStaticRoute(FileConfig,mode='file')
					self.interfaces=ParseFortigateInterface(FileConfig,mode='file')
					cachePolFw.save({'address': self.address, 'groups': self.grpAddr, 'rules': self.rules, 'static_routes':self.staticRoutes,'interfaces':self.interfaces})
				
		if dump:
			with open(dump, 'r' ) as pol_yml:
				self.load(pol_yml)
				
		if dataDict:
			self.address=dataDict['address']
			self.grpAddr=dataDict['groups']
			self.rules=dataDict['rules']
	
		self.initObjAddress()
	
	def load(self,dump):
		dataPolFW=yaml.load(dump,Loader=yaml.SafeLoader)
		self.address=dataPolFw['address']
		self.grpAddr=dataPolFw['groups']
		self.rules=dataPolFw['rules']
		self.interfaces=dataPolFw['interfaces']
		self.staticRoutes=dataPolFw['static_routes']
		
	def save(self,name):
		suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
		filename=self.pathPolDump+'/'+name+suffix
		with open(filename,'w') as yml_w:
			yaml.dump({'address':self.address,'groups':self.grpAddr,'rules':self.rules},yml_w,width=500, indent=2)
		
	def initObjAddress(self):
		"address object"
		self.addressObj={}
		for vdom in self.address:
			self.addressObj[vdom]={}
			for address__ in self.address[vdom]:
				if 'subnet' in self.address[vdom][address__]:
					NetCurList=self.address[vdom][address__]['subnet'].split()
					NetCur=NetCurList[0]+'/'+NetCurList[1]
					self.addressObj[vdom][address__]={'type':'subnet' , 'ipObj':IPNetwork(NetCur), 'content':self.address[vdom][address__] }
				elif 'start-ip' in self.address[vdom][address__]:
					listIPCur=list(iter_iprange(self.address[vdom][address__]['start-ip'], self.address[vdom][address__]['end-ip']))
					self.addressObj[vdom][address__]={'type':'range' , 'ipObj':listIPCur, 'content':self.address[vdom][address__] }
				else:
					self.addressObj[vdom][address__]={'type':'None' , 'ipObj':None, 'content':self.address[vdom][address__] }
					
		
	def testNetinAddr(self,netStr,addrObj,mode='normal'):
		try:
			netObj=IPNetwork(netStr)
		except core.AddrFormatError as E:
			pdb.set_trace()
			print(E)
		if mode=='normal':
			try:
				if addrObj['type']=='subnet':
					if netObj in  addrObj['ipObj'] or  addrObj['ipObj'] in netObj :
						return True
					else:
						return False
				elif addrObj['type']=='range':
					resultat=False
					for ip__ in addrObj['ipObj']:
						if ip__ in netObj:
							resulat=True
							break
					return resultat
						
				elif addrObj['type']=='range':
					return None
			except KeyError as e:
				pdb.set_trace()
				print(e)
				raise(e)
				
	def testNetinNetwork(self,netStr,netCur,mode='normal'):
		try:
			netObj=IPNetwork(netStr)
		except core.AddrFormatError as E:
			pdb.set_trace()
			print(E)
			
		try:
			netCurObj=IPNetwork("/".join(netCur))
		except core.AddrFormatError as E:
			pdb.set_trace()
			print(E)
		if mode=='normal':
			return netObj in  netCurObj or  netCurObj in netObj

				
	def testListGrpContainsOnlyAddr(self,ListGrpOrAddr,vdom	):
	
		try:
			self.grpAddr[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains address")
			return False
			
		resultat=True
		for GrpOrAddr in ListGrpOrAddr:
			if GrpOrAddr in self.grpAddr[vdom]:
				resultat=False
				break
				
		return resultat
				
	def explodeGrp(self,grpName,vdom):
		try:
			self.grpAddr[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains group address")
			return []
			
		if grpName in self.grpAddr[vdom]:
			resultat=self.grpAddr[vdom][grpName]['member']
			
			while not self.testListGrpContainsOnlyAddr(resultat,vdom):
				list_tmp=resultat.copy()
				resultat=[]
				for GrpOrAddr in list_tmp:
					if GrpOrAddr in self.grpAddr[vdom]:
						resultat+=self.grpAddr[vdom][GrpOrAddr]['member']
					else:
						resultat.append(GrpOrAddr)
		else:		
			print("Group Name unknown or not configured:"+grpName,'vdom:',vdom)
			return []
			
		return resultat
		
		
	def explodeListGrp(self,grpNameList,vdom):
		try:
			self.grpAddr[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains group address")
			return []
			
		FinalResultat=[]
		for grpName in grpNameList:
			typeCur=self.getTypeObj(grpName,vdom)
			
			if typeCur=='group':
				resultat=self.explodeGrp(grpName,vdom)
			else:
				resultat=[grpName]
		
			for addr__ in resultat:
				if addr__ not in FinalResultat:
					FinalResultat.append(addr__)
					
			
		return FinalResultat
	
	def testNetinGrp(self,netStr,grpName,vdom,mode='normal'):
	
		try:
			self.grpAddr[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains group address")
			return False
		try:
			grpContent=self.grpAddr[vdom][grpName]
		except KeyError as e:
			print(e)
			print("Group Name unknown or not configured")
			pdb.set_trace()
			return False
		
		ListAddr=self.explodeGrp(grpName,vdom)
		resultat=False
		for Addr in ListAddr:
			if self.testNetinAddr(netStr,self.addressObj[vdom][Addr],mode):
				resultat=True
				break
			
		return resultat
		
	def testNetinRoute(self,netStr,RouteId,vdom,mode='normal'):
	
		try:
			self.staticRoutes[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains group address")
			return False
		try:
			routeContent=self.staticRoutes[vdom][RouteId]
			
			try:
				resultat=self.testNetinNetwork(netStr,routeContent['dst'],mode=mode)
			except KeyError as E:
				print(E)
				print('default route')
				self.staticRoutes[vdom][RouteId]['dst']=['0.0.0.0','0.0.0.0']
				return True
			
			return resultat
		except KeyError as e:
			print(e)
			print("route id unknown or not configured")
			pdb.set_trace()
			return False
		
		resultat=False
		
			
		return resultat
		
	def filterAddr(self,netStr,vdom,AddrName,mode='normal'):
		resultat={}
		
		if self.testNetinAddr(netStr,self.addressObj[vdom][AddrName],mode=mode):
			resultat=self.address[vdom][AddrName]
		
		return resultat
		
	def filterAddrList(self,netStrList,vdom,AddrName,mode='normal'):
		resultat={}
		for netStr in netStrList:
			if self.testNetinAddr(netStr,self.addressObj[vdom][AddrName],mode=mode):
				resultat=self.address[vdom][AddrName]
				break
		
		return resultat
		
	def filterGrpAddr(self,netStr,vdom,GrpName,mode='normal',suppressMember=False):
		resultat={}
		
		if not suppressMember:
			if self.testNetinGrp(netStr,GrpName,vdom,mode=mode):
				resultat=self.grpAddr[vdom][GrpName]
		
		return resultat
		
	def filterGrpAddrList(self,netStrList,vdom,GrpName,mode='normal',suppressMember=False):
		resultat={}
		
		for netStr in netStrList:
			if not suppressMember:
				if self.testNetinGrp(netStr,GrpName,vdom,mode=mode):
					resultat=self.grpAddr[vdom][GrpName]
					break
		
		return resultat
		
	def filterStaticRoute(self,netStr,vdom,mode='normal'):
		resultat={}
		
		for route in self.staticRoutes[vdom]:
			if self.testNetinRoute(netStr,route,vdom,mode='normal'):
				resultat[route]=self.staticRoutes[vdom][route]
				
		return resultat
		
	def filterStaticRouteList(self,netStrList,vdom,mode='normal'):
	
		resultat={}
		
		for route in self.staticRoutes[vdom]:
			for netStr in netStrList:
				if self.testNetinRoute(netStr,route,vdom,mode='normal'):
					resultat[route]=self.staticRoutes[vdom][route]
					break
		
		return resultat
		
	def filterListAddr(self,netStr,vdom,mode='normal'):
		resultat=[]
		if mode=='normal':
			for addr in self.addressObj[vdom]:
				if self.testNetinAddr(netStr,self.addressObj[vdom][addr]):
					resultat.append(addr)
		return resultat
		
	def filterListAddrList(self,netStrList,vdom,mode='normal'):
		resultat=[]
		if mode=='normal':
			for addr in self.addressObj[vdom]:
				if self.testNetinAddr(netStr,self.addressObj[vdom][addr]):
					resultat.append(addr)
		return resultat
		
	def filterListGrpAddr(self,netStr,vdom,mode='normal'):
		resultat=[]
		if mode=='normal':
			for grpName in self.grpAddr[vdom]:
				if self.testNetinGrp(netStr,grpName,vdom,mode=mode):
					if grpName not in resultat:
						resultat.append(grpName)
					break
		return resultat
		
	def filterListGrpAddrList(self,netStrList,vdom,mode='normal',suppressMember=False):
		
		if mode=='normal':
			resultat=[]
			if not suppressMember:
				for netStr in netStrList:
					for grpName in self.grpAddr[vdom]:
						if self.testNetinGrp(netStr,grpName,vdom,mode=mode):
							if grpName not in resultat:
								resultat.append(grpName)
							break
			else:
				resultat={}
				for grpName in self.grpAddr[vdom]:
					for netStr in netStrList:
						if self.testNetinGrp(netStr,grpName,vdom,mode=mode):
							if grpName not in resultat:
								resultat[grpName]=[netStr]
							else:
								resultat[grpName].append(netStr)

		return resultat
		
	def getTypeObj(self,GrpOrAddrName,vdom):
		TypeObj="Unknown"
		if GrpOrAddrName in self.grpAddr[vdom]:
			TypeObj="group"
		elif GrpOrAddrName in self.address[vdom]:
			TypeObj="address"
			
		if TypeObj=="Unknown":
			pdb.set_trace()
			print('warning ',GrpOrAddrName, ' unknown type object')
			
		return TypeObj
		
	def matchListGrpOrAddr(self,netStr,listObj,vdom,mode='normal'):
		resultat=False
		
		if mode=='normal':
			for objName in listObj:
				typeCur=self.getTypeObj(objName,vdom)
				if typeCur=='group':
					resultat=self.testNetinGrp(netStr,objName,vdom,mode='normal')
				elif typeCur=='address':
					resultat=self.testNetinAddr(netStr,self.addressObj[vdom][objName],mode='normal')
				else:
					#pdb.set_trace()
					print('warning for object:',objName)
				if resultat:
					return resultat
					
		elif mode=='list':
			resultatList=[]
			for net__ in netStr:
				pdb.set_trace()
				for objName in listObj:
					typeCur=self.getTypeObj(objName,vdom)
					if typeCur=='group':
						resultat_cur=self.testNetinGrp(net__,objName,vdom,mode='normal')
					elif typeCur=='address':
						resultat_cur=self.testNetinAddr(net__,self.addressObj[vdom][objName],mode='normal')
					else:
						pdb.set_trace()
						print('warning for object:',objName)
				resultatList.append(resultat_cur)
				
			resultat=True
			for resultat__ in resultatList:
				resultat=resultat and resultat__
		
		return resultat
				
	def filterListRules(self,netStr,vdom,mode='normal',savefile="",objectAddressImpacted={},ifs=[]):
		resultat={}
		
		if  mode=='getObjImpacted':
			objectAddressImpacted['src']={}
			objectAddressImpacted['dst']={}
			
		if mode=='normal' or mode=='addAll' or mode=='getObjImpacted':
			for id_rule in self.rules[vdom]:
			
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['srcaddr']
				dstAddrList=self.rules[vdom][id_rule]['dstaddr']
				
				if mode=='addAll':
					if srcAddrList[0]=='all'  or dstAddrList[0]=='all':
						resultat[id_rule]=self.rules[vdom][id_rule]
						continue
						
				testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
				testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
				
				if mode=='getObjImpacted':
					try:
						if self.rules[vdom][id_rule]['action']!='accept':
							pdb.set_trace()
					except KeyError as E:
						print(f'rule:{id_rule}')
						continue
					if testSrc:
						curObjDstList=self.rules[vdom][id_rule]['dstaddr']
						objectAddressImpacted['dst'][id_rule]={ addrCur:self.address[vdom][addrCur] for addrCur in self.explodeListGrp(curObjDstList,vdom) } 
					if testDst:
						curObjSrcList=self.rules[vdom][id_rule]['srcaddr']
						objectAddressImpacted['src'][id_rule]={ addrCur:self.address[vdom][addrCur] for addrCur in self.explodeListGrp(curObjSrcList,vdom) } 
				
				if testSrc or testDst:
					resultat[id_rule]=self.rules[vdom][id_rule]
					

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)
					
			return resultat		
			
		if mode=='SrcDst':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['srcaddr']
				dstAddrList=self.rules[vdom][id_rule]['dstaddr']
				
						
				testSrc=self.matchListGrpOrAddr(netStr[0],srcAddrList,vdom,mode='normal')
				testDst=self.matchListGrpOrAddr(netStr[1],dstAddrList,vdom,mode='normal')
				
				if testSrc and testDst:
					resultat[id_rule]=self.rules[vdom][id_rule]
					

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)			
					
			return resultat
		
		if mode=='Src':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['srcaddr']
				
						
				testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
				
				if testSrc:
					resultat[id_rule]=self.rules[vdom][id_rule]
					

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)			
					
			return resultat

		if mode=='Dst':
			for id_rule in self.rules[vdom]:
			
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
						
				dstAddrList=self.rules[vdom][id_rule]['dstaddr']
						
				testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
				
				if testDst:
					resultat[id_rule]=self.rules[vdom][id_rule]
					

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)			
					
			return resultat
		if mode=='FileSrcDst':
			AllSrcDst=list(product(netStr[0],netStr[1]))
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['srcaddr']
				dstAddrList=self.rules[vdom][id_rule]['dstaddr']
				for netStrSrc,netStrDst  in AllSrcDst:		
					testSrc=self.matchListGrpOrAddr(netStrSrc,srcAddrList,vdom,mode='normal')
					testDst=self.matchListGrpOrAddr(netStrDst,dstAddrList,vdom,mode='normal')
					
					if testSrc and testDst:
						if id_rule not in resultat:
							resultat[id_rule]=self.rules[vdom][id_rule]
							resultat[id_rule]['matching']=[{'src':netStrSrc,'dst':netStrDst}]
						else:
							resultat[id_rule]['matching'].append({'src':netStrSrc,'dst':netStrDst})

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)	
					
			return resultat	
					
		if mode=='FileSrc':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['srcaddr']
				
				for netStr__  in netStr:		
					testSrc=self.matchListGrpOrAddr(netStr__,srcAddrList,vdom,mode='normal')
					
					if testSrc:
						if id_rule not in resultat:
							resultat[id_rule]=self.rules[vdom][id_rule]
							resultat[id_rule]['matching']=[{'src':netStr__}]
						else:
							resultat[id_rule]['matching'].append({'src':netStr__})
			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)			
					
			return resultat	
			
		if mode=='FileDst':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf'][0]
					ifDst=self.rules[vdom][id_rule]['dstintf'][0]
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				dstAddrList=self.rules[vdom][id_rule]['dstaddr']
				
				for netStr__  in netStr:		
					testDst=self.matchListGrpOrAddr(netStr__,dstAddrList,vdom,mode='normal')
					
					if testDst:
						if id_rule not in resultat:
							resultat[id_rule]=self.rules[vdom][id_rule]
							resultat[id_rule]['matching']=[{'dst':netStr__}]
						else:
							resultat[id_rule]['matching'].append({'dst':netStr__})				
				

			if savefile:
				FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
				if mode=='getObjImpacted':
					objectImpactedSaveFile='obj_impacted_'+savefile
					saveResult(objectAddressImpacted,objectImpactedSaveFile)			
					
			return resultat			
		elif mode=='list':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf']
					ifDst=self.rules[vdom][id_rule]['dstintf']
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['dstaddr']
				dstAddrList=self.rules[vdom][id_rule]['srcaddr']
				test=self.matchListGrpOrAddr(netStr,srcAddrList+dstAddrList,vdom,mode='list')
				if test:
					resultat[id_rule]=self.rules[vdom][id_rule]
					
				if savefile:
					FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
					
			return resultat
		elif mode=='fullPolicy':
			AddrNeeded=[]
			GrpNeeded=[]
			RuleNeeded=[]
			
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf']
					ifDst=self.rules[vdom][id_rule]['dstintf']
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				srcAddrList=self.rules[vdom][id_rule]['dstaddr']
				dstAddrList=self.rules[vdom][id_rule]['srcaddr']


				testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
				testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
				
				
				if testSrc and testDst:
					RuleNeeded.append(id_rule)
					AddrSrcCur=self.explodeListGrp(srcAddrList,vdom)
					AddrDstCur=self.explodeListGrp(dstAddrList,vdom)
					for addrOrGrp in AddrSrcCur+AddrDstCur:
						typeCur=self.getTypeObj(addrOrGrp)
						if typeCur=='address':
							if not self.testNetinAddr(netStr,self.addressObj[vdom][addrOrGrp],mode='normal'):
								if addrOrGrp not in AddrNeeded:
									AddrNeeded.append(addrOrGrp)
						elif typeCur=='group':
							GroupOrAddrCur=self.getAllObjFromGrp(addrOrGrp,vdom,mode=mode)
							if GroupOrAddrCur not in GroupOrAddrCur:
								GrpNeeded.append(GroupOrAddrCur)
							for address__ in GroupOrAddrCur['address']:
								if not self.testNetinAddr(netStr,self.addressObj[vdom][address__],mode='normal'):
									if address__ not in AddrNeeded:
										AddrNeeded.append(address__)
							for group__ in 	 GroupOrAddrCur['address']:
								if group__ not in GrpNeeded:
									GrpNeeded.append(group__)
						else:
							print('warning type object is unknown for:',addrOrGrp)
							
			'''Generate address needed'''
			addressFiltered={vdom:{addrName:self.address[vdom][addrName] for addrName in AddrNeeded }}
			grpFiltered={vdom:{grpName:self.grpAddr[vdom][grpName] for grpName in GrpNeeded }}
			rulesFiltered={vdom:{ruleid:self.rules[vdom][ruleid] for ruleid in RuleNeeded }}
			
			dataFwFiltered={'address':addressFiltered , 'groups':grpFiltered, 'rules':rulesFiltered }
			return FortinetFw(dataDict=dataFwFiltered)
			
	
	def filterListRulesList(self,netStrList,vdom,mode='normal',savefile="",getMode="",ifs=[]):
		resultat={}
		if mode=='normal' or mode=='addAll':
			for id_rule in self.rules[vdom]:
				if ifs:
					ifSrc=self.rules[vdom][id_rule]['srcintf']
					ifDst=self.rules[vdom][id_rule]['dstintf']
					if ifSrc not in ifs and ifDst not in ifDst:
						continue
				for netStr in netStrList:
					srcAddrList=self.rules[vdom][id_rule]['dstaddr']
					dstAddrList=self.rules[vdom][id_rule]['srcaddr']
					testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
					testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
					if mode=='addAll':
						if srcAddrList[0]=='all':
							testSrc=True
						if dstAddrList[0]=='all':
							testDst=True
					if testSrc or testDst:
						if id_rule not in resultat:
							resultat[id_rule]=self.rules[vdom][id_rule]
						break
						
		if savefile:
			FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }}).save(savefile)
			
		if getMode=='obj':
			return FortinetFw(dataDict={'address':self.address , 'groups': self.grpAddr, 'rules': { vdom: resultat }})

		return resultat
		
	def filterTheseRules(self,netStrOrList,rulesDict,vdom,mode='normal'):
		resultat={}

		if mode=='normal':
			if isinstance(netStrOrList,str):
				netStr=netStrOrList
				for id_rule in rulesDict:
					srcAddrList=rulesDict[id_rule]['dstaddr']
					dstAddrList=rulesDict[id_rule]['srcaddr']
					testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
					testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
					if testSrc or testDst:
						resultat[id_rule]=rulesDict[id_rule]
			elif isinstance(netStrOrList,list):
				netStrList=netStrOrList
				for id_rule in rulesDict:
					for netStr in netStrList:
						srcAddrList=rulesDict[id_rule]['dstaddr']
						dstAddrList=rulesDict[id_rule]['srcaddr']
						testSrc=self.matchListGrpOrAddr(netStr,srcAddrList,vdom,mode='normal')
						testDst=self.matchListGrpOrAddr(netStr,dstAddrList,vdom,mode='normal')
						if testSrc or testDst:
							if id_rule not in resultat:
								resultat[id_rule]=rulesDict[id_rule]
							break
			
		return resultat
	
	
	def explodeRule(self,vdom,mode='normal',netStr='',netStrList=[]):

			
		new_id=1
		explodedRule={}
		try:
			for id_rule in sorted(self.rules[vdom].keys(),key=lambda x : int(x)):
				tmp_rule=self.rules[vdom][id_rule].copy()
				srcAddrList=self.rules[vdom][id_rule]['dstaddr']
				dstAddrList=self.rules[vdom][id_rule]['srcaddr']
				srcAddrListWoGrp=self.explodeListGrp(srcAddrList,vdom)
				dstAddrListWoGrp=self.explodeListGrp(srcAddrList,vdom)
				del tmp_rule['dstaddr']
				del tmp_rule['srcaddr']
				for srcAddr in srcAddrListWoGrp:
					for dstAddr in dstAddrListWoGrp:
						id_cur=str(new_id)
						cur_rule=tmp_rule.copy()
						explodedRule[id_cur]=cur_rule
						explodedRule[id_cur]['dstaddr']=[dstAddr]
						explodedRule[id_cur]['srcaddr']=[srcAddr]
						new_id+=1
						#if new_id>100000:
						#	pdb.set_trace()
						#	break;
		except MemoryError as E:
			print(E)
			print(new_id)
		if netStr:
			return self.filterTheseRules(netStr,explodedRule,vdom,mode=mode)
		if netStrList:
			return self.filterTheseRules(netStrList,explodedRule,vdom,mode=mode)
			
		print(str(new_id))
					
		return explodedRule
					
	def getAllObjFromGrp(self,grpName,vdom,mode='normal'):
		try:
			self.grpAddr[vdom]
		except KeyError as e:
			print(e)
			print("Vdom unknown, not configured, or Vdom do not contains group address")
			return []
			
		AllObj={'address':[],'group':[]}
		if mode=='normal':
			for member in self.grpAddr[vdom][grpName]['member']:
				typeCur=self.getTypeObj(member,vdom)
				if typeCur=='address':
					if member not in AllObj['address']:
						AllObj['address'].append(member)
				elif typeCur=='group':
					if member not in AllObj['group']:
						AllObj['group'].append(member)
					list_tmp=self.grpAddr[vdom][grpName]['member']
					while list_tmp:
						for GrpOrAddr in list_tmp:
							if GrpOrAddr in self.grpAddr[vdom]:
								if GrpOrAddr not in AllObj['group']:
									AllObj['group'].append(GrpOrAddr)
								list_tmp.remove(GrpOrAddr)
								list_tmp+=self.grpAddr[vdom][GrpOrAddr]['member']
							else:
								if GrpOrAddr not in AllObj['address']:
									AllObj['address'].append(GrpOrAddr)
								list_tmp.remove(GrpOrAddr)
					
		return AllObj			
	
if __name__ == '__main__':
	"main function"
	
	parser = argparse.ArgumentParser()
	groupInit=parser.add_mutually_exclusive_group(required=True)
	groupNet=parser.add_mutually_exclusive_group(required=False)
	groupRule=parser.add_mutually_exclusive_group(required=False)
	groupInit.add_argument("-f", "--file",action="store",help=u"Fortigate File config to analyze")
	groupInit.add_argument("-d", "--dump",action="store",help=u"Fortigate Dump to analyze")
	parser.add_argument("--list-vdom", dest='list_vdom',action="store_true",help=u"display vdom list",required=False)
	parser.add_argument("--list-addr", dest='list_addr',action="store_true",help=u"display address list for a vdom",required=False)
	parser.add_argument("--list-grp", dest='list_grp',action="store_true",help=u"display group address list for a vdom",required=False)
	parser.add_argument("--list-static-routes", dest='list_static_routes',action="store_true",help=u"display route for a vdom",required=False)
	parser.add_argument("--list-interfaces", dest='list_interfaces',action="store_true",help=u"display intefaces",required=False)
	groupRule.add_argument("--list-rules", dest='list_rules',action="store_true",help=u"display rule list for a vdom",required=False)
	groupRule.add_argument("--explode-rule", dest='explode_rules',action="store_true",help=u"display exploded rules list for a vdom ",required=False)
	groupRule.add_argument("--filter-policy", dest='filter_policy',action="store_true",help=u"filter all policy",required=False)
	parser.add_argument("--vdom",action="store",help=u"vdom to analyze",required=False)
	parser.add_argument("--group",action="store",help=u"group to analyze or display",required=False)
	parser.add_argument("--address",action="store",help=u"address object to analyze or display",required=False)
	parser.add_argument("--src",action="store",help=u"Filter on source",required=False)
	parser.add_argument("--dst",action="store",help=u"Filter on destination",required=False)
	parser.add_argument("--file-src",dest='file_src',action="store",help=u"Filter on multiple source contains in a text file",required=False)
	parser.add_argument("--file-dst",dest='file_dst',action="store",help=u"Filter on multiple destination contains in a text file",required=False)
	parser.add_argument("--interface",action="append",default=[],help=u"filter interface only with list-rules",required=False)
	parser.add_argument("--mode",action="store",help=u"mode of filtering:normal|fullPolicy|addAll|getObjImpacted",default='normal',required=False)
	parser.add_argument("--cache",action="store_true",default=False,help=u"use cache if it existed",required=False)
	parser.add_argument("--explode",action="store_true",default=False,help=u"use explode group only, return all object contains inside",required=False)
	parser.add_argument("--save",action="store",default="",help=u"Save result in yaml",required=False)
	groupNet.add_argument("-n","--network",action="append",help=u"network filter",required=False)
	groupNet.add_argument("--file-network",dest='filenetwork',action="store",help=u"list network filter in a text file",required=False)
	groupNet.add_argument("--mfile-network",dest='mfilenetwork',action="append",help=u"2 list network filter in a text file apply successively",required=False)
	args = parser.parse_args()
	
	if  args.list_addr and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --list-addr ')
		
	if  args.list_grp and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --list-grp ')
		
	if  args.list_rules and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --list-rules ')
		
	if  args.list_static_routes and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --list-static-routes ')
		
	if  args.explode_rules and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --list-rules ')
		
	if  args.network and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --network ')
		
	if  args.filenetwork and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --file-network ')
		
	if  args.group and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --group ')
		
	if  args.address and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory with --address ')
		
	if  args.filter_policy and not args.vdom:
		raise argparse.ArgumentError(None,'--vdom  is manadatory --file-network with --filter-policy ')
		
	if  args.filter_policy and not (args.network or args.filenetwork):
		raise argparse.ArgumentError(None,'--network or   is manadatory with --filter-policy ')	
		
	if  args.explode and not args.group:
		raise argparse.ArgumentError(None,'--group or   is manadatory with --explode ')
		
	if args.network and (args.src or args.dst or args.file_src or args.file_dst):
		raise argparse.ArgumentError(None,'--network not compatible with --src or --dst or --file-src or --file-dst ')
		
	if (args.src or args.dst) and (args.file_src or args.file_dst):
		raise argparse.ArgumentError(None,'--src/--dst not compatible with ---file-src/--file-dst')
		
	if (args.src or args.dst or args.file_src or args.file_dst) and not args.list_rules:
		raise argparse.ArgumentError(None,'--list-rules  is manadatory with ---file-src/--file-dst/--src/--dst')
		
	if args.network:
		if len(args.network)==1:
			args.network=args.network[0]
		else:
			if not (args.list_rules or args.list_static_routes):
				raise argparse.ArgumentError(None,'--list-rules or --list-static-routes is manadatory with multiple --network ')
				
	if args.save and not args.list_rules:
		raise argparse.ArgumentError(None,'--list-rules is manadatory with --save ')
		
	if args.interface and not args.list_rules:
		raise argparse.ArgumentError(None,'--list-rules is manadatory with --interface ')
		
	FwObj= FortinetFw(args.file,caching=args.cache)
	
	if args.mfilenetwork:
		if args.mfilenetwork and not args.list_rules:
			raise argparse.ArgumentError(None,'--list-rules is manadatory with --mfile-network ')
			
		if len(args.mfilenetwork)!=2:
			raise argparse.ArgumentError(None,'--mfile-network must be used twice only')
			
		listNetwork1=getListNetFromFile(args.mfilenetwork[0])
		listNetwork2=getListNetFromFile(args.mfilenetwork[1])
	
	if args.list_vdom:
		ppr(list(FwObj.address.keys()))
		
	if args.vdom:
		list_vdom=list(FwObj.address.keys())
		if args.vdom not in list_vdom:
			raise FortinetFwError(value1=args.vdom)
			
	if args.filenetwork:
		listNetwork=getListNetFromFile(args.filenetwork)
		
	if args.file_src:
		listNetworkSrc=getListNetFromFile(args.file_src)
		
	if args.file_dst:
		listNetworkDst=getListNetFromFile(args.file_dst)
		
	if args.list_addr:
		if args.vdom not in FwObj.address:
			print(args.vdom,"do not contain address")
			sys.exit(0)
		if args.network:
			ppr(FwObj.filterListAddr(args.network,args.vdom,mode=args.mode))
		elif args.filenetwork:
			ppr(FwObj.filterListAddrList(listNetwork,args.vdom,mode=args.mode))
		else:
			ppr(list(FwObj.address[args.vdom].keys()),width=100)

	if args.list_addr:
		if args.vdom not in FwObj.address:
			print(args.vdom,"do not contain address")
			sys.exit(0)
		if args.network:
			ppr(FwObj.filterListAddr(args.network,args.vdom,mode=args.mode))
		elif args.filenetwork:
			ppr(FwObj.filterListAddrList(listNetwork,args.vdom,mode=args.mode))
		else:
			ppr(list(FwObj.address[args.vdom].keys()),width=100)	

		
	if args.list_grp:
		if args.network:
			ppr(FwObj.filterListGrpAddr(args.network,args.vdom,mode=args.mode))
		elif args.filenetwork:
			ppr(FwObj.filterListGrpAddrList(listNetwork,args.vdom,mode=args.mode))
		else:
			ppr(list(FwObj.grpAddr[args.vdom].keys()),width=100)
	
	if args.list_static_routes:
		if args.network:
			if isinstance(args.network,str):
				ppr(FwObj.filterStaticRoute(args.network,args.vdom,mode=args.mode),width=200)
			elif isinstance(args.network,list):
				ppr(FwObj.filterStaticRouteList(args.network,args.vdom,mode=args.mode),width=200)
		elif args.filenetwork:
			ppr(FwObj.filterfilterStaticRouteList(listNetwork,args.vdom,mode=args.mode),width=200)
		else:
			ppr(FwObj.staticRoutes[args.vdom],width=200)	

	if args.list_interfaces:
		ppr(FwObj.interfaces,width=200)	
			
	if args.list_rules:
		if args.vdom not in FwObj.rules:
			print(args.vdom,"do not contain rules")
			sys.exit(0)
			
		if args.network:
			if args.mode=='addAll':
				ppr(FwObj.filterListRules(args.network,args.vdom,mode='addAll',savefile=args.save,ifs=args.interface),width=1000)
			elif args.mode=='getObjImpacted':
				ObjImpacted={}
				ppr(FwObj.filterListRules(args.network,args.vdom,mode='getObjImpacted',savefile=args.save,objectAddressImpacted=ObjImpacted,ifs=args.interface),width=1000)
				ppr(ObjImpacted,width=200)
			elif isinstance(args.network,str):
				ppr(FwObj.filterListRules(args.network,args.vdom,mode='normal',savefile=args.save,ifs=args.interface),width=1000)
			elif isinstance(args.network,list):
				ppr(FwObj.filterListRules(args.network,args.vdom,mode='list',savefile=args.save,ifs=args.interface),width=1000)
		elif args.filenetwork:
			ppr(FwObj.filterListRulesList(listNetwork,args.vdom,mode=args.mode,savefile=args.save,ifs=args.interface),width=5000)
		elif args.mfilenetwork:
			FwObjTmp=FwObj.filterListRulesList(listNetwork1,args.vdom,mode=args.mode,getMode='obj',ifs=args.interface)
			ppr(FwObjTmp.filterListRulesList(listNetwork2,args.vdom,mode=args.mode,savefile=args.save,ifs=args.interface),width=5000)
		elif args.src and args.dst:
			ppr(FwObj.filterListRules([args.src,args.dst],args.vdom,mode='SrcDst',savefile=args.save,ifs=args.interface),width=1000)
		elif args.src:
			ppr(FwObj.filterListRules(args.src,args.vdom,mode='Src',savefile=args.save,ifs=args.interface),width=1000)
		elif args.dst:
			ppr(FwObj.filterListRules(args.dst,args.vdom,mode='Dst',savefile=args.save,ifs=args.interface),width=1000)
		elif args.file_src and args.file_dst:
			ppr(FwObj.filterListRules([listNetworkSrc,listNetworkDst],args.vdom,mode='FileSrcDst',savefile=args.save,ifs=args.interface),width=1000)
		elif args.file_src:
			ppr(FwObj.filterListRules(listNetworkSrc,args.vdom,mode='FileSrc',savefile=args.save,ifs=args.interface),width=1000)
		elif args.file_dst:
			ppr(FwObj.filterListRules(listNetworkDst,args.vdom,mode='FileDst',savefile=args.save,ifs=args.interface),width=1000)
		else:
			ppr(FwObj.rules[args.vdom],width=1000)
		
			
	if args.explode_rules:
		if args.vdom not in FwObj.rules:
			print(args.vdom,"do not contain rules")
			sys.exit(0)
			
		if args.network:
			ppr(FwObj.explodeRule(args.vdom,mode='normal',netStr=args.network),width=1000)
		elif args.filenetwork:
			ppr(FwObj.explodeRule(args.vdom,mode='normal',netStrList=listNetwork),width=1000)
		else:
			ExplodedRules=FwObj.explodeRule(args.vdom,mode='normal')
			try:
				ppr(ExplodedRules,width=1000)
			except MemoryError as E:
				for ruleId in ExplodedRules:
					print('=>',ruleId,":",ExplodedRules[ruleId])
			cacheExplodedRule=cc.Cache(FwObj.tag+'EXPLODED_RULES')
			cacheExplodedRule.save(ExplodedRules)
			
	if args.filter_policy:
		if args.network:
			FilteredPol=FwObj.filterListRules(args.network,args.vdom,mode='fullPolicy')
			ppr(FilteredPol,width=1000)
		elif args.filenetwork:
			FilteredPol=FwObj.filterListRulesList(listNetwork,args.vdom)
			ppr(FilteredPol,width=1000)
			
			
	if args.group:
		if args.vdom not in FwObj.grpAddr:
			print(args.vdom,"do not contain group")
			sys.exit(0)
		else:
			if args.group not in FwObj.grpAddr[args.vdom]:
				print(args.vdom,"do not contain group ",args.group)
				sys.exit(0)
		if args.network:
			filteredResult=FwObj.filterGrpAddr(args.network,args.vdom,args.group,args.mode)
			ppr(filteredResult,width=300)
		elif args.filenetwork:
			filteredResult=FwObj.filterGrpAddrList(listNetwork,args.vdom,args.group,args.mode)
			ppr(filteredResult,width=300)
		elif args.explode:
			explodedResult=FwObj.getAllObjFromGrp(args.group,args.vdom,mode=args.mode)
			ppr(explodedResult,width=5)
		else:
			ppr(FwObj.grpAddr[args.vdom][args.group],width=100)
		
	if args.address:
		if args.vdom not in FwObj.address:
			print(args.vdom,"do not contain address")
			sys.exit(0)
		else:
			if args.address not in FwObj.address[args.vdom]:
				print(args.vdom,"do not contain address object ",args.address)
				pdb.set_trace()
				sys.exit(0)
				
		if args.network:
			filteredResult=FwObj.filterAddr(args.network,args.vdom,args.address,args.mode)
			ppr(filteredResult,width=300)
		elif args.filenetwork:
			filteredResult=FwObj.filterAddrList(listNetwork,args.vdom,args.address,args.mode)
			ppr(filteredResult,width=300)
		else:
			ppr(FwObj.address[args.vdom][args.address],width=100)
