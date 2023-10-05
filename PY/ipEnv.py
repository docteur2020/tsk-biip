#!/usr/bin/env python3.8
# coding: utf-8

import pyparsing as pp
import sys
import os
import argparse
import glob
import pdb
import pickle
import urllib3
import requests
import json
urllib3.disable_warnings()
import re
from io import StringIO
from ipcalc import Network , IP
from time import gmtime, strftime , localtime
from ParsingShow import ParseBigIPInterface , ParsePaloAltoXmlInterface , ParseCkpInterface , getEquipementFromFilename
from section import config_cisco
import xmltodict
from pprint import pprint as ppr

#import warnings
#warnings.filterwarnings("ignore", category=SyntaxWarning)
#
#import aci.Fabric
#from envAci import getAllFabric
#from acitoolkit.acitoolkit import Session
#from acitoolkit.aciphysobject import Node
#from acitoolkit.acitoolkit import *

from getHosts import *
from getsec import *
import cache as cc

PATH_IP_DUMP="/home/b11945/IP/DUMP/"
DIR_YAML_SAVE="/home/b11945/yaml/IF/"

import yaml

def saveData(data,yaml_tag,sub_dir=''):
	suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
	if sub_dir:
		filename=DIR_YAML_SAVE+'/'+sub_dir+'/'+yaml_tag+suffix
	else:
		filename=DIR_YAML_SAVE+'/'+yaml_tag+suffix
	with open(filename,'w') as yml_w:
		print(f"Saving file:{filename}")
		yaml.dump(data,yml_w ,default_flow_style=False)


def loadData(yaml_file):
	data__=None
	with open(yaml_file) as io_yml:
		data__=yaml.load(io_yml,Loader=yaml.SafeLoader)
	return data__
	
def get_last_dump(path__):
	try:
		lastDump=max(glob.glob(path__+'/*'),key=os.path.getctime)
		#print("dump:",lastDump)
	except ValueError as E:
		return
	return lastDump

class interface(object):
	def __init__(self,interface="Null",ip="0.0.0.0/0",vrf="N/A",description="N/A",nhrp=None,dict_int={}):
	
		if dict_int:
			self.nom=dict_int['interface'][0]
			try:
				self.ip=dict_int['ip']
			except KeyError as e:
				raise(e)
			try:
				self.vrf=dict_int['vrf'][0]
			except KeyError:
				self.vrf="GRT"
			try:
				self.description=dict_int['description']
			except KeyError:
				self.description="None"
				
			try:
				self.nhrp=dict_int['hsrp']
			except KeyError:
				self.nhrp="None"
				
		else:
			self.nom=interface
			self.ip=ip
			self.vrf=vrf
			self.description=description
			self.nhrp=nhrp
		
	def __str__(self):
		resultat=resultat=StringIO()
		resultat.write('interface:'+self.nom+' vrf:'+str(self.vrf)+' ip:'+str(self.ip)+' description:'+str(self.description)+'\n')
		resultat_str=resultat.getvalue()
		
		return resultat_str
		
		
	def __repr__(self):
		resultat=resultat=StringIO()
		try:
			resultat.write('interface:'+self.nom+' vrf:'+str(self.vrf)+' ip:'+str(self.ip)+' description:'+str(self.description))
		except TypeError as e:
			pdb.set_trace()
			print(e)
		resultat_str=resultat.getvalue()
		
		return resultat_str
		
	def getIP(self):
		return self.ip
		
	def getCNAME(self,hostname):
		try:
			if self.vrf:
				resultat=".".join([hostname,self.nom,self.vrf])
			else:
				resultat=".".join([hostname,self.nom,"GRT"])
		except TypeError as e:
			pdb.set_trace()
			print(e)
		return resultat
		
	def isNhrpPresent(self):
		resultat=False
		if self.nhrp!="None":
			resultat=True
			
		return resultat
		
		
		
