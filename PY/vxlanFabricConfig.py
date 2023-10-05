#!/usr/bin/env python3.8
# coding: utf-8

import jinja2
import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
import csv
import os
import yaml
import pyparsing as pp
import pickle
from netaddr import IPNetwork,IPAddress,iter_iprange
import re
import sys
import io
from textops import *

from connexion import *
from section import config_cisco
import cache as cc
from ParsingShow import ParseCdpNeighborDetailString
from cdpEnv import DC_cdp

TEMPLATE_DIR="/home/d83071/TEMPLATE/J2"
CONFIG_DIR="/home/d83071/CONF"
CSV_DNS_DIR="/home/d83071/CSV/INFOBLOX"

CSV_Example='''WNORM6-DFI-T-P01F01;1;WNORM6-DFI-T-P01X;Eth2/3
WNORM6-DFI-T-P01F01;5;WNORM6-DFI-T-P01Y;Eth2/3
WNORM6-DFI-T-P01F02;1;WNORM6-DFI-T-P01X;Eth2/4
WNORM6-DFI-T-P01F02;5;WNORM6-DFI-T-P01Y;Eth2/4'''

class netGenerator(object):
	def __init__(self, net,bitsplit,excluded_range=None,dump=""):
		if dump:
			self.load(dump)
		else:
			self.supernet= net
			self.supernetObj=IPNetwork(self.supernet)
			self.subnetsUsed=[]
			self.wildcard=bitsplit
			if excluded_range:
				if re.search('-',excluded_range):
					ipList=excluded_range.split('-')
					ipfirst=ipList[0]
					iplast=ipList[1]
					self.excludedIP=iter_iprange(ipfirst,iplast)
					self.list_excluded_range=list(self.excludedIP)
				else:
					self.excludedIP=None
					self.list_excluded_range=[]
			else:
				self.list_excluded_range=[]
					
	def testNetInRange(self,net):
		result=False
		ipfirst=IPAddress(net.first)
		iplast=IPAddress(net.last)
		if ipfirst in self.list_excluded_range or iplast in self.list_excluded_range:
			return True
		
		return result
		
	def save(self):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)

	def load(self, dump):
		with open(filename,'rb') as file__:
			netObj=pickle.load(file__)
			self.supertnet=netObj.net
			self.netsUsed=netObj.netsUsed
		
	def __iter__(self):
		first=True
		for net in self.supernetObj.subnet(self.wildcard):
			if net.__str__() not in self.subnetsUsed and not self.testNetInRange(net):
				if first:
					self.firstIP=IPAddress(net.first).__str__()
					first=False
				self.subnetsUsed.append(net.__str__())
				self.lastIP=IPAddress(net.last.__str__()).__str__()
				yield net.__str__()

	def getRange(self):
		return self.firstIP+'-'+self.lastIP
	
def getCdpDetail(hostname):
	commande=f'show cdp neighbor detail'
	con_get_cdp=connexion(equipement(hostname),None,'SSH',"TMP/"+hostname.lower()+"_shcdpdetail.log",commande_en_ligne=commande,timeout=30,verbose=False)
	cdpNeighbors=con_get_cdp.launch_withParser(ParseCdpNeighborDetailString)
	
	return cdpNeighbors
	
def suppressVlan(Str,listVlan):
	Resultat=Str
	for Vlan in listVlan:
		SpaceX=pp.White(' ',min=1)
		entryInterface=SpaceX+pp.OneOrMore(pp.CharsNotIn('\n'))
		BlocVlan=pp.Literal('interface Vlan'+Vlan)+pp.OneOrMore(entryInterface)
		suppressVlan=lambda t: ""
		BlocVlan.setParseAction(suppressVlan)
		strCur=Resultat
		Resultat=BlocVlan.transformString(strCur)
		
	return Resultat
	
def suppressBGPCommun(Str):
	Resultat=Str
	SpaceX=pp.White(' ',min=1)
	
	OtherBGP=pp.SkipTo(SpaceX+pp.Literal('vrf'))
	suppressBGP=lambda t: "\n"
	OtherBGP.setParseAction(suppressBGP)
	BlocBGP=pp.Literal('router bgp ')+pp.Word(pp.nums)+OtherBGP
	Resultat=BlocBGP.transformString(Str)
		
	return Resultat

def suppressOther(Str,ListStr):
	Resultat=Str
	for StrCur in ListStr:
		tmp=Resultat
		Resultat="\n".join(tmp|grepv(StrCur).tolist())
		
	return Resultat
	
class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)
Loader__.add_constructor('!include', Loader__.include)

def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
		
