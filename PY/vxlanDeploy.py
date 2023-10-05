#!/usr/bin/env python3.8
# coding: utf-8

import jinja2
import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
from vxlanFabricConfig import equipmentConfig,writeConfig,TEMPLATE_DIR,CONFIG_DIR,CSV_DNS_DIR
import cache as cc
from ParsingShow import ParseCdpNeighborDetailString
from connexion import *
import yaml
import os
from textops import *
from section import config_cisco
from itertools import count

class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)
Loader__.add_constructor('!include', Loader__.include)

def parserSyncConfig(Str):
	
	ciscoConfigFileObj=config_cisco(None,data=Str)
	routerId=(ciscoConfigFileObj.extract('^interface loopback0$')|grep('address').tolist())[0].split()[-1].split('/')[0]
	filteredConfigRaw=ciscoConfigFileObj.extract('^vlan|vrf\ context|interface Vlan|interface nve1|evpn')
	filteredConfig_wo_Vlan=suppressVlan(filteredConfigRaw,['1','6'])
	filteredConfigRaw2=suppressBGPCommun(filteredConfig_wo_Vlan)
	filteredConfig=suppressOther(filteredConfigRaw2,['ip route 0.0.0.0','vrf context management','nv overlay evpn','^vlan 2$','^vlan 3$','^vlan 6$','NATIVE','TRASH','UNDERLAY-BACK2BACK','vlan dot1Q tag native'])
	
	return { 'loopback0':routerId , 'config': filteredConfig }

class leafEvpnConfig(equipmentConfig):
	def __init__(self,params):
		'''params:dict'''
		self.j2File='VXLAN/l2l3vpn.j2'
		super().__init__('VXLAN',params,self.j2File)


		
class vrfConfig(object):
	def __init__(self,name,vrfid):
		pass
class l2config(object):
	def __init__(self,name,vlanid):
		pass
