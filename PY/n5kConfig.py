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

TEMPLATE_DIR="/home/d83071/TEMPLATE/J2"
CONFIG_DIR="/home/d83071/CONF"
CSV_DNS_DIR="/home/d83071/CSV/INFOBLOX"

CSV_Example='''WNORM6-DFI-T-P01F01;1;WNORM6-DFI-T-P01X;Eth2/3
WNORM6-DFI-T-P01F01;5;WNORM6-DFI-T-P01Y;Eth2/3
WNORM6-DFI-T-P01F02;1;WNORM6-DFI-T-P01X;Eth2/4
WNORM6-DFI-T-P01F02;5;WNORM6-DFI-T-P01Y;Eth2/4'''

		
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
	
class interconnection(object):
		def __init__(self,tabInterco,description=""):
			self.hostA=tabInterco[0]
			self.hostB=tabInterco[2]
			self.intA=tabInterco[1]
			self.intB=tabInterco[3]

		
			
		def __str__(self):
			return pprs(self.__dict__)
			
		def __repr__(self):
			return pprs(self.__dict__)
			
			
class equipmentConfig(object):
	def __init__(self,dir,params,template):
		'''params:dict, template:jinja2 file'''
		self.params=params
		self.j2File=template
		#Loader Jinja
		self.loader = jinja2.FileSystemLoader(TEMPLATE_DIR+'/'+dir)
		self.env = jinja2.Environment( loader=self.loader)
		#add filter here
		vpcDomain=lambda t:str(int(t[-2])+100)
		vpcPriority=lambda t: '4096' if t[-1]=='X' else '8192'
		priority=lambda t: '1' if t[-1]=='X' else '10'
		ipOnly=lambda t: str(IPNetwork(t).ip)
		self.env.filters['netisis']=initNetISIS
		self.env.filters['vpcDomain']=vpcDomain
		self.env.filters['vpcPriority']=vpcPriority
		self.env.filters['priority']=priority
		self.env.filters['ipOnly']=ipOnly
		### template object
		self.template=self.env.get_template(os.path.basename(self.j2File))
			
		# config initialization
		self.config=self.template.render(self.params)
		
	def getConfig(self):
		return self.config
		
		
class n7kConfig(equipmentConfig):
	def __init__(self,params):
		'''params:dict'''
		self.j2File='FABRICPATH/n7k.j2'
		super().__init__('FABRICPATH',params,self.j2File)
		
	
	
class n5kConfig(equipmentConfig):
	def __init__(self,params):
		'''params:dict'''
		self.j2File='FABRICPATH/n5k.j2'
		super().__init__('FABRICPATH',params,self.j2File)
		

