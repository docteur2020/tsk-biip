#!/usr/bin/env python3.8
# coding: utf-8

import argparse
import pdb
import yaml
import checkroute
from pprint import pprint as ppr
from pprint import pformat as pprs
from numpy import unique
import pyparsing as pp
import os
import io

from ipEnv import interface, ifEntries
from xlsxDictWriter import xlsMatrix



DIR_RESULT='/home/d83071/EXCEL/STATICROUTE/'
DIR_CONFIG='/home/d83071/CONFIG/STATICROUTE/'

def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)

def loadYaml(file):
	with open(file, 'r') as yml__:
		yaml_obj = yaml.load(yml__,Loader=yaml.SafeLoader)

	return yaml_obj
	
def inser_inc(dict_id):
	def parseAction(s,l,t):
		dict_id['0']=str(int(dict_id['0'])+1)
		return dict_id['0']
	return parseAction
	
def extractStaticRouteFromConf(runningFile):

	id__={'0':'0'}
	

			
	Vrf=pp.Suppress(pp.Literal('vrf')+pp.Literal('context'))+pp.Word(pp.alphanums+"-_*,")
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ]) | pp.Literal('Loopback') | pp.Literal('Vlan') | pp.Literal('Tunnel') |pp.Literal('Null') |pp.Literal('mgmt')) + pp.Word(pp.nums+('\/.')) )
	Nexthop=ipAddress
	prefixLen=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Literal('/')+prefixLen)
	routeWoAttribute=Prefix.setResultsName('prefix')+pp.Optional(Interface).setResultsName('interface')+Nexthop.setResultsName('nh')+pp.LineEnd()
	RouteEntryWithNH=Prefix.setResultsName('prefix')+pp.Optional(Interface).setResultsName('interface')+Nexthop.setResultsName('nh')+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n'))).setResultsName('otherAttributes')
	RouteEntryWoNh=Prefix.setResultsName('prefix')+pp.Optional(Interface).setResultsName('interface')+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n'))).setResultsName('otherAttributes')
	RouteEntry=pp.MatchFirst([routeWoAttribute,RouteEntryWithNH,RouteEntryWoNh])
	RouteEntries=pp.dictOf(pp.Literal('ip route').setParseAction(inser_inc(id__)) ,RouteEntry)
	AllStaticRoute=pp.Suppress(pp.SkipTo(Vrf))+pp.dictOf(Vrf,pp.MatchFirst([pp.Suppress(pp.SkipTo(pp.Literal('ip route')))+RouteEntries,pp.SkipTo(pp.Literal('vrf context')).setParseAction(pp.replaceWith(None))]) )
	
	VrfBlocStatic=pp.dictOf(Vrf,pp.Optional(pp.SkipTo(pp.Literal('ip route'),failOn="vrf context"))+RouteEntries)
	
	with open(runningFile) as file:
		str__=file.read()
		
	result=VrfBlocStatic.scanString(str__)
	resultList=list(result)
	
	staticVrf={}
	for entry in resultList:
		entry_cur=entry[0].asDict()
		for vrf in entry_cur:
			staticVrf[vrf]=[ route for route in entry_cur[vrf].values() ]
	
	
	return staticVrf
	
