#!/usr/bin/env python3.8
# coding: utf-8


import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
import yaml
import os
import shutil
import re
from time import gmtime, strftime , localtime
import json
from textops import *

from connexion import runActionCache , runListData , getHostsFromEnv , equipement
from vxlanFabricConfig import equipmentConfig
from section import config_cisco
import ParseVlanListe
from ipEnv import ifEntries
from ParsingShow import *
from xlsxToDict import xlsContainer
YAML_ENV="/home/d83071/yaml/DEFAULT_ENV.yml"
YML_PATH_FABRIC="/home/d83071/yaml/fabric"
YML_PATH_FABRIC_CFG="/home/d83071/yaml/fabric/config"
BCK_YML_PATH_FABRIC="/home/d83071/yaml/fabric/backup"
IMPACT="/home/d83071/OUTPUT/IMPACT/"
TMP="/home/d83071/TMP/FABRIC/"
CFG="/home/d83071/TMP/FABRIC/CFG"
CONFIG="/home/d83071/CONF/"

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
	
	
class fabric(object):
	def __init__(self,fabricName,renew=False,verbose=False):
		self.ymlFabric=YML_PATH_FABRIC+'/'+fabricName+'.yml'
		self.name=fabricName
		self.attributeToSave=['name','typeFabric','syncHost','hostnames','leaves','aleaves','bleaves','brand','spines','vlans','vpcs','ifs','mlag','routerId','bgpAs']
		self.verbose=verbose
		self.renew=renew
		self.hostnamesTmp=[]
		if os.path.isfile(self.ymlFabric):
			self.load()
		else:
			self.resync()
			renew=False
		if renew:
			self.resync()

	def save(self):
		saveFile(self.ymlFabric,BCK_YML_PATH_FABRIC)
		
		ctnFabric={}
		
		for attr in self.__dir__():
			if attr in self.attributeToSave:
				valueToSave=getattr(self,attr)
				ctnFabric[attr]=valueToSave
					
				
		print(f'Saving Data for {self.name}:{self.ymlFabric}... ')
		with open(self.ymlFabric,'w') as yml_w:
			yaml.dump(ctnFabric,yml_w ,default_flow_style=False)

	def load(self):
		dataYml={}
		with open(self.ymlFabric, 'r') as yml__:
			dataYaml=yaml.load(yml__,Loader__)
			
		for attr,value in dataYaml.items():
			setattr(self,attr,value)
						
		
	def resync(self):
		self.hostnamesTmp=getHostsFromEnv(self.name)
		self.syncHost=self.hostnamesTmp[0]
		versionSyncHost=self.getVersion([self.syncHost])
		versionCur= versionSyncHost[self.syncHost]
		nameCur=self.syncHost
		self.brand='UNKNOWN'
		if 'cisco' in versionCur:
			self.brand='CISCO'
		elif 'Arista' in versionCur :
			self.brand='ARISTA'
			
		self.typeFabric=self.getTypeFabric()


		if self.brand=='CISCO':
			if self.typeFabric=='FABRICPATH':
				self.hostnames=self.getFPNeighbor([self.syncHost])[self.syncHost]
			elif self.typeFabric=='VXLAN':
				spinesCur=[ host for host in self.hostnamesTmp if re.search('SP[0-9][0-9]',host) ]
				self.hostnames=self.getNeighbor(spinesCur )
			else:
				self.hostnames=self.hostnamesTmp
		else:
			self.hostnames=self.hostnamesTmp
		self.initSwitchType()
		self.initData()
		self.save()
		

	def initData(self):
		if self.typeFabric=='VXLAN':
			self.initDataVxlan()
		elif self.typeFabric=='FABRICPATH':
			self.initDataFP()
	
	def initDataFP(self):
		dataList=[ {"hostname":hostname , 'action': 'RUN' , "directory":TMP} for hostname in self.hostnames ]
		configsRaw=runListData(dataList,verbose=False,timeout=200,parser=None)
		
		parseVPCDomainID=lambda y: str((y|grep('^vpc domain').tolist())[0].split()[-1])
		parseVPCFPSwitchID=lambda y: str((y|grep('\s+fabricpath switch-id').tolist())[0].split()[-1])
		
		
		self.configs={ host__: result['sh run']  for host__,result in configsRaw.items()}
		self.vlans={ hostname:ParseVlanRun(output) for hostname,output in self.configs.items() }
		self.vpcs={ hostname: { "VpcId":parseVPCDomainID(output), "FPSwitchID": parseVPCFPSwitchID(output) } for hostname,output in self.configs.items() if hostname in self.leaves }
		self.ifs={ hostname:[ ifCur[0].asDict() for ifCur in ifEntries.ParseCiscoInterface(output) ] for hostname,output in self.configs.items()  if hostname in self.hostnames}
	
	def initDataVxlan(self):
		dataList=[ {"hostname":hostname , 'action': 'RUN' , "directory":TMP} for hostname in self.hostnames ]
		configsRaw=runListData(dataList,verbose=False,timeout=200,parser=None)		
		self.configs={ host__: result['sh run']  for host__,result in configsRaw.items()}
		self.vlans={ hostname:ParseVlanRun(output) for hostname,output in self.configs.items() }
		self.configFileObj={ hostname : config_cisco(None,data=self.configs[hostname]) for hostname in self.configs }

		parseBgpAs=lambda y: str((y|grep('^router bgp').tolist())[0].split()[-1])
		
		if self.brand=='CISCO':
			parseVPCDomainID=lambda y: str((y|grep('^vpc domain').tolist())[0].split()[-1])
			self.vpcs={ hostname: { "VpcId": parseVPCDomainID(output)  } for hostname,output in self.configs.items() if hostname in self.leaves }
			self.ifs={ hostname:[ ifCur[0].asDict() for ifCur in ifEntries.ParseCiscoInterface(output) ] for hostname,output in self.configs.items()  if hostname in self.hostnames }
			self.routerId= { hostname: str((self.configFileObj[hostname].extract('^interface loopback0$')|grep('address').tolist())[0].split()[-1].split('/')[0]) for hostname in self.configFileObj }
			self.bgpAs={hostname: parseBgpAs(output) for hostname,output in self.configs.items() }
		elif self.brand=='ARISTA':
			self.mlag={ hostname: str((self.configFileObj[hostname].extract('^mlag')|grep('domain-id').tolist())[0].split()[-1].split('/')[0])  for hostname in self.configFileObj  if hostname in self.leaves}
			self.routerId={ hostname: str((self.configFileObj[hostname].extract('^interface Loopback0$')|grep('address').tolist())[0].split()[-1].split('/')[0]) for hostname in self.configFileObj }
			self.bgpAs={hostname: parseBgpAs(output) for hostname,output in self.configs.items() }
		
		
	def initSwitchType(self):
	
		if self.typeFabric=='VXLAN':
			self.spines=[]
			self.leaves=[]
			self.aleaves=[]
			self.bleaves=[]
			
			for hostname in self.hostnames:
				if re.search('-SP[0-9][0-9]',hostname):
					self.spines.append(hostname)
				elif re.search('-AL[0-9][0-9]',hostname):
					self.aleaves.append(hostname)
					self.leaves.append(hostname)
				elif re.search('-BL[0-9][0-9]',hostname):
					self.bleaves.append(hostname)
					self.leaves.append(hostname)
				else:
					self.leaves.append(hostname)
					self.bleaves.append(hostname)
					self.aleaves.append(hostname)
		elif self.typeFabric=='FABRICPATH':
			self.spines=[]
			self.leaves=[]
			
			for hostname in self.hostnames:
				if hostname[0]=='R':
					self.spines.append(hostname)
				else:
					self.leaves.append(hostname)
	
					
	def getFPNeighbor(self,hostnames):
	
		timeout=30
		Neighs=None
		dataList=[ {"hostname":hostname , 'commande': 'sh fabricpath isis hostname' , "directory":TMP} for hostname in hostnames ]
		ParseLldpArista=lambda y: [ neigh['neighborDevice'].split('.')[0] for neigh in json.loads(y)['lldpNeighbors'] ]
		FPHostsRaw=runListData(dataList,verbose=False,timeout=40,parser=ParseFPHostnameStr)
		
		Neighs={ host__: [entry[1] for entry in entries]  for host__,entries in FPHostsRaw.items()}
		
		return Neighs
		
		
	def getTypeFabric(self):
		resultType='SPANNINGTREE'
		
		if self.brand=='ARISTA':
			resultType='VXLAN'
		elif self.brand=='CISCO':
			if re.search('-SP[0-9][0-9]', self.syncHost):
				resultType='VXLAN'
			else:
				testTypeRaw=runListData([{'hostname': self.syncHost,'commande':[ 'sh run | i "fabricpath|nve"']}],verbose=self.verbose,timeout=200,parser=None)
				testType=testTypeRaw[self.syncHost]['sh run | i "fabricpath|nve"']
				if 'fabricpath' in testType:
					resultType='FABRICPATH'
				elif 'nve' in testType:
					resultType='VXLAN'
		
		return resultType
		
	def getVersion(self,hostnames):
		
		timeout=30
		dataList=[ {"hostname":host__ , 'commande':['sh version'] , "directory":TMP} for host__ in hostnames ]
		versionsRaw=runListData(dataList,verbose=False,timeout=100,parser=None)
		
		versions={ hostname:value['sh version'] for hostname,value in versionsRaw.items() }
		
		return versions

	def getNeighbor(self,hostnames):
	
		Neigh=[]
		if self.brand=='CISCO':
			Neigh=self.getCdpNeighbor(hostnames)
		elif self.brand=='ARISTA':
			Neigh=self.getLldpNeighbor(hostnames)
		else:
			print(f'unsupported function  getNeighbor for {self.brand}')
			
		return Neigh

	
	
	def getLldpNeighbor(self,hostnames):
		timeout=30
		Neighs=None
		dataList=[ {"hostname":host__ , 'commande': 'sh lldp neighbors | json' , "directory":TMP} for host__ in hostnames ]
		ParseLldpArista=lambda y: [ neigh['neighborDevice'].split('.')[0] for neigh in json.loads(y)['lldpNeighbors'] ] 
		lldpsRaw=runListData(dataList,verbose=False,timeout=100,parser=ParseLldpArista)
		
		nb_element=hostnames[0]
		infra=hostnames[0].split('-')[1]
		
		Neighs=[ neigh for neigh in lldpsRaw if re.search(infra,neigh.upper())]
		
		return Neighs
		
	def getCdpNeighbor(self,hostnames):	
		timeout=30
		Neigh=None
		dataList=[ {"hostname":host__ , 'action':'CDPDETAIL', "directory":TMP} for host__ in hostnames ]
		Cdps=runListData(dataList,verbose=False,timeout=100,parser=ParseCdpNeighborDetailString)
		
		
		
		hostnamesRaw=[]
		for host,CdpNeighs in Cdps.items():
			if host not in hostnamesRaw:
				hostnamesRaw.append(host)
			for interface in CdpNeighs:
				neighCur=CdpNeighs[interface]['Neighbor']
				if neighCur not in hostnamesRaw:
					hostnamesRaw.append(neighCur)			
				
		infra=self.name.split('-')[0]
		
		Neighs=[ neigh for neigh in hostnamesRaw if re.search(infra,neigh.upper())]
		
		return Neighs
		
	def getSyncHost(self):
		try:
			child=pexpect.spawn(f'ssh -l {login} {bastion}',timeout=20)
			if verbose:
				child.logfile = sys.stdout.buffer
			child.expect(['[Pp]assword:'])
			child.sendline(f'{passwd}')
			child.expect('>')
			
		except:
			print('ERROR')
			pass
			
		return child
		

	def checkHosts(self,defaultYml=YAML_ENV):
	
		if not self.hostnamesTmp:
			self.hostnamesTmp=getHostsFromEnv(self.name)
		
		test=diffList(self.hostnames,self.hostnamesTmp)
		
		pdb.set_trace()
		
		if test['equals']:
			print(f'Fabric data hosts is sync with default yml data {defaultYml}')
		
		else:
			print(f'Fabric data hosts is not sync with default yml data {defaultYml}')
			if test['missing in list 2']:
				print('The following hosts should be suppressed to default yaml: {defaultYml}')
				ppr(test['missing in list 2'])
			if test['missing in list 1']:
				print('The following hosts should  be added to default yaml: {defaultYml}')
				ppr(test['missing in list 1'])
				
	def getImpact(self,directory=IMPACT):
		dataList=[]
		if self.typeFabric=='FABRICPATH':
			actions={'leaves':['MAC','SWITCHPORT','DESC','STATUS','PORTCHANNEL','VPC'] , 'spines':['MAC','GETALLARP','STATUS','SWITCHPORT','PORTCHANNEL']}
			
			for typeCur in actions:
				for hostname in self.leaves:
					for actionCur in actions['leaves']:
						if actionCur in ['SWITCHPORT','DESC','STATUS','MAC']:
							timeoutCur=400
						elif actionCur in ['GETALLARP']:
							timeoutCur=300
						else:
							timeoutCur=40
					for actionCur in actions['spines']:
						if actionCur in ['SWITCHPORT','DESC','STATUS','MAC']:
							timeoutCur=400
						elif actionCur in ['GETALLARP']:
							timeoutCur=300
						else:
							timeoutCur=40
												
						dataList.append({'hostname':hostname,'action':actionCur,'directory':directory+'/'+actionCur,'timeout':timeoutCur})
						
		runListData(dataList,verbose=False,timeout=40,parser=None)
		
	def extractVlansInfo(self,vlans__):
		infoVlan={}
		for hostname in self.vlans:
			for vlan__ in self.vlans[hostname]:
				if vlan__ in ParseVlanListe.liste_vlans(vlans__).explode():
					if vlan__ in self.vlans[hostname]:
						if hostname not in infoVlan:
							infoVlan[hostname]={'l2':[]}
						infoVlan[hostname]['l2'].append(vlan__)
						
		
		for hostname in self.ifs:
			for interface in self.ifs[hostname]:
				interfaceCur=interface['interface'][0]
				if 'Vlan' in interfaceCur:
					vlanCur=interfaceCur.replace('Vlan','').replace('vlan','').strip()
					if vlanCur in ParseVlanListe.liste_vlans(vlans__).explode():
						if hostname not in infoVlan:
							infoVlan[hostname]={'l3':[]}
						else:
							if 'l3' not in infoVlan[hostname]:
								infoVlan[hostname]['l3']=[]
						infoVlan[hostname]['l3'].append(vlanCur)					
		
		return infoVlan
	
	def getTemplate(self,action):
		ACTION={
			'FABRICPATH': {
				'CISCO': {
					'suppress_vlan': "suppress_vlan.j2"
				}
			},
			'VXLAN': {
			
				'CISCO': {
					'suppress_vlan': 'suppress_l2l3vpn.j2',
					'add_l2l3vpn': 'add_l2l3vpn.j2'
					
				},
				'ARISTA': {
					'add_l2l3vpn': 'add_l2l3vpn-eos.j2'
				}
			}
		}
		return ACTION[self.typeFabric][self.brand][action]
		
	def genConfig(self,action,datas):
	
		config={}
		model=self.getTemplate(action)
		for hostname in self.leaves:
			dataCur={'hostname': hostname , 'type': self.getTypeLeaf(hostname) , 'routerid': self.routerId[hostname] , 'bgpas': self.bgpAs[hostname] }
			dataCur.update(datas)
			cfgObj=equipmentConfig('fabric',dataCur,model)
			config[hostname]=cfgObj.getConfig()
		
		return config
			
	def getTypeLeaf(self,hostname):
		if hostname in self.bleaves:
			return 'BORDER'
		if hostname in self.aleaves:
			return 'ACCESS'
		if hostname in self.spines:
			return 'SPINE'
		