class fabricInfo(object):
	def __init__(self,fileYaml,caching=False):
		'''params:dict'''
		with open(args.yaml, 'r') as yml__:
			self.params=yaml.load(yml__,Loader__)
		
		self.caching=caching
		self.configDir=CONFIG_DIR
		for key,item in self.params['fabric'].items():
			super().__setattr__(key,item)
		self.masterSpine=list(self.spines.keys())[0]
		self.tagConfigPrefix={'CDPDETAIL':'CDPDETAIL_','OTHER_CONFIG':'PART_CONFIG_VXLAN_DEPLOY_'}
		self.trackFirst=10
		self.trackIdIter=map(str,count(self.trackFirst))
		self.getLeaves()
		self.getConfig()
		
	def getLeaves(self):
		tagCur=self.tagConfigPrefix['CDPDETAIL']+self.masterSpine.upper()
		cacheCur=cc.Cache(tagCur)
		
		if self.caching:
			if cacheCur.isOK():
				print(f'info in cache for list leaves {self.masterSpine} is used')
				cdpNeighbors=cacheCur.getValue()
				allNeighbors=[ cdpNeighbors[interface]['Neighbor'] for  interface in cdpNeighbors if 'Eth' in interface ]
				self.listLeaves=list(filter( lambda t: True if not '-SP' in t else False  ,allNeighbors))
				return
				
		commande=f'show cdp neighbor detail'
		if self.caching:
			print(f'cache leaves list for {self.masterSpine}  is absent')		
		con_get_leaves=connexion(equipement(self.masterSpine),None,None,None,'SSH',"TMP/"+self.masterSpine.lower()+"_shcdpdetail.log","TMP",commande,timeout=300,verbose=False)
		cdpNeighbors=con_get_leaves.launch_withParser(ParseCdpNeighborDetailString)
		cacheCur.save(cdpNeighbors)
		allNeighbors=[ cdpNeighbors[interface]['Neighbor'] for  interface in cdpNeighbors if 'Eth' in interface ]
		self.listLeaves=list(filter( lambda t: True if not '-SP' in t else False  ,allNeighbors))
		
		return	
		
	@staticmethod
	def	getTypeEquipment(hostname):
		type='UNKNOWN'
		suffixe=hostname.split('-')[-1][:2]
		if suffixe=="AL":
			type="SERVER"
		elif suffixe=="BL":
			if 'BL01' in hostname or 'BL02' in hostname :
				type="BORDER"
			else:
				type="OTHER_BORDER"
		elif suffixe=="SP":
			type="SPINE"
		return type
		
	def getConfig(self):
		
		self.infos={}
		
		for leaf in self.listLeaves:
			TAG_OTHER_CONFIG_HOST=self.tagConfigPrefix['CDPDETAIL']+leaf.upper()
			cacheOtherConfig=cc.Cache(TAG_OTHER_CONFIG_HOST)
		
			if self.caching:
				if cacheOtherConfig.isOK():
					print(f'info in cache config vxlan for {leaf} is used')
					runningConfigLeaves=cacheOtherConfig.getValue()
					self.infos[leaf]=runningConfigLeaves
				else:
					print(f'cache config vxlan for {leaf} is absent')
					commande=f'show run'
					con_get_running=connexion(equipement(leaf),None,None,None,'SSH',"TMP/"+leaf.lower()+"_shrun.log","TMP",commande,timeout=300,verbose=False)
					runningConfigLeaves=con_get_running.launch_withParser(self.parserOtherConfig)
					cacheOtherConfig.save(runningConfigLeaves)
					self.infos[leaf]=runningConfigLeaves
			else:
				print(f'cache config vxlan for {leaf} is not used')
				commande=f'show run'
				con_get_running=connexion(equipement(leaf),None,None,None,'SSH',"TMP/"+leaf.lower()+"_shrun.log","TMP",commande,timeout=300,verbose=False)
				runningConfigLeaves=con_get_running.launch_withParser(self.parserOtherConfig)
				cacheOtherConfig.save(runningConfigLeaves)
				self.infos[leaf]=runningConfigLeaves
				
	@staticmethod
	def parserOtherConfig(Str):
	
		ciscoConfigFileObj=config_cisco(None,data=Str)
		routerId=(ciscoConfigFileObj.extract('^interface loopback0$')|grep('address').tolist())[0].split()[-1].split('/')[0]
		vlanl3vni=[ int(ligne.split()[-1]) for ligne in ciscoConfigFileObj.extract('vn-segment 30')|grep('vlan').tolist() if ligne.strip() ]

		if not vlanl3vni:
			vlanl3vni = [50]
		return { 'loopback0':routerId  , 'nextVlanl3vni': max(vlanl3vni)+1}	
	
	def initVlanl3vniIter(self):
		listVlan=[]
		self.vlanl3vniIter={}
		for hostname in self.infos:
			vlanl3vnicur=self.infos[hostname]['nextVlanl3vni']
			if vlanl3vnicur not in listVlan:
				listVlan.append(vlanl3vnicur)
		
		for hostname in self.infos:			
			self.vlanl3vniIter[hostname]=map(str,count(max(listVlan)))
			
	def initTrack(self):
		self.tracks=[]
		self.nhStatic={}
		

		for vrf in self.evpnParams['static']:
			for route in self.evpnParams['static'][vrf]:
				if 'hmm' not in route:
					continue
				if route['gateway'] not in self.nhStatic:
					idCur=next(self.trackIdIter) 
					self.tracks.append({'id':idCur , 'gateway':route['gateway'] , 'vrf': vrf})
					self.nhStatic[route['gateway']]=idCur
		
		return self.tracks
		
	def initRMConnected(self):
		self.rmConnected={}
		

		for vlan in self.evpnParams['borders']:
			vrfCur=vlan['vrf']
			if vrfCur not in self.rmConnected:
				self.rmConnected[vrfCur]=f'{vrfCur}-DIRECT-to-BGP'
				
		return self.rmConnected
		
		return self.tracks			
	def generateConfig(self,yamlCfg):
	
		self.initVlanl3vniIter()
		self.paramLeaves={}
		self.leavesConfigEpvn={}
		with open(yamlCfg, 'r') as yml__:
			self.evpnParams=yaml.load(yml__,Loader__)
			
		staticsCur=self.evpnParams['static']
		tracksCur=self.initTrack()
		rmConnectedCur=self.initRMConnected()
		for leaf in self.listLeaves:
			other_param={}
			other_param['hostname']=leaf
			other_param['as']=self.bgp['as']
			other_param['routerId']=self.infos[leaf]['loopback0']
			other_param['type']=self.getTypeEquipment(leaf)
			other_param['vrfs']=[]
			for vrf in  self.evpnParams['vrfs']:
				idCur=next(self.vlanl3vniIter[leaf])
				other_param['vrfs'].append({'name': vrf['name'] , 'vlan': idCur })
			other_param['vlans']= self.evpnParams['vlans']
			other_param['interconnections']= self.evpnParams['borders']
			other_param['static']= staticsCur
			other_param['tracks']= tracksCur
			other_param['trackByGw']=self.nhStatic
			other_param['rmConnected']=rmConnectedCur
			self.paramLeaves[leaf]=other_param
			self.leavesConfigEpvn[leaf]=leafEvpnConfig(self.paramLeaves[leaf])
			
	def writeCfg(self,tag):
		dirCur=self.configDir+'/VXLAN/'+tag.upper()
		if not os.path.exists(dirCur):
			os.makedirs(dirCur)
			
		for leaf in self.leavesConfigEpvn:
			writeConfig(self.leavesConfigEpvn[leaf].getConfig(),dirCur+'/'+leaf.upper()+'.CFG')

			
		
if __name__ == '__main__':
	"Fonction principale"
	
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-y","--yaml",action="store",help="yaml file that contains fabric Vxlan informations ",required=True)
	parser.add_argument("-c","--config",action="store",help="yaml file that configuration",required=True)
	parser.add_argument("--cache" ,action="store_true",help="enable caching",required=False)
	parser.add_argument("-t","--tag" ,action="store",help="tag ",required=False)
	args = parser.parse_args()
	
	fabricObj=fabricInfo(args.yaml,caching=args.cache)

	if args.config:
		fabricObj.generateConfig(args.config)
		
		if args.tag:
			fabricObj.writeCfg(args.tag)
			