class ifEntries(object):
	def __init__(self,repertoire='RUN', yamlfile='',dump=''):
		if dump:
			self.load(dump)
		elif yamlfile:
			self.interfaces=self.extract_interface_from_yaml(yaml)
			self.cnames=self.init_cnames()

				
		else:
			self.repertoire=repertoire
			self.interfaces=self.extract_interface()
			#self.get_fw_ip_vip()
			#self.get_aci_ip()
			self.cnames=self.init_cnames()
			
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
		
		try:
			self.interfaces=dc.interfaces
			self.cnames=dc.cnames

		except:
			print('ERROR LOAD IP/INTERFACE DUMP:'+filename)
	
	@staticmethod	
	def ParsePaloAltoHostname(strorfile,modestr=False):
		
		if not modestr:
			with open(StringOrFile) as file:
				xmlStr__=file.read()
				
		else:
			xmlStr__=StringOrFile
				
		configDict=xmltodict.parse(xmlStr__)
		
		hostname=configDict['config']['devices']['entry']['deviceconfig']['system']['hostname']
	
		return hostname
	
	@staticmethod	
	def ParseCiscoInterface(str__):
	
		ciscoConfigFileObj=config_cisco(None,data=str__)
		strFiltered=ciscoConfigFileObj.extract('ip address [0-9]|ip address virtual|ipv4 address')
		result=None
		Space=pp.OneOrMore(pp.White(ws=' '))
		Slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		LigneNonParagraphe=pp.LineStart()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		Mask=pp.Combine(octet + ('.'+octet)*3)
		head_interface=(pp.LineStart()+pp.Keyword('interface').suppress()+Space.suppress()+pp.Word(pp.alphanums+'/.-')+pp.LineEnd().suppress()).setResultsName('interface')
		Vrf=((Space+(pp.MatchFirst([pp.Literal('ip vrf forwarding'),pp.Literal('vrf forwarding'),pp.Literal('vrf member'),pp.Literal('vrf')])+Space)).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*+')+pp.LineEnd().suppress()).setResultsName('vrf')
		Address=((Space+ (pp.Literal('ip address')|pp.Literal('ipv4 address'))).suppress()+(pp.Combine(ipAddress+Space+Mask)|pp.Combine(ipAddress+pp.Literal('/').setParseAction(pp.replaceWith(' '))+Slash))+pp.LineEnd().suppress()).setResultsName('ip')
		AddressSecondary=((Space+ (pp.Literal('ip address')|pp.Literal('ipv4 address'))).suppress()+(pp.Combine(ipAddress+Space+Mask)|pp.Combine(ipAddress+pp.Literal('/').setParseAction(pp.replaceWith(' '))+Slash))+pp.Suppress(pp.Literal('secondary'))+pp.LineEnd().suppress()).setResultsName('ip secondary')
		HsrpIOS=(Space+ pp.Literal('standby')+pp.Optional(pp.Word(pp.nums))+pp.Literal('ip')).suppress()+(pp.Combine(ipAddress))+pp.LineEnd().suppress()
		HsrpNexus=(Space+pp.Literal('hsrp')+pp.Word(pp.nums)).suppress()+pp.SkipTo(pp.Literal('ip')+ipAddress,failOn=LigneNonParagraphe).suppress()+pp.Literal('ip').suppress()+ipAddress+pp.LineEnd().suppress()
		VrrpNexus=(Space+pp.Literal('vrrp')+pp.Word(pp.nums)).suppress()+pp.SkipTo(pp.Literal('address')+ipAddress,failOn=LigneNonParagraphe).suppress()+pp.Literal('address').suppress()+ipAddress+pp.LineEnd().suppress()
		AnycastGW=(pp.Suppress(Space)+pp.Literal('fabric forwarding mode anycast-gateway').setParseAction(pp.replaceWith('on'))+pp.LineEnd().suppress()).setResultsName('anycast-gateway')
		virtualGW=(pp.Suppress(Space)+pp.Literal('ip address virtual ').setParseAction(pp.replaceWith('on') )).setResultsName('anycast-gateway')+(pp.Combine(ipAddress+pp.Literal('/').setParseAction(pp.replaceWith(' '))+Slash)+pp.LineEnd().suppress()).setResultsName('ip')
		Hsrp=(HsrpIOS|HsrpNexus|VrrpNexus).setResultsName('hsrp')
		OtherLine=pp.Combine((pp.LineStart()+Space+pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space))+pp.LineEnd())).suppress()
		SectionInterface=head_interface+pp.Optional(pp.SkipTo(Vrf,failOn=LigneNonParagraphe).suppress()+Vrf)+pp.Optional(pp.SkipTo(Address,failOn=LigneNonParagraphe).suppress()+Address)+pp.Optional(pp.SkipTo(AddressSecondary,failOn=LigneNonParagraphe).suppress()+AddressSecondary)+pp.Optional(pp.SkipTo(virtualGW,failOn=LigneNonParagraphe).suppress()+virtualGW)+pp.Optional(pp.SkipTo(Hsrp,failOn=LigneNonParagraphe).suppress()+Hsrp)+pp.Optional(pp.MatchFirst([AnycastGW,pp.SkipTo(AnycastGW,failOn=LigneNonParagraphe).suppress()+AnycastGW]))+pp.ZeroOrMore(OtherLine)
		result=SectionInterface.scanString(strFiltered)
		
		return result
		
	@staticmethod	
	def ParseFortigateInterface(str__):
	
		result=None
		Space=pp.OneOrMore(pp.White(ws=' '))
		Slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		LigneNonParagraphe=pp.LineStart()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		Mask=pp.Combine(octet + ('.'+octet)*3)
		BlocIP6Prefix=pp.Literal('config ip6-prefix-list')+pp.SkipTo(pp.Literal('end'))
		BlocIPv6=pp.MatchFirst([pp.Literal('config ipv6')+pp.SkipTo(BlocIP6Prefix)+BlocIP6Prefix+pp.Literal('end'),pp.Literal('config ipv6')+pp.SkipTo(pp.Literal('end'))+pp.Literal('end')])
		head_interface=(pp.LineStart()+pp.Keyword('config system interface')).suppress()
		port=(pp.Literal('edit').suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*\".').setParseAction(lambda t : t[0].replace('\"',''))).setResultsName('interface')
		Vdom=(pp.Literal('set vdom').suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*\"').setParseAction(lambda t : t[0].replace('\"',''))).setResultsName('vrf')
		Address=(pp.Literal('set ip').suppress()+pp.Combine(ipAddress+Space+Mask)).setResultsName('ip')
		end_interface=pp.Suppress(pp.SkipTo(pp.Literal('next'))+pp.Literal('next'))
		BlocInterface=pp.Group(port+pp.Optional(Vdom,default="None")+pp.Optional(Address,default="None")+end_interface)
		SectionConfigInterface=head_interface+pp.Group(pp.OneOrMore(BlocInterface))

		result=SectionConfigInterface.scanString(str__)

		return result
		
	@staticmethod		
	def ParseJuniperInterface(str__):
	
		result=None
		Space=pp.OneOrMore(pp.White(ws=' '))
		Slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		LigneNonParagraphe=pp.LineStart()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		Mask=pp.Combine(octet + ('.'+octet)*3)
		Address=pp.Literal('set interface').suppress()+pp.Group(pp.Word(pp.alphanums+'()/\,.-_[]{}<>')).setResultsName('interface')+pp.Literal('ip').suppress()+pp.Group(pp.Combine(ipAddress+pp.Literal('/').setParseAction(pp.replaceWith(' '))+Slash)).setResultsName('ip')
		result=Address.scanString(str__)
		
		

		return result
	
	@staticmethod		
	def ParseF5Interface(strorfile,mode=False):
		result=ParseBigIPInterface(strorfile,modestr=mode)
		
		return result
		
	@staticmethod		
	def ParseCheckpointInterface(strorfile,mode=False):
		result=ParseCkpInterface(strorfile,modestr=mode)
		
		interface=[]
	
		for vs__ in result:
			for if__ in result[vs__]:
				if if__[1]:
					interface.append({'interface': [if__[0] ] , 'ip': [if__[1]] , 'vrf': [vs__]})
	
		return interface
		
	@staticmethod
	def ParsePaloAltoXml(strOrFile,modestr=False):

		if not modestr:
			with open(strOrFile) as file:
				xmlStr__=file.read()
				
		else:
			xmlStr__=strOrFile
				
		configDict=xmltodict.parse(xmlStr__)
		
		hostname=configDict['config']['devices']['entry']['deviceconfig']['system']['hostname']
		
		ifs=[]
		
		if 'network'  not in configDict['config']['devices']['entry']:
			ifs.append( {'interface':'management' , 'ip': [ configDict['config']['devices']['entry']['deviceconfig']['system']['ip-address']+'/'+configDict['config']['devices']['entry']['deviceconfig']['system']['netmask'] ] ,'description':'management' ,'vrf':['GRT'] }  )
		
		if 'network' in configDict['config']['devices']['entry']:
			for typeIfs in configDict['config']['devices']['entry']['network']['interface']:
				typeIfsCur=configDict['config']['devices']['entry']['network']['interface'][typeIfs]
				if 'entry' in typeIfsCur:
					if isinstance(typeIfsCur['entry'],list):
						for entry in typeIfsCur['entry']:
							if 'layer3' in entry:
								try:
									dataCur=entry['layer3']['units']['entry']
								except KeyError as E:
									continue
									print(E)
								except TypeError as E:
									if not entry['layer3']['units']:
										continue
									pdb.set_trace()
									print(E)
								if isinstance(dataCur,list):
									for if__ in entry['layer3']['units']['entry']:
										try:
											if 'comment' in if__:
												description=if__['comment']
											else:
												description=None
											
											ifs.append({'interface':[ if__['@name'] ] , 'ip': [" ".join(if__['ip']['entry']['@name'].split('/'))] ,'description':[ description] ,'vrf':['GRT']})
										except TypeError as E:
											print(f'{strOrFile} not parsed')
											print(E)
								else:
									if__=entry['layer3']['units']['entry']
									if 'comment' in if__:
										description=if__['comment']
									else:
										description=None
									ifs.append({'interface':[ if__['@name'] ] , 'ip': [" ".join(if__['ip']['entry']['@name'].split('/'))] ,'description':[ description] ,'vrf':['GRT']})
					else:
						for if__ in  typeIfsCur['entry']['layer3']['units']['entry']:
							try:
								if 'comment' in if__:
									description=if__['comment']
								else:
									description=None
								
								ifs.append({'interface':[ if__['@name'] ] , 'ip': [" ".join(if__['ip']['entry']['@name'].split('/'))] ,'description':[ description] ,'vrf':['GRT']})
							except TypeError as E:
								print(f'{strOrFile} not parsed')
								print(E)

		return {'hostname': hostname ,'ifs': ifs}

	def extract_interface(self):

		result={}
		
		Type=None

		
		liste_file= glob.glob(self.repertoire+'/*')
		nombre_total_fichier=len(liste_file)
		file_counter=0
		for file__ in liste_file:
			file_counter+=1
			print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
			with open(file__,'r') as fich__:
					file_str=fich__.read()
			try:
				Space=pp.OneOrMore(pp.White(ws=' '))
				Hostname=pp.LineStart()+(pp.Keyword('hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.LineEnd().suppress()
				hostname_cur=next(Hostname.scanString(file_str))[0][0]
				Type="CISCO"
			except StopIteration:
				print('Fichier Non Cisco:'+file__)
				hostname_cur="N/A"
				Type="UNKNOWN"
				try:
					Space=pp.OneOrMore(pp.White(ws=' '))
					Hostname=(Space+pp.Keyword('set hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*"').setParseAction(lambda t : t[0].replace('\"',''))+pp.LineEnd().suppress()
					hostname_cur=next(Hostname.scanString(file_str))[0][0]
					Type="FORTIGATE"
				except StopIteration:
					print('Fichier Non Fortigate:'+file__)
					Type="UNKNOWN"
					hostname_cur="N/A"
					try:
						Hostname=(pp.Keyword('set hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*"').setParseAction(lambda t : t[0].replace('\"',''))+pp.LineEnd().suppress()
						hostname_cur=next(Hostname.scanString(file_str))[0][0]
						Type="JUNIPER"
					except StopIteration:
						print('Fichier Non Juniper:'+file__)
						Type="UNKNOWN"
						hostname_cur="N/A"
					
			temp_list_interfaces=[]
			
			if Type=="CISCO":
				for parsingInterface in self.ParseCiscoInterface(file_str):
					temp_list_interfaces.append(parsingInterface[0].asDict())
				#print(hostname_cur)
				#print(str(temp_list_interfaces))
				list_int_cur=[]
				for dict_in in temp_list_interfaces:
					try:
						list_int_cur.append(interface(dict_int=dict_in))
					except KeyError:
						pass
				result[hostname_cur]=list_int_cur
			elif  Type=="FORTIGATE":
				try:
					parsingInterface=self.ParseFortigateInterface(file_str)
					parsingElement=next(parsingInterface)
					temp_list_interfaces=[ element.asDict() for element in  parsingElement[0][0] ]
					#print(hostname_cur)
					#print(str(temp_list_interfaces))
					list_int_cur=[]
					for dict_in in temp_list_interfaces:
						try:
							if dict_in['ip']!='None':
								list_int_cur.append(interface(dict_int=dict_in))
								
						except KeyError:
							pass
					result[hostname_cur]=list_int_cur
				except StopIteration:
						print('Fichier FORTIGATE ECHEC:'+file__)
						Type="UNKNOWN"
						hostname_cur="N/A"
			elif Type=="JUNIPER":
				for parsingInterface in self.ParseJuniperInterface(file_str):
					temp_list_interfaces.append(parsingInterface[0].asDict())
				#print(hostname_cur)
				#print(str(temp_list_interfaces))
				list_int_cur=[]
				for dict_in in temp_list_interfaces:
					try:
						list_int_cur.append(interface(dict_int=dict_in))
					except KeyError:
						pass
				result[hostname_cur]=list_int_cur
			else:
				print('Equipement non gere:'+file__)
				continue
			
		return result
		
	def extract_interface_from_yaml(self,fileyaml):

		result={}
		
		Type=None
		
		parsingIfInfo=loadData(args.yaml)

		for type__ in parsingIfInfo:
			
			if parsingIfInfo[type__]['type']=='directory':
				liste_file= glob.glob(parsingIfInfo[type__]['path']+'*.'+parsingIfInfo[type__]['extension'])
				nombre_total_fichier=len(liste_file)
				file_counter=0
				print(f"Traitement type {type__}")
				if type__=='cisco':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						with open(file__,'r') as fich__:
								file_str=fich__.read()
						try:
							Space=pp.OneOrMore(pp.White(ws=' '))
							Hostname=pp.LineStart()+((pp.Keyword('hostname')|pp.Keyword('switchname'))+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.LineEnd().suppress()
							hostname_cur=next(Hostname.scanString(file_str))[0][0]
							Type="CISCO"
						except StopIteration:
							print('Fichier Non Cisco:'+file__)
							hostname_cur="N/A"
							Type="UNKNOWN"
						temp_list_interfaces=[]
						for parsingInterface in self.ParseCiscoInterface(file_str):
							temp_list_interfaces.append(parsingInterface[0].asDict())
						#print(hostname_cur)
						#print(str(temp_list_interfaces))
						list_int_cur=[]
						for dict_in in temp_list_interfaces:
							try:
								list_int_cur.append(interface(dict_int=dict_in))
							except KeyError:
								pass
						result[hostname_cur]=list_int_cur
						
				elif  type__=='fortinet':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						try:
							with open(file__,'r') as fich__:
								file_str=fich__.read()
						except UnicodeDecodeError as E:
							print(E)
							continue
						try:
							Space=pp.OneOrMore(pp.White(ws=' '))
							Hostname=(Space+pp.Keyword('set hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*"').setParseAction(lambda t : t[0].replace('\"',''))+pp.LineEnd().suppress()
							hostname_cur=next(Hostname.scanString(file_str))[0][0]
							Type="FORTIGATE"
						except StopIteration:
							print('Fichier Non Fortigate:'+file__)
							Type="UNKNOWN"
							hostname_cur="N/A"
							
						try:
							parsingInterface=self.ParseFortigateInterface(file_str)
							parsingElement=next(parsingInterface)
							temp_list_interfaces=[ element.asDict() for element in  parsingElement[0][0] ]
							#print(hostname_cur)
							#print(str(temp_list_interfaces))
							list_int_cur=[]
							for dict_in in temp_list_interfaces:
								try:
									if dict_in['ip']!='None':
										list_int_cur.append(interface(dict_int=dict_in))
										
								except KeyError:
									pass
							result[hostname_cur]=list_int_cur
							
						except StopIteration:
								print('Fichier FORTIGATE ECHEC:'+file__)
								Type="UNKNOWN"
								hostname_cur="N/A"
				elif  type__=='juniper':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						try:
							Hostname=(pp.Keyword('set hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*"').setParseAction(lambda t : t[0].replace('\"',''))+pp.LineEnd().suppress()
							hostname_cur=next(Hostname.scanString(file_str))[0][0]
							Type="JUNIPER"
						except StopIteration:
							print('Fichier Non Juniper:'+file__)
							Type="UNKNOWN"
							hostname_cur="N/A"
						temp_list_interfaces=[]
						for parsingInterface in self.ParseJuniperInterface(file_str):
							temp_list_interfaces.append(parsingInterface[0].asDict())
						#print(hostname_cur)
						#print(str(temp_list_interfaces))
						list_int_cur=[]
						
						for dict_in in temp_list_interfaces:
							try:
								list_int_cur.append(interface(dict_int=dict_in))
							except KeyError:
								pass
						result[hostname_cur]=list_int_cur
					else:
						print('Equipement non gere:'+file__)
						continue
				elif  type__=='f5':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						try:
							with open(file__,'r') as fich__:
								file_str=fich__.read()
						except UnicodeDecodeError as E:
							print(E)
							continue
						try:
							#Space=pp.OneOrMore(pp.White(ws=' '))
							#Hostname=(Space+pp.Keyword('hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>.*')+pp.LineEnd().suppress()
							#hostname_cur=next(Hostname.scanString(file_str))[0][0].split('.')[0]
							file_short=file__.split('/')[-1]
							hostname_cur=getEquipementFromFilename(file_short).upper()
							Type="F5"
						except StopIteration:
							print('Fichier Non F5:'+file__)
							hostname_cur="N/A"
							Type="UNKNOWN"
						temp_list_interfaces=self.ParseF5Interface(file__)
						
						list_int_cur=[]
						for dict_in in temp_list_interfaces:
							try:
								list_int_cur.append(interface(dict_int=dict_in))
							except KeyError:
								pass
						result[hostname_cur]=list_int_cur
				elif  type__=='paloalto':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						
						try:
							
							xmlResult=self.ParsePaloAltoXml(file__)
							type='PALOALTO'
							hostname_cur=xmlResult['hostname']
							temp_list_interfaces=xmlResult['ifs']
						except ValueError:
							pdb.set_trace()
							print('Fichier Non Palo Alto:'+file__)
							hostname_cur="N/A"
							Type="UNKNOWN"
							

						
						list_int_cur=[]
						for dict_in in temp_list_interfaces:
							try:
								list_int_cur.append(interface(dict_int=dict_in))
							except KeyError:
								pass
						result[hostname_cur]=list_int_cur
				elif  type__=='checkpoint':
					for file__ in liste_file:
						file_counter+=1
						print("Traitement du fichier:"+file__+"("+str(file_counter)+"/"+str(nombre_total_fichier)+")")
						try:
							with open(file__,'r') as fich__:
								file_str=fich__.read()
						except UnicodeDecodeError as E:
							print(E)
							continue
						try:
							file_short=file__.split('/')[-1]
							hostname_cur=getEquipementFromFilename(file_short).upper()
							
							Type="CHECKPOINT"
						except IndexError:
							print('Fichier Non Checkpoint:'+file__)
							hostname_cur="N/A"
							Type="UNKNOWN"
							
						temp_list_interfaces=self.ParseCheckpointInterface(file__)
						
						list_int_cur=[]
						for dict_in in temp_list_interfaces:
							try:
								list_int_cur.append(interface(dict_int=dict_in))
							except KeyError:
								pass
						result[hostname_cur]=list_int_cur						
			
		return result
		
	def get_fw_ip_vip(self):
	
		url_if = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/?fields=name,interface&device-types=firewall'
		url_vip = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/?fields=name,vip&device-types=firewall'
		os.environ['NO_PROXY'] = 'hcs-tooling.gts.socgen'
		r_if = requests.get(url_if, verify=False, headers={'X-API-KEY': '887104b073d57bd2c19dddb1755a0ddd5e371666'}, stream=True, proxies={})
		r_vip = requests.get(url_vip, verify=False, headers={'X-API-KEY': '887104b073d57bd2c19dddb1755a0ddd5e371666'}, stream=True, proxies={}) 

		if_unicorns = json.loads(r_if.text)
		vip_unicorns = json.loads(r_vip.text)
		
		try:
			for ifs in if_unicorns:
				try:
					for if__ in ifs['interface']:
						if if__['ip']!="0.0.0.0" and if__['ip']!="127.0.0.1":
							try:
								if if__['netmask']=="0.0.0.0":
									if__['netmask']="255.255.255.255"
								self.append_interface(ifs['name'],interface(interface=if__['name'],ip=[if__['ip']+" "+if__['netmask']],vrf=if__['vrf'],description=if__['description']))
							except KeyError as e:
								pdb.set_trace()
								print(e)
				except KeyError as e:
					pdb.set_trace()
					print(e)
					
		except KeyError as e:
			print(e)
        
		
		for vips in vip_unicorns:
			for vip__ in vips['vip']:
				try:
					self.append_interface(vips['name'],interface(interface=vip__['interface'],ip=[vip__['vip']],vrf='nhrp',description='nhrp',nhrp="nhrp_fw"))
				except KeyError as e:
					pdb.set_trace()
					print(e)
					
	#def get_aci_ip(self,mode="",caching=True):
	#	Fabrics_name=getAllFabric()
	#	
	#	TAG="ALL_ACI_IP_"
	#	CacheAciIP=cc.Cache(TAG)
	#	
	#	if CacheAciIP.isOK() and caching:
	#		Allipv4Aci=CacheAciIP.getValue()
	#	else:
	#	
	#		fabrics={}
	#		for fabric_name in getAllFabric():
	#			fabrics[fabric_name]=aci.Fabric.Fabric(name=fabric_name)
	#			
	#		Allipv4Aci={}
	#		for fabric_name in fabrics:
	#			Allipv4Aci[fabric_name]=fabrics[fabric_name].getIPv4Address()
	#			
	#		if caching:
	#			CacheAciIP.save(Allipv4Aci)
	#		
	#	if mode=="update":
	#		keyToDelete=[]
	#		for fabric_name in Allipv4Aci:
	#			for site in Allipv4Aci[fabric_name]:
	#				for ipv4 in Allipv4Aci[fabric_name][site]:
	#					name_cur='aci'+':'+fabric_name+':'+site+':'+ipv4['node'][0]
	#					if name_cur not in keyToDelete:
	#						keyToDelete.append(name_cur)
	#						
	#		for key in keyToDelete:
	#			if key in self.interfaces:
	#				del self.interfaces[key]
	#	
	#	for fabric_name in Allipv4Aci:
	#		for site in Allipv4Aci[fabric_name]:
	#			for ipv4 in Allipv4Aci[fabric_name][site]:
	#				[ip_cur,mask]=ipv4['ip'][0].split('/')
	#				self.append_interface('aci'+':'+fabric_name+':'+site+':'+ipv4['node'][0],interface(interface=ipv4['if'][0],ip=[ ip_cur+" "+mask ],vrf=ipv4['vrf'][0]))
	#				
	#	if mode=="update":
	#		self.cnames=self.init_cnames()
	#		
					
	def init_cnames(self):
		
		resultat={}
		for equipement__ in self.interfaces:
			for int__ in self.interfaces[equipement__]:
				try:
					ip_cur=int__.ip[0].split()[0]
				except IndexError as E:
					if not int__.ip:
						continue
					if not int__.ip[0]:
						continue
					pdb.set_trace()
					print(E)
				try:
					if ip_cur in resultat:
						resultat[int__.ip[0].split()[0]]+="|"+int__.getCNAME(equipement__)
					else:
						resultat[int__.ip[0].split()[0]]=int__.getCNAME(equipement__)
				except TypeError as e:
					pdb.set_trace()
					print(e)
				if int__.isNhrpPresent():
					if isinstance(int__.nhrp,list):
						for nhrp__ in int__.nhrp:
							resultat[nhrp__]=int__.getCNAME(equipement__)+".nhrp"
					else:
						resultat[int__.nhrp]=int__.getCNAME(equipement__)+".nhrp"
		
		return resultat
		
	def print_cnames(self):
		ppr(str(self.cnames))
		
	def print_if(self):
		print(str(self.interfaces))
		
	def append_interface(self,hostname__,interface__):
		
		if hostname__ in self.interfaces.keys():
			self.interfaces[hostname__].append(interface__)
		else:
			self.interfaces[hostname__]=[interface__]
			
		
	def searchIP(self,ip__):
		resultat=None
		try:
			resultat=self.cnames[ip__]
		except KeyError:
			pass
			
		return resultat
			
			
	def getConnected(self,ip__,minimum_subnet=16):
		resultat=[]
		

		ip_obj=IP(ip__)

		for equipement__ in self.interfaces:
			for int__ in self.interfaces[equipement__]:
				for ip__f in int__.ip:
					info_ip=ip__f.split()
					if len(info_ip)>=2:
						ip_addr_cur=info_ip[0]
						netmask_cur=info_ip[1]
						Res_cur=Network(ip_addr_cur+'/'+netmask_cur)
						if ip_obj in Res_cur and ip_obj.subnet() >=minimum_subnet:
							resultat.append([equipement__,int__])
		
		return resultat
		
	def getIPConnected(self,ip__,hostname=""):
		resultat=[]
		
		if not hostname:
			for equipement__ in self.interfaces:
				for int__ in self.interfaces[equipement__]:
					for ip__f in int__.ip:
						info_ip=ip__f.split()
						if len(info_ip)>=2:
							ip_addr_cur=info_ip[0]
							netmask_cur=info_ip[1]
							if ip_addr_cur == ip__:
								resultat.append([equipement__,int__])
			
		else:
			try:
				for int__ in self.interfaces[hostname]:
					for ip__f in int__.ip:
						info_ip=ip__f.split()
						if len(info_ip)>=2:
							ip_addr_cur=info_ip[0]
							netmask_cur=info_ip[1]
							if ip_addr_cur == ip__:
								resultat.append([hostname,int__])
			except KeyError as E:
				print(f'Equipement {hostname} inconnu')
				print(E)
				return []
		return resultat
		
	def getIfHostname(self,hostname__):
		resultat=None
		
		try:
			resultat=self.interfaces[hostname__]
		except KeyError:
			pass
			
		return resultat
		
	def getIfHostnameRe(self,regex__):
	
		resultat={}

		for equipement__ in self.interfaces:
			if re.search(regex__,equipement__, re.IGNORECASE):
				resultat[equipement__]=self.interfaces[equipement__]
		
		return resultat
		
	def searchHostname(self,regex__):
		resultat=[]

		for equipement__ in self.interfaces:
			if re.search(regex__,equipement__, re.IGNORECASE):
				resultat.append(equipement__)
		
		return resultat
		
	def getHostnameRe(self,regex__):
	
		resultat=[]

		for equipement__ in self.interfaces:
			if re.search(regex__,equipement__, re.IGNORECASE):
				resultat.append(equipement__)
		
		return resultat

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-r", "--repertoire",action="store",help="Répertoire contenant les output show run")
	group1.add_argument("-d", "--dumpfile",action="store",default=get_last_dump(PATH_IP_DUMP),help="Contient le fichier dump type interfaces")
	group1.add_argument("-y", "--yaml",action="store",help="yaml contenant tous les répertoires et parser")
	parser.add_argument("-s", "--save",action="store",help=u"Sauvegarde dans fichier dump",required=False)
	parser.add_argument("-i", "--ip",action="store",help=u"Recherche une IP",required=False)
	parser.add_argument("-p", "--printCname",action="store_true",help=u"Affichage des cnames",required=False)
	parser.add_argument("--tag",action="store",help=u"save result to yaml (tag)",required=False)
	parser.add_argument("-P", "--PrintIf",action="store_true",help=u"Affichage des interfaces",required=False)
	parser.add_argument("--exact",action="store_true",help=u"Avec option -i recherche les interfaces avec l'ip exacte",required=False)
	parser.add_argument("-e", "--extractif",action="store",help=u"Renvoie les interfaces contenant cette IP",required=False)
	parser.add_argument("--search",action="store",help=u"search by hostname \(regex\)",required=False)
	parser.add_argument("-E","--Equipment",action="store",help=u"Renvoie les interfaces contenant un(des) équipement(s)",required=False)
	parser.add_argument("--as-regex",dest='asregex',action="store_true",help=u"recherche en regex",required=False)
	parser.add_argument("-H",'--hostname',dest='hostname',action="store",help=u"recherche les equipements en regex",required=False)
	#parser.add_argument('--update-aci',dest='update_aci',action="store_true",help=u"recherche les equipements en regex",required=False)
	args = parser.parse_args()
	
	
	
	if args.repertoire:
		A=ifEntries(repertoire=args.repertoire)
		A.print_cnames()
		
	elif args.yaml:
		A=ifEntries(yamlfile=args.yaml)
		A.print_cnames()
			
		
	elif args.dumpfile:
		A=ifEntries(dump=args.dumpfile)
		if args.printCname:
			A.print_cnames()
		if args.PrintIf:
			A.print_if()
		
	
	#if args.update_aci:
	#	timestamp__=strftime("%Y%m%d_%Hh%Mm%Ss", localtime())
	#	filedump=PATH_IP_DUMP+timestamp__+'.dump'
	#	A.get_aci_ip(mode="update")
	#	A.save(filedump)
	
	if args.save:
		A.save(args.save)
		
	if args.ip:
		cname__=A.searchIP(args.ip)
		print("IP:"+args.ip+"=>"+cname__.__str__())
		
		if args.exact:
			resultat=A.getIPConnected(args.ip)
			ppr(resultat)
		
	if args.extractif:
		resultat=A.getConnected(args.extractif)
		print(resultat)
		
		if args.tag:
			saveData(resultat,args.tag)
		
		
	
	if args.Equipment:
		if args.asregex:
			print(A.getIfHostnameRe(args.Equipment))
		else:
			ppr(A.getIfHostname(args.Equipment))
			
	if args.hostname:
		print(A.getHostnameRe(args.hostname))
	
	if args.search:
		print(A.searchHostname(args.search))
		