def initNetISIS(IP):
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 )).setParseAction(lambda s,l,t : t[0].rjust(3,'0'))
	ipAddress=pp.Combine(octet + (pp.Suppress(pp.Literal('.'))+octet)*3).setParseAction(lambda s,l,t : '49.0001.'+'.'.join(t[0][i:i+4] for i in range(0, len(t[0]), 4))+'.00')
	
	try:
		result=ipAddress.parseString(IP,parseAll=True).asList()[0]
		return result
	except pp.ParseException as e:
		print(f'Verify IP format:{IP}',file=sys.stderr)
		raise e
		
def readCsv(csvFilename):
	result=[]

	with open(csvFilename, newline='') as csvFile:
		spamreader = csv.reader(csvFile, delimiter=';', quotechar='|')
		for row in spamreader:
			result.append([ t.strip() for t in row] )
				
	return result

def parserSyncConfig(Str):
	
	ciscoConfigFileObj=config_cisco(None,data=Str)
	routerId=(ciscoConfigFileObj.extract('^interface loopback0$')|grep('address').tolist())[0].split()[-1].split('/')[0]
	filteredConfigRaw=ciscoConfigFileObj.extract('^vlan|vrf\ context|interface nve1|evpn')
	filteredConfig_wo_Vlan=suppressVlan(filteredConfigRaw,['1','6'])
	filteredConfigRaw2=suppressBGPCommun(filteredConfig_wo_Vlan)
	filteredConfig=suppressOther(filteredConfigRaw2,['ip route 0.0.0.0','vrf context management','nv overlay evpn','^vlan 2$','^vlan 3$','^vlan 6$','NATIVE','TRASH','UNDERLAY-BACK2BACK','vlan dot1Q tag native'])
	
	return { 'loopback0':routerId , 'config': filteredConfig }
	
class intercoIPN(IPNetwork):
	def __init__(self,net__):
		try:
			IPNetwork.__init__(self,net__)
		except:
			pdb.set_trace()
		
	def __add__(self,incr):
		return str(self.network+incr)+'/'+str(self.prefixlen)
		
class equipmentConfig(object):
	def __init__(self,dir,params,template):
		'''params:dict, template:jinja2 file'''
		self.params=params
		self.j2File=template
		#Loader Jinja
		self.loader = jinja2.FileSystemLoader(TEMPLATE_DIR+'/'+dir)
		self.env = jinja2.Environment( loader=self.loader)
		#add filter here
		vpcDomain=lambda t:str(int(t[-3:-1])+100)
		vpcPriority=lambda t: '4096' if t[-1]=='X' else '8192'
		ipOnly=lambda t: str(IPNetwork(t).ip)
		self.env.filters['netisis']=initNetISIS
		self.env.filters['vpcDomain']=vpcDomain
		self.env.filters['vpcPriority']=vpcPriority
		self.env.filters['ipOnly']=ipOnly
		self.env.filters['vlanvrf']=lambda t: str(50+int(t))
		self.env.filters['l3vnid']=lambda t: str(30000+int(t))
		self.env.filters['byVrf']=dataByVrf
		self.env.filters['l2vnid']=lambda t: str(20000+int(t))
		### template object
		self.template=self.env.get_template(os.path.basename(self.j2File))
			
		# config initialization
		self.config=self.template.render(self.params)
		
	def getConfig(self):
		return self.config
		
def dataByVrf(datas):
	datasByVrf={}

	for entry in datas:
		vrfCur=entry['vrf']
		entryCc=entry.copy()
		del entryCc['vrf']
		if vrfCur not in datasByVrf:
			datasByVrf[vrfCur]=[]
		datasByVrf[vrfCur].append(entryCc)
			
	return datasByVrf
	
class spineConfig(equipmentConfig):
	def __init__(self,params,newleaves=False,other=False):
		'''params:dict'''

		if newleaves:
			self.j2File='spineConfigForNewLeaf.j2'
		elif other:
			self.j2File='otherSpine.j2'
		else:
			self.j2File='spine.j2'
		super().__init__('VXLAN',params,self.j2File)
		
	
	
class leafConfig(equipmentConfig):
	def __init__(self,params):
		'''params:dict'''
		self.j2File='VXLAN/leaf.j2'
		super().__init__('VXLAN',params,self.j2File)
		