class fabricLegacyConfig(object):
	def __init__(self,fileYaml):
		'''params:dict'''
		with open(args.yaml, 'r') as yml__:
			self.params=yaml.load(yml__,Loader__)
			
		for key,item in self.params['fabric'].items():
			super().__setattr__(key,item)

		self.vpcIfs={}
		self.vpcs={}
		self.interconnections=[]
		self.descriptionMgmt={}
		self.initInterco()
		self.initDataIf()
		self.initVPCCouple()
		self.initDataVpc()
		self.config={}
		self.configDir=CONFIG_DIR+'/FABRICPATH/'+self.name.replace(' ','_')
	
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
		
	def	getTypeEquipment(hostname):
		type='UNKNOWN'
		suffixe=hostname.split('-')[-1][:2]
		if suffixe[0]=="W":
			type="LEAF"
		elif suffixe[0]=="R":
			type="SPINE"
		return type
		
			
	def initInterco(self):
		self.n7ks={}
		if 'matrix' in self.params['fabric']:
			if  self.params['fabric']['matrix']['mode']=='csv':
				self.tab_interconnections=readCsv(self.params['fabric']['matrix']['file'])
				for interco__ in self.tab_interconnections:
					if re.search('mgmt',interco__[1],re.IGNORECASE):
						self.descriptionMgmt[interco__[0]]=f'{interco__[2]}_{interco__[3]}'
					elif re.search('mgmt',interco__[3],re.IGNORECASE):
						self.descriptionMgmt[interco__[2]]=f'{interco__[0]}_{interco__[1]}'
					elif  interco__[0] in self.params['fabric']['n5ks'] and interco__[2] in self.params['fabric']['n5ks']:
						if interco__[0] not in self.vpcIfs:
							self.vpcIfs[interco__[0]]=[interconnection(interco__)]
						else:
							self.vpcIfs[interco__[0]].append(interconnection(interco__))
						if interco__[2] not in self.vpcIfs:
							self.vpcIfs[interco__[2]]=[interconnection(interco__)]
						else:
							self.vpcIfs[interco__[2]].append(interconnection(interco__))
					else:
						if interco__[0] not in self.params['fabric']['n5ks']:
							self.n7ks[interco__[0]]={}
						elif interco__[2] not in self.params['fabric']['n5ks']:
							self.n7ks[interco__[2]]={}
							
						self.interconnections.append(interconnection(interco__))
	
			
	def initN7ksConfig(self):
		self.n7ksConfig={}
		for n7k,data in self.n7ks.items():
			self.n7ksConfig[n7k]=n7kConfig(self.getGlobalData(n7k,data))
			self.config[n7k]=self.n7ksConfig[n7k]
	

			
	def initN5ksConfig(self):
	
		self.n5ksConfig={}
		for n5k,data in self.n5ks.items():
			self.n5ksConfig[n5k]=n5kConfig(self.getGlobalData(n5k,data))
			self.config[n5k]=self.n5ksConfig[n5k]
			
	def initVPCCouple(self):
		self.vpcs['couple']={}
		result={}
		for host__ in self.n5ks:
			if host__[:-1]  not in result:
				if 'MX' in host:
					result[host__[:-1] ]={'primary': {'hostname':host__}}
				elif 'MY' in host:
					result[host__[:-1] ]={'secondary':{'hostname':host__}}
			else:
				if 'MX' in host:
					result[host__[:-1] ]['primary']={'hostname':host__}
				elif 'MY' in host:
					result[host__[:-1] ]['secondary']={'hostname':host__}	
					
		for key,value in result.items():
			if len(value)==2:
				self.vpcs['couple'][key]=value

			
	
	def initDataIf(self):
		self.interfaces={}
		
		for interco__ in self.interconnections:
			if interco__.hostA not in self.interfaces:
				self.interfaces[interco__.hostA]=[]
			if interco__.hostB not in self.interfaces:
				self.interfaces[interco__.hostB]=[]
				

			self.interfaces[interco__.hostA].append({'name': interco__.intA, 'destination':{ 'hostname': interco__.hostB, 'ifName':interco__.intB}})
			self.interfaces[interco__.hostB].append({'name': interco__.intB, 'destination':{ 'hostname': interco__.hostA, 'ifName':interco__.intA}})
			
				
	
	def initDataVpc(self):
		for host__ in self.vpcIfs:
			self.vpcs[host__]={}
			self.vpcs[host__]['interfaces']=[]
			
			
			for interco__ in self.vpcIfs[host__]:
				if interco__.hostA == host__:
					self.vpcs[host__]['interfaces'].append({'name':interco__.intA , 'otherMember': { 'hostname': interco__.hostB, 'intf': interco__.intB} })
					if 'otherMemberIP' not in self.vpcs[host__]:
						self.vpcs[host__]['otherMember']={'ip': self.n5ks[interco__.hostB]['mgmt'] , 'hostname':interco__.hostB }
				elif interco__.hostB == host__:
					self.vpcs[host__]['interfaces'].append({'name':interco__.intB , 'otherMember': { 'hostname': interco__.hostA, 'intf': interco__.intA} })
					if 'otherMemberIP' not in self.vpcs[host__]:
						self.vpcs[host__]['otherMember']={'ip': self.n5ks[interco__.hostA]['mgmt'] , 'hostname':interco__.hostA }					

	
	def getGlobalData(self,hostname,otherData):
	
		result=self.params['fabric'].copy()

		result['hostname']=hostname
		for key,item in otherData.items():
			result[key]=item
			
		if hostname in self.params['fabric']['n5ks']:
			type_cur='leaf'
		else:
			type_cur='spine'
			
		
		try:
			result['interfaces']=self.interfaces[hostname]
		except KeyError as E:
			pdb.set_trace()
			print(E)
		
		if type_cur=='leaf':
			result['management']['ip']=self.params['fabric']['n5ks'][hostname]['mgmt']
			try:
				result['management']['description']=self.descriptionMgmt[hostname]
			except KeyError:
				result['management']['description']='TBD'
			result['vpc']=self.vpcs[hostname]
			result['vpc'].update(self.vpcGlobal)
				
			snmp_cur=self.getSnmpInfoFromEquipment(hostname,self.params['fabric']['n5ks'][hostname]['location'])
			result.update(snmp_cur)
		
		del result['n5ks']

		
		return result
		


	def writeCfg(self):
		if not os.path.exists(self.configDir):
			os.makedirs(self.configDir)
			
		for equipment__ in self.config:
			writeConfig(self.config[equipment__].getConfig(),self.configDir+'/'+equipment__+'.CFG')
			

	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-y","--yaml",action="store",help="yaml file that contains fabric Vxlan informations ",required=True)

	args = parser.parse_args()
	
	curFabric=fabricLegacyConfig(args.yaml)
	curFabric.initN7ksConfig()
	curFabric.initN5ksConfig()
	curFabric.writeCfg()
	
	
	ppr(curFabric.interconnections,width=300)
	ppr(curFabric.vpcs,width=300)
	

	
	