def getListFromFile(filename):
	with open(filename,'r') as file_r:
		listStr=file_r.read().split()
	return listStr

	
def diffList(list1,list2):
	missingL1=[]
	missingL2=[]
	
	for element in list1:
		if element not in list2:
			missingL1.append(element)

	for element in list2:
		if element not in list1:
			missingL2.append(element)

	if not missingL1 and not missingL2:
		return { 'equals': True }
	else:
		return { 'equals': False , 'missing in list 1': missingL1 , 'missing in list 2': missingL2}

	
def initYamlConfig(params,model,tag,directory=CFG):
	
	DictData={}
	
	configs={}
	for hostname in params:
		dataCur={'hostname':hostname  }
		dataCur=  { key:value for key,value in params[hostname].items() } 
		if dataCur:
			dataCur.update({'hostname':hostname})
		else:
			continue
		cfgObj=equipmentConfig('fabric',dataCur,model)
		configCur=cfgObj.getConfig().split('\n')
		DictData[hostname]={'configuration':configCur,'directory':directory}
		configs[hostname]=cfgObj.getConfig()
	
	saveResult(DictData,tag)
	writeCfg(configs,tag)

def saveResult(result,saveName,directory=YML_PATH_FABRIC_CFG):
	suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
	filename=directory+'/'+saveName+suffix
	with open(filename,'w') as yml_w:
		yaml.dump(result,yml_w ,default_flow_style=False)