class interconnection(object):
		def __init__(self,tabInterco,IPInterco='0.0.0.0/0',first='A',l2Only=False,description=""):
			self.hostA=tabInterco[0]
			self.hostB=tabInterco[2]
			self.intA=tabInterco[1]
			self.intB=tabInterco[3]

			if not l2Only:
				self.IPInterco=IPInterco
				self.IPIntercoObj=IPNetwork(IPInterco)
				if first=='A':
					if self.IPIntercoObj.prefixlen==31:
						self.IPA=self.IPInterco
						self.IPB=intercoIPN(self.IPIntercoObj)+1
					elif self.IPIntercoObj.prefixlen<31:
						self.IPA=intercoIPN(self.IPIntercoObj)+1
						self.IPB=intercoIPN(self.IPIntercoObj)+2
					else:
						print(f'Network /32 is not possible:{self.IPInterco}',file=sys.stderr)
						os.exit(1)
				
				else:
					if self.IPIntercoObj.prefixlen==31:
						self.IPB=self.IPInterco
						self.IPA=intercoIPN(self.IPIntercoObj)+1
					elif self.IPIntercoObj.prefixlen<31:
						self.IPB=intercoIPN(self.IPIntercoObj)+1
						self.IPA=intercoIPN(self.IPIntercoObj)+2
					else:
						print(f'Network /32 is not possible:{self.IPInterco}',file=sys.stderr)
						os.exit(1)
				
			
		def __str__(self):
			return pprs(self.__dict__)
			
		def __repr__(self):
			return pprs(self.__dict__)
			

class csvInfoBlox(object):
	def __init__(self, intercos,tag,ips=[]):
		self.interconnexions=intercos
		addQuote=lambda y: '"'+y+'"'
		self.headers_network_str='header-network,address*,netmask*,always_update_dns,basic_polling_settings,boot_file,boot_server,broadcast_address,comment,ddns_domainname,ddns_ttl,deny_bootp,dhcp_members,disabled,discovery_exclusion_range,discovery_member,domain_name,domain_name_servers,enable_ddns,enable_discovery,enable_option81,enable_pxe_lease_time,enable_threshold_email_warnings,enable_threshold_snmp_warnings,enable_thresholds,generate_hostname,ignore_client_requested_options,is_authoritative,lease_scavenge_time,lease_time,mgm_private,network_view,next_server,option_logic_filters,pxe_lease_time,range_high_water_mark,range_high_water_mark_reset,range_low_water_mark,range_low_water_mark_reset,recycle_leases,routers,threshold_email_addresses,update_dns_on_lease_renewal,update_static_leases,vlans,zone_associations,EA-IPAM_Allow_DNSaaS,EAInherited-IPAM_Allow_DNSaaS'
		self.headers_host_str='header-hostrecord,addresses*,configure_for_dns*,view,fqdn*'
		#self.headers_host=['IP Address','Name','MAC Address','DHCP Client Identifier','Status','Type','Discover Now','Usage','Lease State','User Name','Task Name','First Discovered','Last Discovered','OS','NetBIOS Name','Device Type(s)','Open Port(s)','Fingerprint','Comment','Site']
		self.headers_network=self.headers_network_str.split(',')
		self.headers_host=self.headers_host_str.split(',')
		self.headers_network_ref={value:num for num,value in enumerate(self.headers_network,0)}
		self.headers_host_ref={value:num for num,value in enumerate(self.headers_host,0)}
		#self.netDatas=[list(map(addQuote,self.headers_network))]
		#self.hostDatas=[list(map(addQuote,self.headers_host))]
		self.netDatas=[self.headers_network]
		self.hostDatas=[self.headers_host]
		self.loopbackDatas=[self.headers_host]
		self.defaultLineNet=[ "" for i in self.headers_network]
		self.defaultLineHost=[ "" for i in self.headers_host]
		self.csvDir=CSV_DNS_DIR+"/"+tag.replace(' ','_')
		if not os.path.exists(self.csvDir):
			os.makedirs(self.csvDir)
		self.initDataNet()
		self.initDataHost(otherIP=ips)
		
	def initDataNet(self):
		for interco in self.interconnexions:
			commentCur=f'{interco.hostA.upper()} & {interco.hostB.upper()}'
			netCurObj=interco.IPIntercoObj
			netCur=str(netCurObj.ip)
			maskCur=str(netCurObj.netmask)
			lineCur=self.defaultLineNet.copy()
			lineCur[self.headers_network_ref['header-network']]='network'
			lineCur[self.headers_network_ref['address*']]=netCur
			lineCur[self.headers_network_ref['netmask*']]=maskCur
			lineCur[self.headers_network_ref['comment']]=commentCur
			lineCur[self.headers_network_ref['disabled']]='False'
			lineCur[self.headers_network_ref['enable_threshold_email_warnings']]='False'
			lineCur[self.headers_network_ref['enable_threshold_snmp_warnings']]='False'
			lineCur[self.headers_network_ref['mgm_private']]='False'
			lineCur[self.headers_network_ref['network_view']]='default'
			lineCur[self.headers_network_ref['EA-IPAM_Allow_DNSaaS']]='no'
			lineCur[self.headers_network_ref['EAInherited-IPAM_Allow_DNSaaS']]='OVERRIDE'
			self.netDatas.append(lineCur)
		
	def initDataHost(self,otherIP=[]):
		
		for interco in self.interconnexions:
			ipA=interco.IPA.split('/')[0]
			ipB=interco.IPB.split('/')[0]
			nameA=interco.hostA.lower()+'_'+interco.intA.lower().replace('/','-')+'.fr.net.intra'
			nameB=interco.hostB.lower()+'_'+interco.intB.lower().replace('/','-')+'.fr.net.intra'
			lineCurA=self.defaultLineHost.copy()
			lineCurB=self.defaultLineHost.copy()
			lineCurA[self.headers_host_ref['addresses*']]=ipA
			lineCurA[self.headers_host_ref['fqdn*']]=nameA
			lineCurA[self.headers_host_ref['header-hostrecord']]='hostrecord'
			lineCurA[self.headers_host_ref['view']]='default'
			lineCurA[self.headers_host_ref['configure_for_dns*']]='true'
			lineCurB[self.headers_host_ref['addresses*']]=ipB
			lineCurB[self.headers_host_ref['fqdn*']]=nameB
			lineCurB[self.headers_host_ref['header-hostrecord']]='hostrecord'
			lineCurB[self.headers_host_ref['view']]='default'
			lineCurB[self.headers_host_ref['configure_for_dns*']]='true'
			self.hostDatas.append(lineCurA)
			self.hostDatas.append(lineCurB)
			
		for ip in otherIP:
			lineCur=self.defaultLineHost.copy()
			lineCur[self.headers_host_ref['addresses*']]=ip['ip']
			lineCur[self.headers_host_ref['fqdn*']]=ip['hostname'].lower()+'_'+ip['if'].lower().replace('/','-')+'.fr.net.intra'
			lineCur[self.headers_host_ref['header-hostrecord']]='hostrecord'
			lineCur[self.headers_host_ref['view']]='default'
			lineCur[self.headers_host_ref['configure_for_dns*']]='true'
			self.loopbackDatas.append(lineCur)
			
	def writeCsvData(self,filename_,datas):
		file=open(filename_,'w')

		writer=csv.writer(file,delimiter=";")
		
		with file:
			writer.writerows(datas)
			
	def writeNet(self,filename_):
		self.filenameNet=self.csvDir+'/'+filename_
		self.writeCsvData(self.filenameNet,self.netDatas)
		
	def writeHost(self,filename_):
		self.filenameHost=self.csvDir+'/'+filename_
		self.writeCsvData(self.filenameHost,self.hostDatas)

	def writeLoopback(self,filename_):
		self.filenameLoopback=self.csvDir+'/'+filename_
		self.writeCsvData(self.filenameLoopback,self.loopbackDatas)

			
			