class MultipleRTContainer(object):
	def __init__(self,yaml_file,ifs_dump_file=""):
		self.routes={}
		self.routesStaticObj={}
		self.routesStatic={}
		self.prefixes={}
		self.routesByVrf={}
		self.uniqRoute={}
		self.routesStaticCfg={}
		
		dataRT=loadYaml(yaml_file)
		
		if ifs_dump_file:
			self.ifsDb=ifEntries(dump=ifs_dump_file)
		else:
			self.ifsDb=None
			
		for host__ in dataRT:
			self.routes[host__]=checkroute.table_routage_allVRF(dump=dataRT[host__]['dump'])
			self.routesStaticObj[host__]=self.routes[host__].extract_protocol('S')
			
			if self.ifsDb:
				self.routesStaticCfg[host__]=extractStaticRouteFromConf(dataRT[host__]['running'])
			

		self.hostnames=list(self.routes.keys())
		self.hostnames.sort()
		
		if self.ifsDb: 
			self.initStaticDict()
			self.initRouteByVrf()
			self.initRouteStaticCfgByPrefix()
			self.initRouteUniqByVrf()
			self.getPatchConfigSpof()
			self.reportDict={'Spofs':[['vrf','prefix','configuration','ifsConnectedNH']]}
			
			
			self.initReport()
		#self.connected=

	def __str__(self):
		return pprs(self.routes,width=500)
		
	def __repr__(self):
		return pprs(self.routes,width=500)
		
	def initStaticDict(self):
		for host__ in self.routesStaticObj:
			self.routesStatic[host__]={}
			for vrf in self.routesStaticObj[host__].dict_RT_AllVRF:
				self.routesStatic[host__][vrf]={}
				for entry in self.routesStaticObj[host__].dict_RT_AllVRF[vrf].tab_prefix:
					self.routesStatic[host__][vrf][str(entry.reseau)]=entry
		
		listNetTmp={}
		for host__ in self.routesStatic:
			for vrf in self.routesStatic[host__]:
				if vrf not in listNetTmp:
					listNetTmp[vrf]=list(self.routesStatic[host__][vrf].keys())
				else:
					listNetTmp[vrf]+=list(self.routesStatic[host__][vrf].keys())
		
		for vrf in listNetTmp:
			self.prefixes[vrf]=list(unique(listNetTmp[vrf]))
			
	def initRouteByVrf(self):
		for vrf in self.prefixes:
			self.routesByVrf[vrf]={}
			for prefix__ in self.prefixes[vrf]:
				result_brief_cur=0
				result_cur={}
				for host__ in self.hostnames:
					if prefix__ in self.routesStatic[host__][vrf]:
						result_cur[host__]=self.routesStatic[host__][vrf][prefix__]
						result_brief_cur+=1
				self.routesByVrf[vrf][prefix__]={'rt':result_cur,'total':result_brief_cur}
				
				
	def initRouteUniqByVrf(self):
		for vrf in self.routesByVrf:
			for prefix__ in self.routesByVrf[vrf]:
				result_brief_cur=self.routesByVrf[vrf][prefix__]['total']
				if result_brief_cur==1:
					configurationCur=self.getRouteStaticConfigured(vrf,prefix__)
					ifCurNH={}
					for hostname in configurationCur:
						for route in configurationCur[hostname]:
							if 'ifsConnected_NH' in route:
								nh_cur=route['nh']
								if nh_cur not in ifCurNH:
									ifCurNH[nh_cur]=route['ifsConnected_NH']
					if vrf not in self.uniqRoute:
						self.uniqRoute[vrf]=[{ 'prefix': prefix__ ,'configuration':configurationCur,'ConnectedNH':ifCurNH} ]
					else:
						self.uniqRoute[vrf].append({ 'prefix': prefix__ ,'configuration':configurationCur,'ConnectedNH':ifCurNH})
				#elif result_brief_cur==2:
				#	print('2 routes only')
				#	print(self.routesByVrf[vrf][prefix__])
	def initRouteStaticCfgByPrefix(self):
		self.routeStaticCfgByPrefix={}
		tempIfs={}
		for host__ in self.routesStaticCfg:
			self.routeStaticCfgByPrefix[host__]={}
			for vrf in self.routesStaticCfg[host__]:
				self.routeStaticCfgByPrefix[host__][vrf]={}
				for entry in self.routesStaticCfg[host__][vrf]:
					prefix_cur=entry['prefix']
					if 'nh' in entry:
						if entry['nh'] in tempIfs:	
							entry['ifsConnected_NH']=tempIfs[entry['nh']]
						else:
							if self.ifsDb:
								entry['ifsConnected_NH']=self.ifsDb.getConnected(entry['nh'])
								tempIfs[entry['nh']]=entry['ifsConnected_NH']
							else:
								entry['ifsConnected_NH']="TBD"
								tempIfs[entry['nh']]=entry['ifsConnected_NH']
								
					if prefix_cur in self.routeStaticCfgByPrefix[host__][vrf]:
						self.routeStaticCfgByPrefix[host__][vrf][prefix_cur].append(entry)
					else:
						self.routeStaticCfgByPrefix[host__][vrf][prefix_cur]=[entry]
						
	def getRouteStaticConfiguredByHost(self,hostname,vrf,prefix):
		try: 
			return self.routeStaticCfgByPrefix[hostname][vrf][prefix]
		except KeyError:
			return []
			
	def getRouteStaticConfigured(self,vrf,prefix):
		result={}
		
		for hostname in self.hostnames :
			result_cur=self.getRouteStaticConfiguredByHost(hostname,vrf,prefix)
			if result_cur:
				result[hostname]= result_cur
				
		return result
		
	def initReport(self):
		"['vrf','prefix','configuration','Ifs NextHop']"
		for vrf in self.uniqRoute:
			for entry in self.uniqRoute[vrf]:
				self.reportDict['Spofs'].append([vrf,entry['prefix'],str(entry['configuration']),str(entry['ConnectedNH'])])

		
	def getPatchConfigSpof(self):
	
		def extractInfoRoute(dictRoute,vrf__):
			result=[]
			for route in dictRoute:
				route_copy=route.copy()
				route_copy['vrf']=vrf__
				if 'ifsConnected_NH' in route_copy:
					del route_copy['ifsConnected_NH']
				result.append(route_copy)
				
			return result
	
		self.configPatch={'add':{} , 'del':{}}

		pdb.set_trace()
		
		for vrf in self.uniqRoute:
			self.configPatch['add'][vrf]={}
			self.configPatch['del'][vrf]={}
			for entry in self.uniqRoute[vrf]:
				ifsCurNH=entry['ConnectedNH']
				CurListNH=list(ifsCurNH.keys())
				configCur=entry['configuration']
				hostnameCurConfig=list(configCur.keys())
				AlreadyConfigured=[]
				ToBeSuppressed=[]
				self.configPatch['add'][vrf][entry['prefix']]=[]
				self.configPatch['del'][vrf][entry['prefix']]=[]
				
				#if entry['prefix']=='22.254.201.128/26':
				#	pdb.set_trace()
				#	"stop"
					
				if len(CurListNH)>1:
					pdb.set_trace()
					print('multiple NH please verify the good one')
					nh_cur=[]
				else:
					nh_cur=ifsCurNH[CurListNH[0]]
					nh_cur_hosts=[i[0] for i in nh_cur]
					if len(hostnameCurConfig)>1:
						print('Verifying inactive route...:')
						for hostConfig in configCur:
							if hostConfig not in nh_cur_hosts:
								print(f'On {hostConfig:}')
								print(f'inactive route to be suppressed:')
								CurDelConfig=extractInfoRoute(configCur[hostConfig],vrf)
								ppr(CurDelConfig)
								ToBeSuppressed.append(hostConfig)
								self.configPatch['del'][vrf][entry['prefix']].append({hostConfig:CurDelConfig})
							else:
								AlreadyConfigured.append(hostConfig)
					else:
						AlreadyConfigured=hostnameCurConfig
						
				if ToBeSuppressed:
					AlreadyConfigured=hostnameCurConfig
					
				for hostname in nh_cur:
					if hostname[0] not in AlreadyConfigured:
						print(f'Route to be added on {hostname[0]}:')
						try:
							CurAddConfig=extractInfoRoute(configCur[AlreadyConfigured[0]],vrf)
							ppr(CurAddConfig)
							self.configPatch['add'][vrf][entry['prefix']].append({hostname[0]:CurAddConfig})
							
						except IndexError:
							pdb.set_trace()
							"stop"
							
		"Check route not patched"
		print("Verify configuration not patched...")
		for vrf in self.configPatch['add']:
			for prefix__ in self.configPatch['add'][vrf]:

				if not self.configPatch['add'][vrf][ prefix__]:
					print("Verify configuration for:")
					print(f'{vrf}/{prefix__}')	
					
	def genConfig(self,directory):
	
		ioConfigsRO={}
		ioConfigsRB={}
		
		dir_ro=directory+'RO/'
		dir_rb=directory+'RB/'
		if not os.path.exists(dir_ro):
			os.makedirs(dir_ro)	
		if not os.path.exists(dir_rb):
			os.makedirs(dir_rb)
			
		configByHostAdd={}
		configByHostDel={}
		
		for vrf in self.configPatch['add']:
			for prefix__ in self.configPatch['add'][vrf]:
				for entry in  self.configPatch['add'][vrf][prefix__]:
					for hostname in entry:
						configCur__=entry[hostname]
						if hostname not in configByHostAdd:
							configByHostAdd[hostname]={vrf:[	configCur__]}
						else:
							if vrf not in configByHostAdd[hostname]:
								configByHostAdd[hostname][vrf]=[configCur__]
							else:
								configByHostAdd[hostname][vrf].append(configCur__)
							
		for vrf in self.configPatch['del']:
			for prefix__ in self.configPatch['del'][vrf]:
				for entry in  self.configPatch['del'][vrf][prefix__]:
					for hostname in entry:
						configCur__=entry[hostname]
					
						if hostname not in configByHostDel:
							configByHostDel[hostname]={vrf:[	configCur__]}
						else:
							if vrf not in configByHostDel[hostname]:
								configByHostDel[hostname][vrf]=[configCur__]
							else:
								configByHostDel[hostname][vrf].append(configCur__)
						
		"Rollout"
		

		for hostnameCur in configByHostAdd:
			if hostnameCur not in ioConfigsRO:
				ioConfigsRO[hostnameCur]=io.StringIO()
			ioConfigsRO[hostnameCur].write('! Correcting Spof, routes adding\n')
			for vrf in configByHostAdd[hostnameCur]:
				ioConfigsRO[hostnameCur].write('vrf context '+vrf+'\n')
				for entryCfg in configByHostAdd[hostnameCur][vrf]:
					ioConfigsRO[hostnameCur].write(" ip route "+self.getRouteEntryCfg(entryCfg[0])+'\n')
					
		for hostnameCur in configByHostDel:
			if hostnameCur not in ioConfigsRO:
				ioConfigsRO[hostnameCur]=io.StringIO()
			ioConfigsRO[hostnameCur].write('! Correcting useless routes, routes deleting\n')
			for vrf in configByHostDel[hostnameCur]:
				ioConfigsRO[hostnameCur].write('vrf context '+vrf+'\n')
				for entryCfg in configByHostDel[hostnameCur][vrf]:
					ioConfigsRO[hostnameCur].write(" no ip route "+self.getRouteEntryCfg(entryCfg[0])+'\n')				
		
		"Rollback"

		for hostnameCur in configByHostAdd:
			if hostnameCur not in ioConfigsRB:
				ioConfigsRB[hostnameCur]=io.StringIO()
			ioConfigsRB[hostnameCur].write('![RB] Correcting Spof, routes adding\n')
			for vrf in configByHostAdd[hostnameCur]:
				ioConfigsRB[hostnameCur].write('vrf context '+vrf+'\n')
				for entryCfg in configByHostAdd[hostnameCur][vrf]:
					ioConfigsRB[hostnameCur].write(" no ip route "+self.getRouteEntryCfg(entryCfg[0])+'\n')
					
		for hostnameCur in configByHostDel:
			if hostnameCur not in ioConfigsRB:
				ioConfigsRB[hostnameCur]=io.StringIO()
			ioConfigsRB[hostnameCur].write('! [RB] Correcting useless routes, routes deleting\n')
			for vrf in configByHostDel[hostnameCur]:
				ioConfigsRB[hostnameCur].write('vrf context '+vrf+'\n')
				for entryCfg in configByHostDel[hostnameCur][vrf]:
					ioConfigsRB[hostnameCur].write(" ip route "+self.getRouteEntryCfg(entryCfg[0])+'\n')		
	

		
		#Writing Config:
		print("Configuration directory:"+directory)
		
		"RO"
		for equipment in ioConfigsRO:
			RO_FILE=dir_ro+equipment.upper() +'.CFG'
			writeConfig(ioConfigsRO[equipment].getvalue(),RO_FILE)

		"RB"
		for equipment in ioConfigsRB:
			RB_FILE=dir_rb+equipment.upper() +'.CFG'
			writeConfig(ioConfigsRB[equipment].getvalue(),RB_FILE)
	
	def getRouteEntryCfg(self,entry):
		result=[]
		listSort=['prefix','interface', 'nh','otherAttributes']
	
			
		for key in listSort:
			if key in entry:
				result.append(entry[key])
		
		resultat=" ".join(result)
		
		return resultat
		
	def filteredByPrefix(self,ListeVrf,Net):
		Result={}
		
		for host__ in self.routes:
		
			if ListeVrf:
				Result[host__]=self.routes[host__].filteredByPrefix(ListeVrf,Net)
			else:
				ListeVrfCur=self.routes[host__].getAllVRF()
				Result[host__]=self.routes[host__].filteredByPrefix(ListeVrfCur,Net)
			
		return Result
		
	def filteredByIP(self,ListeVrf,Net):
		Result={}
		
		for host__ in self.routes:
			if ListeVrf:	
				Result[host__]=self.routes[host__].filteredByIP(ListeVrf,Net)
			else:
				ListeVrfCur=self.routes[host__].getAllVRF()
				Result[host__]=self.routes[host__].filteredByIP(ListeVrfCur,Net)				
			
		return Result
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-y", "--yaml",  action="store",help="yaml route informations",required=True)
	parser.add_argument("-i", "--interface",  action="store",help="dump interface informations",required=True)
	parser.add_argument("-x", "--xlsx",  action="store",help="File xlsx to save rapport",required=False)
	parser.add_argument("-r", "--resultat",  action="store",help="Configuration directory",required=False)
	args = parser.parse_args()
	
	MRTObj=MultipleRTContainer(args.yaml,args.interface)
	
	#print(MRTObj)
	
	#ppr(MRTObj.prefixes)
	
	#ppr(MRTObj.uniqRoute,width=600)
	
	if args.xlsx:
		saveXlsxFilename=DIR_RESULT+args.xlsx
		print(f'Saving report file{saveXlsxFilename}...')
		xlsMatrix(saveXlsxFilename,MRTObj.reportDict)
		
	if args.resultat:
		directoryCur=DIR_CONFIG+args.resultat+'/'
		if not os.path.exists(directoryCur):
			os.makedirs(directoryCur)

		MRTObj.genConfig(directoryCur)