def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
		
def writeCfg(configs,tag,directory='FABRIC'):
	dirCur=CONFIG+'/'+ directory +'/'+tag.upper()
	if not os.path.exists(dirCur):
		os.makedirs(dirCur)
		
	for leaf in configs:
		writeConfig(configs[leaf],dirCur+'/'+leaf.upper()+'.CFG')
			
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	groupConfig=parser.add_mutually_exclusive_group(required=False)
	
	parser.add_argument("-f","--fabric",action="store",help="Fabric Name ",required=True)
	parser.add_argument("-v","--verbose" ,action="store_true",default=False,help="mode verbose ",required=False)
	parser.add_argument("-r","--renew",action="store_true",default=False ,help="resync fabric data ",required=False)
	parser.add_argument("--vlans",dest='vlans', action="store",help="Extract info for vlan list",required=False)
	groupConfig.add_argument("--suppress", action="store",help="Suppress configuration yaml tag",required=False)
	groupConfig.add_argument("--add", action="store",help="Add configuration yaml tag",required=False)
	parser.add_argument("--import-data",dest='xlsxdata',action="store",default=False ,help="excel file data for configuration ",required=False)
	parser.add_argument("--check-host",dest='checkhost',action="store_true",default=False ,help="compare host list with defaut yaml hosts ",required=False)
	parser.add_argument("--get-impact",dest='getimpact',action="store_true",default=False ,help="get all output to study impact ",required=False)
	args = parser.parse_args()

	if  ( args.suppress or args.add )  and not (args.vlans or args.xlsxdata) :
		raise argparse.ArgumentError(None,'--vlans  is manadatory with --add or --suppress ')	
	
	A=fabric(args.fabric,renew=args.renew,verbose=args.verbose)

	if args.checkhost:
		A.checkHosts()


	if args.getimpact:
		A.getImpact()	
		
	if args.vlans:
		infoVlan=A.extractVlansInfo(args.vlans)
		ppr(infoVlan)
		
		if args.suppress:
			initYamlConfig(infoVlan,A.getTemplate('suppress_vlan'),args.suppress)
			
	if args.xlsxdata:
		infoData=xlsContainer(args.xlsxdata).datas
		
		
		if args.add:
			configs=A.genConfig('add_l2l3vpn',infoData)
			writeCfg(configs,args.add)
			