class fabricConfig(object):
	def __init__(self,fileYaml,newleaves=False,caching=False,sync=False):
		'''params:dict'''
		with open(args.yaml, 'r') as yml__:
			self.params=yaml.load(yml__,Loader__)
			
		for key,item in self.params['fabric'].items():
			super().__setattr__(key,item)
		try:
			if "excluded_range" in self.pool:
				self.excludedIPRange=self.pool['excluded_range']
				self.netGenObj=netGenerator(self.pool['interco'],31,excluded_range=self.excludedIPRange)
				self.IPintercoGen=iter(self.netGenObj)
			else:
				self.netGenObj=netGenerator(self.pool['interco'],31)
				self.IPintercoGen=iter(self.netGenObj)
		except AttributeError as E:
			pdb.set_trace()
			print(f'Please define pool: interco in yaml',file=sys.stderr)
		self.vpcIfs={}
		self.vpcs={}
		self.configSync={}
		self.caching=caching
		self.sync=sync
		self.masterHostLeaves={'CIS-A':{'MARNE NORD':'RNORM5-CIS-A-AL04X','MARNE EST':'REST11-CIS-A-AL06X'} ,'SIAA':{'MARNE NORD': 'RNORM5-SIA-A-AL15X','MARNE EST':'REST12-SIA-A-AL16X'}}		
		
		if sync:
			self.configSync=self.getSyncConfig()
			
		if not 'other_spines' in self.params['fabric']:
			self.other_spines={}

		self.newleavesOnly=newleaves
		self.interconnections=[]
		self.descriptionMgmt={}
		self.initInterco()
		self.initDataIf()
		self.initDataNeighborBGP()
		self.initVPCCouple()
		self.initDataVpc()
		self.config={}
		self.configDir=CONFIG_DIR+'/VXLAN/'+self.name.replace(' ','_')
	
	@staticmethod
	def	getSnmpInfoFromEquipment(hostname,location):
		snmp={}
		type='UNKNOWN'
		prefix=hostname.split('-')[0][1:]
		if 'BA' in prefix:
			if prefix[2]=='N':
				snmp['contact']='BASTOGNE NORD'
				snmp['location']=f'/BASTOGNE NORD/{location}'
			elif prefix[2]=='S':
				snmp['contact']='BASTOGNE SUD'
				snmp['location']=f'/BASTOGNE SUD/{location}'
		elif 'NOR' or 'EST' in prefix:
			if 'NOR' in prefix:
				snmp['contact']='MARNE NORD'
				snmp['location']=f'/MARNE NORD/{location}'
			elif 'EST' in prefix:
				snmp['contact']='MARNE EST'
				snmp['location']=f'/MARNE EST/{location}'

		return snmp
		
	def getSiteFromEquipment(self,hostname):
		prefix=hostname.split('-')[0][1:]
		if 'BA' in prefix:
			if prefix[2]=='N':
				site='BASTOGNE NORD'
			elif prefix[2]=='S':
				site=='BASTOGNE SUD'
				snmp['location']=f'/BASTOGNE SUD/{location}'
		elif 'NOR' or 'EST' in prefix:
			if 'NOR' in prefix:
				site='MARNE NORD'
			elif 'EST' in prefix:
				site='MARNE EST'
		environment="-".join(hostname.split('-')[1:2])
		return {'env': environment, 'site': site }
		
	@staticmethod
	def	getTypeEquipment(hostname):
		type='UNKNOWN'
		suffixe=hostname.split('-')[-1][:2]
		if suffixe=="AL":
			type="SERVER"
		elif suffixe=="BL":
			type="BORDER"
		elif suffixe=="SP":
			type="SPINE"
		return type
		
	@staticmethod
	def getSuffixDescription(type):
		suffixdesc={'UNKNOWN':"_Uplink_To","BORDER":"_Uplink_To_BLeaft" , "SERVER": "_Uplink_To_Leaft" ,  "SPINE":"_Uplink_To_Spine"  }
		
		if type in suffixdesc:
			return suffixdesc[type]
		else:
			return suffixdesc['UNKNOWN']
			
	@staticmethod
	def getSuffixDescriptionFromHostname(hostname):
		return fabricConfig.getSuffixDescription(fabricConfig.getTypeEquipment(hostname))
			
	def initInterco(self):
		if 'matrix' in self.params['fabric']:
			if  self.params['fabric']['matrix']['mode']=='csv':
				self.tab_interconnections=readCsv(self.params['fabric']['matrix']['file'])
				print(self.tab_interconnections)

			elif self.params['fabric']['matrix']['mode']=='cdp':
				self.cdpN9K={}
				for leaf in self.leaves:
					tagCur='CDPDETAIL_'+leaf.upper()
					cacheCdpCur=cc.Cache(tagCur)
					if self.caching:
						if cacheCdpCur.isOK():
							print(f'info in cache for cdp leaf {leaf} is used')
							self.cdpN9K[leaf]=cacheCdpCur.getValue()
						else:
							print(f'info in cache for cdp leaf {leaf} is absent')
							self.cdpN9K[leaf]=getCdpDetail(leaf)
							cacheCdpCur.save(self.cdpN9K[leaf])
					else:
						self.cdpN9K[leaf]=getCdpDetail(leaf)
						cacheCdpCur.save(self.cdpN9K[leaf])
				if not self.newleavesOnly:
					for spine in self.spines:
						tagCur='CDPDETAIL_'+spine.upper()
						cacheCdpCur=cc.Cache(tagCur)
						if self.caching:
							if cacheCdpCur.isOK():
								print(f'info in cache for cdp spine {spine} is used')
								self.cdpN9K[spine]=cacheCdpCur.getValue()
							else:
								print(f'info in cache for cdp spine {spine} is absent')
								self.cdpN9K[spine]=getCdpDetail(spine)
								cacheCdpCur.save(self.cdpN9K[spine])
						else:
							self.cdpN9K[spine]=getCdpDetail(spine)
							cacheCdpCur.save(self.cdpN9K[spine])
				envCdpCtn=DC_cdp(dictResult=self.cdpN9K)
				self.tab_interconnections=envCdpCtn.interco.toList()
				'stop'
			for interco__ in self.tab_interconnections:
				if re.search('mgmt',interco__[1],re.IGNORECASE):
					self.descriptionMgmt[interco__[0]]=f'{interco__[2]}_{interco__[3]}'
				elif re.search('mgmt',interco__[3],re.IGNORECASE):
					self.descriptionMgmt[interco__[2]]=f'{interco__[0]}_{interco__[1]}'
				elif  interco__[0] in self.params['fabric']['leaves'] and interco__[2] in self.params['fabric']['leaves']:
					if interco__[0] not in self.vpcIfs:
						self.vpcIfs[interco__[0]]=[interconnection(interco__,l2Only=True)]
					else:
						self.vpcIfs[interco__[0]].append(interconnection(interco__,l2Only=True))
					if interco__[2] not in self.vpcIfs:
						self.vpcIfs[interco__[2]]=[interconnection(interco__,l2Only=True)]
					else:
						self.vpcIfs[interco__[2]].append(interconnection(interco__,l2Only=True))
				else:
					if interco__[2] in self.params['fabric']['spines']:
						self.interconnections.append(interconnection(interco__,next(self.IPintercoGen),"B"))
					elif interco__[2] in self.params['fabric']['other_spines']:
						self.interconnections.append(interconnection(interco__,next(self.IPintercoGen)))						
					else:
						pass
	def initSpinesConfig(self):
		self.spinesConfig={}
		for spine,data in self.spines.items():
			self.spinesConfig[spine]=spineConfig(self.getGlobalData(spine,data),newleaves=self.newleavesOnly)
			self.config[spine]=self.spinesConfig[spine]
	
	def initOtherSpinesConfig(self):
		if not 'other_spines' in self.params['fabric']:
			return 
		self.otherSpinesConfig={}
		for spine,data in self.other_spines.items():
			self.otherSpinesConfig[spine]=spineConfig(self.getGlobalData(spine,data),other=True)
			self.config[spine]=self.otherSpinesConfig[spine]
			
	def initLeavesConfig(self):
	
		self.leavesConfig={}
		for leaf,data in self.leaves.items():
			self.leavesConfig[leaf]=leafConfig(self.getGlobalData(leaf,data))
			self.config[leaf]=self.leavesConfig[leaf]
			
	def initVPCCouple(self):
		self.vpcs['couple']={}
		result={}
		for host__ in self.leaves:
			if host__[:-1]  not in result:
				if host__[-1] =='X':
					result[host__[:-1] ]={'primary': {'hostname':host__}}
				elif host__[-1] =='Y':
					result[host__[:-1] ]={'secondary':{'hostname':host__}}
			else:
				if host__[-1] =='X':
					result[host__[:-1] ]['primary']={'hostname':host__}
				elif host__[-1] =='Y':
					result[host__[:-1] ]['secondary']={'hostname':host__}	
					
		for key,value in result.items():
			if len(value)==2:
				self.vpcs['couple'][key]=value

		for prefix_host in self.vpcs['couple']:
			interco_infra=interconnection([self.vpcs['couple'][prefix_host]['primary']['hostname'],'Vlan50',self.vpcs['couple'][prefix_host]['secondary']['hostname'],'Vlan50' ],next(self.IPintercoGen),description="VPC INFRA VLAN")
			self.interconnections.append(interco_infra)
			self.vpcs['couple'][prefix_host]['primary']['ipVlanInfra']=interco_infra.IPA
			self.vpcs['couple'][prefix_host]['secondary']['ipVlanInfra']=interco_infra.IPB
			
				
	
	def initDataIf(self):
		self.interfaces={}
		
		for interco__ in self.interconnections:
			if interco__.hostA not in self.interfaces:
				self.interfaces[interco__.hostA]=[]
			if interco__.hostB not in self.interfaces:
				self.interfaces[interco__.hostB]=[]
				

			self.interfaces[interco__.hostA].append({'name': interco__.intA, 'description':f'{fabricConfig.getSuffixDescriptionFromHostname(interco__.hostB)}_{interco__.hostB}_{interco__.intB}' , 'ip': interco__.IPA })
			self.interfaces[interco__.hostB].append({'name': interco__.intB, 'description':f'{fabricConfig.getSuffixDescriptionFromHostname(interco__.hostA)}_{interco__.hostA}_{interco__.intA}' , 'ip': interco__.IPB })
			
	def initDataNeighborBGP(self):
		self.neighbors={}

		for interco__ in self.interconnections:
			if interco__.hostA not in self.neighbors:
				self.neighbors[interco__.hostA]=[]
			if interco__.hostB not in self.neighbors:
				self.neighbors[interco__.hostB]=[]
				
			if interco__.hostA in self.spines:
				typeA="spine"
				ipa= self.spines[interco__.hostA]['loopback0']
			elif interco__.hostA in self.leaves:
				typeA="leaf"
				ipa= self.leaves[interco__.hostA]['loopback0']
			elif interco__.hostA in self.other_spines:
				typeA="other_spine"
				ipa=self.other_spines[interco__.hostA]['loopback0']
			else:
				typeA="unknown"
				ipa='TBD'

			if interco__.hostB in self.spines:
				typeB="spine"
				ipb= self.spines[interco__.hostB]['loopback0']
			elif interco__.hostB in self.leaves:
				typeB="leaf"
				ipb= self.leaves[interco__.hostB]['loopback0']
			elif interco__.hostB in self.other_spines:
				typeB="other_spine"
				ipb=self.other_spines[interco__.hostB]['loopback0']
			else:
				typeB="unknown"
				ipb='TBD'
			
			try:
				self.neighbors[interco__.hostA].append({'type':typeB,'ip': ipb, 'hostname':interco__.hostB })
				self.neighbors[interco__.hostB].append({'type':typeA,'ip': ipa, 'hostname':interco__.hostA })
			except KeyError as E:
				pdb.set_trace()
				print(E)
			
	
	def initDataVpc(self):
		for host__ in self.vpcIfs:
			self.vpcs[host__]={}
			self.vpcs[host__]['interfaces']=[]
			

			for member in self.vpcs['couple'][host__[:-1]]:
				if self.vpcs['couple'][host__[:-1]][member]['hostname']==host__: 
					self.vpcs[host__]['infraip']=self.vpcs['couple'][host__[:-1]][member]['ipVlanInfra']
			
			for interco__ in self.vpcIfs[host__]:
				if interco__.hostA == host__:
					self.vpcs[host__]['interfaces'].append({'name':interco__.intA , 'otherMember': { 'hostname': interco__.hostB, 'intf': interco__.intB} })
					if 'otherMemberIP' not in self.vpcs[host__]:
						self.vpcs[host__]['otherMember']={'ip': self.leaves[interco__.hostB]['mgmt'] , 'hostname':interco__.hostB }
				elif interco__.hostB == host__:
					self.vpcs[host__]['interfaces'].append({'name':interco__.intB , 'otherMember': { 'hostname': interco__.hostA, 'intf': interco__.intA} })
					if 'otherMemberIP' not in self.vpcs[host__]:
						self.vpcs[host__]['otherMember']={'ip': self.leaves[interco__.hostA]['mgmt'] , 'hostname':interco__.hostA }					
			'stop'
	
	def getGlobalData(self,hostname,otherData):
	
		result=self.params['fabric'].copy()

		result['hostname']=hostname
		for key,item in otherData.items():
			result[key]=item
			
		if hostname in self.params['fabric']['leaves']:
			type_cur='leaves'
		elif hostname in self.params['fabric']['spines']:
			type_cur='spines'
		elif hostname in self.params['fabric']['other_spines']:
			type_cur='other_spines'
		else:
			type_cur='unknown'		
			
		
		try:
			result['interfaces']=self.interfaces[hostname]
		except KeyError as E:
			pdb.set_trace()
			print(E)
		result['neighbors']=self.neighbors[hostname]
		
		if type_cur=='leaves':
			result['vpc']=self.vpcs[hostname]
		
		
		if type_cur!='other_spines':
			try:
				result['management']['ip']=self.params['fabric'][type_cur][hostname]['mgmt']
			except KeyError:
				result['management']['ip']='UNKNOWN'
			try:
				result['management']['description']=self.descriptionMgmt[hostname]
			except KeyError:
				result['management']['description']='TBD'
				
			if 'location' in self.params['fabric'][type_cur][hostname]:
				snmp_cur=self.getSnmpInfoFromEquipment(hostname,self.params['fabric'][type_cur][hostname]['location'])
			else:
				snmp_cur=self.getSnmpInfoFromEquipment(hostname,'UNKNOWN')
			result.update(snmp_cur)
			
			result['sync']=self.configSync
			
				
		del result['leaves']
		del result['spines']
		
		return result
		

	def getIPLoopback(self):
		ips=[]
		ip_already_used=[]
		for leaf in self.leaves:
			for attr in self.leaves[leaf]:
				if re.search('^loopback',attr,re.IGNORECASE):
					ifCur=attr.replace('opback','')
					if isinstance( self.leaves[leaf][attr] ,dict):
						for type in self.leaves[leaf][attr]:
							ip=self.leaves[leaf][attr][type]
							if type=='primary':
								host=leaf
							elif type=='secondary':
								host=leaf[:-1]+'X_Y'
								ifCur='VIP'
							if ip not in ip_already_used:
								ips.append({'ip':ip , 'if':ifCur,'hostname':host})
					else:
						ip=self.leaves[leaf][attr]
						host=leaf
						if ip not in ip_already_used:
							ips.append({'ip':ip , 'if':ifCur,'hostname':host})						
								
		for spine in self.spines:
			for attr in self.spines[spine]:
				if re.search('^loopback',attr,re.IGNORECASE):
					ifCur=attr.replace('opback','')
					ip=self.spines[spine][attr]
					host=spine
					if ip not in ip_already_used:
						ips.append({'ip':ip , 'if':ifCur,'hostname':host})			
						
		return ips

	def writeCfg(self):
		if not os.path.exists(self.configDir):
			os.makedirs(self.configDir)
			
		for equipment__ in self.config:
			writeConfig(self.config[equipment__].getConfig(),self.configDir+'/'+equipment__+'.CFG')
			

	def getSyncHost(self):
		infoCur=self.getSiteFromEquipment(list(self.leaves.keys())[0])
		masterHost=self.masterHostLeaves[infoCur['env']][infoCur['site']]
		return masterHost
		
	def getSyncConfig(self):
		
		result={}
		self.masterHostLeaf=self.getSyncHost()
		TAG_SYNC_HOST='SYNC_'+self.masterHostLeaf
		cacheSyncHost=cc.Cache(TAG_SYNC_HOST)
		if self.caching:
			if cacheSyncHost.isOK():
				print(f'info in cache sync for {self.masterHostLeaf} is used')
				runningConfigMaster=cacheSyncHost.getValue()
				for leaf in self.leaves:
					result[leaf]=runningConfigMaster['config'].replace(runningConfigMaster['loopback0'],self.leaves[leaf]['loopback0'])
				return result

		commande=f'show run'
		if self.caching:
			print(f'cache sync for {self.masterHostLeaf} is absent')
			
		con_get_running=connexion(equipement(self.masterHostLeaf),None,'SSH',"TMP/"+self.masterHostLeaf.lower()+"_shrun.log",commande_en_ligne=commande,timeout=100,verbose=False)
		runningConfigMaster=con_get_running.launch_withParser(parserSyncConfig)
		cacheSyncHost.save(runningConfigMaster)

		
		
		for leaf in self.leaves:
			result[leaf]=runningConfigMaster['config'].replace(runningConfigMaster['loopback0'],self.leaves[leaf]['loopback0'])
	
		return result
		
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-y","--yaml",action="store",help="yaml file that contains fabric Vxlan informations ",required=True)
	parser.add_argument("-t","--tag" ,action="append",help="tag ",required=False)
	parser.add_argument("--new-leaves",dest='newLeaves' ,action="store_true",help="mode new leaves ",required=False,default=False)
	parser.add_argument("--net-iblox-csv",dest='csvnet' ,action="store",help="generate csv file to export in iblox (net)",required=False)
	parser.add_argument("--ip-iblox-csv",dest='csvip' ,action="store",help="generate csv file to export in iblox (ip)",required=False)
	parser.add_argument("--lo-iblox-csv",dest='csvlo' ,action="store",help="generate csv file to export in iblox (loopback)",required=False)
	parser.add_argument("--all-iblox-csv",dest='csvall' ,action="store",help="generate all csv file to export in iblox",required=False)
	parser.add_argument("--sync-host",dest='syncHost' ,action="store_true",help="sync config with existing host",required=False)
	parser.add_argument("--cache",dest='cache' ,action="store_true",help="use cache config",required=False)
	args = parser.parse_args()
	
	curFabric=fabricConfig(args.yaml,newleaves=args.newLeaves,caching=args.cache,sync=args.syncHost)
	curFabric.initSpinesConfig()
	curFabric.initLeavesConfig()
	curFabric.initOtherSpinesConfig()
	curFabric.writeCfg()
	
	
	ppr(curFabric.interconnections,width=300)
	ppr(curFabric.vpcs,width=300)
	
	ips=curFabric.getIPLoopback()
	
	print(curFabric.netGenObj.getRange())
	
	if args.csvnet or args.csvip or args.csvlo or args.csvall:
		
		if not args.newLeaves:
			csvGen=csvInfoBlox(curFabric.interconnections,curFabric.name,ips=ips)
		else:
			ipsWoSpine=list(filter( lambda y: True if '-SP' not in y['hostname'] else False,ips))
			csvGen=csvInfoBlox(curFabric.interconnections,curFabric.name,ips=ipsWoSpine)
		pdb.set_trace()
		if args.csvnet:
			csvGen.writeNet(args.csvnet)
		if args.csvip:
			csvGen.writeHost(args.csvip)
		if args.csvlo:
			csvGen.writeLoopback(args.csvlo)
		if args.csvall:
			fileNet=args.csvall+'_NET.CSV'
			fileIP=args.csvall+'_IP.CSV'
			fileLo=args.csvall+'_LO.CSV'
			csvGen.writeNet(fileNet)
			csvGen.writeHost(fileIP)
			csvGen.writeLoopback(fileLo)
	
	
