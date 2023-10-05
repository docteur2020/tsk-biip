#!/usr/bin/env python3.8
# coding: utf-8



import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
from connexion import *
from ipEnv import ifEntries
from getTdbInfo import PATH_TDB_DUMP , tdbContainer , get_last_dump
from runSec import runCmd,FW,containerFW,getAllIP
import re
import cache as cc
import dns.resolver
from dns.exception  import DNSException
import csv
from netaddr import IPAddress, IPNetwork
from time import gmtime, strftime , localtime ,ctime , sleep
from getsec import *
import pyparsing as pp

TAG_PREFIX_RUNIF='RUNIF_'
DNSs={'BNL':[] ,'FORTIS':['10.18.1.200'], 'BNP':['159.50.101.10','159.50.169.10']}
SHORT_IF={'ethernet':'eth', 'loopback':'lo','hundredgige':'hu'}
CSV_DNS_DIR="/home/d83071/CSV/INFOBLOX"
YAML_ENV="/home/d83071/yaml/DEFAULT_ENV.yml"
HOSTS='/home/d83071/yaml/hosts.yaml'
FWS='/home/d83071/yaml/firewalls.yaml'
TSK="/home/d83071/CONNEXION/pass.db"
secDb=secSbe(TSK)
HOST_SUF={'fban':'fbast','fbas':'fbast','fest':'fmarn','fnorm':'fmarn','rban':'rbast','rbas':'rbast','rest':'rmarn','rnorm':'rmarn'}


def extractFW(hostnames,tdb):
	fw=[]
	other=[]
	
		
	for hostname in hostnames:
		infoCur=tdb.getInfoEquipment(hostname.upper(),mode="normal")
		
		try:
			TypeCur=infoCur['Type']
		except KeyError as E:
			pdb.set_trace()
			'stop'
		
		if TypeCur=='FIREWALL':
			fw.append(hostname)
			
		else:
			other.append(hostname)
	
	result={'fw':fw, 'other':other}
	
	return result
	
def getInterfaceRunning(equipment__):

	ifRun=None
	
	commande=f'show run'
	con_get_run_cur=connexion(equipement(equipment__)     ,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log"            ,commande_en_ligne=commande,retry=5,timeout=20,verbose=False)
	ifRun=con_get_run_cur.launch_withParser(ifEntries.ParseCiscoInterface)
	
	result=[ ifs[0].asDict() for ifs in ifRun] 
	
	return result

def getInterfaceRunningFW(equipment__,branch):

	ifRun=None
	commandes={'CHECKPOINT': ['cphaprob state'] ,'PALOALTO': ['set cli pager off','show high state','set cli pager on'], 'FORTINET': [ 'show'] }
	
	if branch not in commandes:
		print(f'Branch not supported',file=sys.stderr)
		print(f'Supported Branches:',file=sys.stderr)
		ppr(list(comandes.keys()))
		sys.exit(1)
	commandeCur=commandes[branch]
	
	FwCtx=containerFW(FWS)
	curCon=runCmd(equipment__,commandeCur,output='ifs__',fwDb=FwCtx,modeCommand=True,secDb=secDb,verbose=False)
	curCon.start()
	#ifRun=con_get_run_cur.launch_withParser(ifEntries.ParseCiscoInterface)
	curCon.join()
	ppr(curCon.result)	
	#result=[ ifs[0].asDict() for ifs in ifRun] 
	
	resultStr=curCon.result[commandeCur[0]]
	ifRun=ifEntries.ParseFortigateInterface(resultStr)
	parsingInterface=ifRun
	parsingElement=next(parsingInterface)
	temp_list_interfaces=[ element.asDict() for element in  parsingElement[0][0] ]
	#print(hostname_cur)
	#print(str(temp_list_interfaces))
	list_int_cur=[]
	for dict_in in temp_list_interfaces:
		try:
			if dict_in['ip']!='None':
				list_int_cur.append(dict_in)
				
		except KeyError:
			pass
	result=list_int_cur
	
	return result


def getGenericName(hostname):
	
	result=hostname
	suffix_specs=['-dfi','-intra']
	
		
	for prefix in HOST_SUF:
		if re.search('^'+prefix+'[0-9]-',hostname):
			result=re.sub(prefix+'[0-9]',HOST_SUF[prefix],hostname)
			#result=hostname.replace(prefix,HOST_SUF[prefix])
			'stop'
			break
		if re.search('^'+prefix+'[0-9][0-9]-',hostname):
			result=re.sub(prefix+'[0-9][0-9]',HOST_SUF[prefix],hostname)
			#result=hostname.replace(prefix,HOST_SUF[prefix])
			'stop'
			break
	
	for suffix_spec in suffix_specs:
		if suffix_spec in hostname:
			result2=re.sub(suffix_spec+'[1-9]',suffix_spec,result)
			return result2
		
	#pdb.set_trace()
	return result
	
def getShortIf(port):
	result=port.lower()
	for name in SHORT_IF:
		result=result.replace(name,SHORT_IF[name])
	return result
	
def getAnycastSuffixOld(hostname):
	hostname__=hostname.upper()
	if re.search ('^RBA[NS]',hostname__):
		COUNTRY='BE'
	elif re.search ('^RNORM|^REST',hostname__):
		COUNTRY='FR'
	fabric="-".join(hostname__.split('-')[1:-1])
	return COUNTRY+'_'+fabric+'_'

def getGenericNameFromParse(r,l,t):
	
	hostname=t[0].lower()
	result=hostname
	suffix_specs=['-dfi','-intra']
		
		
	for prefix in HOST_SUF:
		if re.search('^'+prefix+'[0-9]-',hostname):
			result=re.sub(prefix+'[0-9]',HOST_SUF[prefix],hostname)
			#result=hostname.replace(prefix,HOST_SUF[prefix])
			'stop'
			break
		if re.search('^'+prefix+'[0-9][0-9]-',hostname):
			result=re.sub(prefix+'[0-9][0-9]',HOST_SUF[prefix],hostname)
			#result=hostname.replace(prefix,HOST_SUF[prefix])
			'stop'
			break
	
	for suffix_spec in suffix_specs:
		if suffix_spec in hostname:
			result2=re.sub(suffix_spec+'[1-9]',suffix_spec,result)
			return result2
		
	return result
	
def getAnycastSuffix(hostname):
	Separator=pp.Literal('-')
	Suffix1=pp.Combine(pp.CaselessLiteral('R')+pp.Word(pp.alphas,min=3,max=4)+pp.Word(pp.nums,min=1,max=2))
	Suffix2=pp.Combine(pp.CaselessLiteral('R')+pp.Word(pp.alphanums,min=3,max=4))
	Suffix=pp.MatchFirst([Suffix2,Suffix1])
	FabricNameOld=pp.Word(pp.alphas,min=3,max=8)+pp.Literal('-')+pp.Word(pp.alphas,exact=1)
	FabricNameNew=pp.Word(pp.alphas,min=3,max=8)

	Type=pp.Word('abAB')+pp.CaselessLiteral('L')+pp.Suppress(pp.Word(pp.nums)+(pp.CaselessLiteral('X')|pp.CaselessLiteral('Y')))
	TypeSmall=(pp.Word(pp.nums,exact=2)+(pp.CaselessLiteral('X')|pp.CaselessLiteral('Y'))).setParseAction(pp.replaceWith('xy'))
	SuffixLongOld=(pp.Combine(Suffix+Separator+FabricNameOld)).setParseAction(getGenericNameFromParse)
	SuffixLongNew=(pp.Combine(Suffix+Separator+FabricNameNew)).setParseAction(getGenericNameFromParse)
	genericNameOld=pp.Combine(SuffixLongOld+Separator+(Type|TypeSmall))
	genericNameNew=pp.Combine(SuffixLongNew+Separator+(Type|TypeSmall))
	
	genericName=pp.MatchFirst([genericNameOld,genericNameNew])

	
	resultat=genericName.parseString(hostname).asList()[0].lower()

	#print(resultat)

	return resultat
	
def getHsrpSuffix(hostname):
	hostname__=hostname.upper()
	if re.search ('^RBA[NS]',hostname__):
		PREFIX='RBAST'
	elif re.search ('^RNORM|^REST',hostname__):
		PREFIX='RMARN'
	pdb.set_trace()
	if hostname__[-1] in '123456789':
		SUFFIX=hostname__.split('-')[-1][:-1]
	else:
		SUFFIX=hostname__.split('-')[-1]
	
	return PREFIX+'-'+SUFFIX
	
def checkDefaultReverseDNS(IPCur,nameAlias):
	
	result=False
	
	result_list=[]
			

		
	testIPSuffixe=IPCur.replace('.','-')+'.'
	for answer in nameAlias:
		for alias in answer:
			if testIPSuffixe in alias.split()[-1] or IPCur in alias.split()[-1]:
				result_list.append(True)
			else:
				result_list.append(False)
	

	if False in result_list:
		result=False
	else:
		result=True
	
	
	return result
	
def checkReversePresence(nom,interfaces,env='BNP',domain='fr.net.intra',branch='CISCO',force=False):
	emptyIP={}
	badDNSEntry={}
	domain='.'+domain
	for interface in interfaces:
		if 'ip' in interface:
			for ip__ in interface['ip']:
				ipCur=ip__.split()[0]
				ifNameCur=getShortIf(interface['interface'][0])
				if ipCur=='55.0.39.256':
					pdb.set_trace()
					'stop'
				try:
					vrfCur=interface['vrf'][0].replace('+','-')
					reverseCur=getReverseDns(ipCur,DNSs[env])
					if 'anycast-gateway' in interface:
						if interface['anycast-gateway'][0]=='on':
							nameCur=getAnycastSuffix(nom)+'_'+ifNameCur.replace('/','-')+'_'+vrfCur+domain
					else:
						if vrfCur.lower() != 'grt':
							nameCur=nom.lower()+'_'+ifNameCur.replace('/','-').replace('.','-')+'_'+vrfCur.lower()+domain
						else:
							nameCur=nom.lower()+'_'+ifNameCur.replace('/','-').replace('.','-')+domain
				except KeyError as E:
					reverseCur=getReverseDns(ipCur,DNSs[env])
					nameCur=nom.lower()+'_'+ifNameCur.replace('/','-').replace('.','-')+domain
				
				if (not reverseCur or checkDefaultReverseDNS(ipCur,reverseCur)) or force:
					print(reverseCur)
					emptyIP[ipCur]={'possibleValue':nameCur}
					
					if branch=='FORTINET':
						pdb.set_trace()
						emptyIP[ipCur]={'possibleValue':getGenericName(nameCur)}
						
		if interface['interface'][0].lower()=='loopback1' and branch=='ARISTA':
			ipSecCur=interface['ip'][0].split()[0]
			nameCurSec=nom.lower()[0:-1]+'x_y_vip'+domain

			reverseCurSec=getReverseDns(ipCur,DNSs[env])
			if (not reverseCurSec or checkDefaultReverseDNS(ipSecCur,reverseCurSec) ) or force:
				print(reverseCurSec)
				emptyIP[ipSecCur]={'possibleValue':nameCurSec}

		if 'ip secondary' in interface:
			if interface['interface'][0].lower()!='loopback1':
				ipSecCur=interface['ip secondary'][0].split()[0]
				try:
					vrfCur=interface['vrf'][0].replace('+','-')
					reverseCurSec=getReverseDns(ipSecCur,DNSs[env])
					nameCurSec=nom.lower()+'_secondary_'+ifNameCur.replace('/','-').replace('.','-')+'_'+vrfCur.lower()+domain
				except KeyError as E:
					reverseCurSec=getReverseDns(ipCur,DNSs[env])
					nameCurSec=nom.lower()+'_secondary_'+ifNameCur.replace('/','-').replace('.','-')+domain
					
				
				if (not reverseCurSec or checkDefaultReverseDNS(ipSecCur,reverseCurSec)) or force:
					print(reverseCurSec)
					emptyIP[ipSecCur]={'possibleValue':nameCurSec}
			else:
				ipSecCur=interface['ip secondary'][0].split()[0]
				nameCurSec=nom.lower()[0:-1]+'x_y_vip'+domain
				reverseCurSec=getReverseDns(ipSecCur,DNSs[env])	
				if (not reverseCurSec or checkDefaultReverseDNS(ipSecCur,reverseCurSec)) or force:
					print(reverseCurSec)
					emptyIP[ipSecCur]={'possibleValue':nameCurSec}
				
		if 'hsrp' in interface:
			ip_virtuel=interface['hsrp'][0]
			nameCurHsrp=getGenericName((nom).lower())+'-hsrp_'+vrfCur+'_'+ifNameCur.replace('/','-')+domain
			try:
				vrfCur=interface['vrf'][0].replace('+','-')
				reverseCurHsrp=getReverseDns(ip_virtuel,DNSs[env])
				nameCurHsrp=getGenericName(nom.lower())+'_hsrp_'+ifNameCur.replace('/','-').replace('.','-')+'_'+vrfCur.lower()+domain
			except KeyError as E:
				reverseCurHsrp=getReverseDns(ip_virtuel,DNSs[env])
				nameCurHsrp=getGenericName(nom.lower())+'_hsrp_'+ifNameCur.replace('/','-').replace('.','-')+domain
				
			if (not reverseCurHsrp or checkDefaultReverseDNS(ip_virtuel,reverseCurHsrp)) or force:
				print(reverseCurHsrp)
				emptyIP[ip_virtuel]={'possibleValue':nameCurHsrp}
				
		if 'vip' in interface:
			ip_virtuel=interface['vip'][0].split()[0]
			vrfCur=interface['vrf'][0].replace('+','-')
			ifNameCur=interface['interface'][0]
			if 'vs' not in vrfCur:
				nameCurVip=getGenericName(nom.lower())+'_'+ifNameCur.replace('/','-').replace('.','-')+domain
			else:
				nameCurVip=getGenericName(nom.lower())+'_'+vrfCur+'-'+ifNameCur.replace('/','-').replace('.','-')+domain
			

			reverseCurVip=getReverseDns(ip_virtuel,DNSs[env])
				
			if (not reverseCurVip or checkDefaultReverseDNS(ip_virtuel,reverseCurVip)) or force:
				print(reverseCurVip)
				emptyIP[ip_virtuel]={'possibleValue':nameCurVip}				
		
	return emptyIP

def getNameFromInterface(ifs,env='BNP',domain='fr.net.intra'):
	DNSEntry={}
	domain='.'+domain
	for hostname in ifs:
		nom=hostname
		DNSEntry[hostname]={}
		for interface in ifs[hostname]:
			for ip__ in interface['ip']:
				ipCur=ip__.split()[0]
				ifNameCur=getShortIf(interface['interface'][0])
				if ipCur=='55.0.39.256':
					pdb.set_trace()
					'stop'
				try:
					vrfCur=interface['vrf'][0].replace('+','-')
					if 'anycast-gateway' in interface:
						if interface['anycast-gateway'][0]=='on':
							nameCur=getAnycastSuffix(nom)+'_'+ifNameCur.replace('/','-')+'_'+vrfCur+domain
					else:
						nameCur=nom.lower()+'_'+ifNameCur.replace('/','-').replace('.','-')+'_'+vrfCur.lower()+domain
				except KeyError as E:
					nameCur=nom.lower()+'_'+ifNameCur.replace('/','-').replace('.','-')+domain
				
				DNSEntry[hostname][ipCur]={'possibleValue':nameCur}

			if 'ip secondary' in interface:
				if interface['interface'][0].lower()!='loopback1':
					continue
				ipSecCur=interface['ip secondary'][0].split()[0]
				nameCurSec=nom.lower()[0:-1]+'x_y_vip'+domain
				DNSEntry[hostname][ipSecCur]={'possibleValue':nameCurSec}
			if 'hsrp' in interface:
				ip_virtuel=interface['hsrp'][0]
				nameCurHsrp=getGenericName(nom.lower())+'-hsrp_'+vrfCur+'_'+ifNameCur.replace('/','-')+domain			
				DNSEntry[hostname][ip_virtuel]={'possibleValue':nameCurHsrp}	
				
	return DNSEntry
	
def getReverseDns(IP,LISTE_DNS):

	resultat=[]
	

	for DNS in LISTE_DNS:
		name_cur=None
		try:
			answerCur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR,  use_edns=0),DNS,timeout=3)
			name_cur=[ res for res in answerCur.answer[0].__str__().split('\n') ]
			len_answer=len(answerCur.answer[0].__str__().split('\n'))

		except  DNSException as E:
			print(E)
			sleep(5)
			try:
				answerCur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR,  use_edns=0),DNS,timeout=3)
				name_cur=answerCur.answer[0].__str__().split()[-1]

			except  DNSException as E:
				pdb.set_trace()
				print(E)
			except IndexError:
				pass
		except IndexError:
			pass
		if name_cur:
			resultat.append(name_cur)
	return resultat	
		
def testIPinNetworks(ip__,networks):
	
	for network in networks:
		if IPAddress(ip__) in IPNetwork(network):
			return True
			
	return False

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet
		
def filterIP(ips,networks):
	
	IPSFiltered={}
	
	for ip__ in ips:
		if testIPinNetworks(ip__,networks):
			IPSFiltered[ip__]=ips[ip__]
	
	return IPSFiltered
	
def writeCsvInfoblox(ips,filename,mode='dict'):
	header='header-hostrecord,addresses*,configure_for_dns*,view,fqdn*'
	headerLst=header.split(',')
	headers_host_ref={value:num for num,value in enumerate(headerLst,0)}
	defaultLineHost=[ "" for i in headerLst]
	dataCsv=[headerLst]
	
	if mode=='dict':
		for equipment in ips:
			for ip in ips[equipment]:
				lineCur=defaultLineHost.copy()
				lineCur[headers_host_ref['addresses*']]=ip
				lineCur[headers_host_ref['fqdn*']]=ips[equipment][ip]['possibleValue']
				lineCur[headers_host_ref['header-hostrecord']]='hostrecord'
				lineCur[headers_host_ref['view']]='default'
				lineCur[headers_host_ref['configure_for_dns*']]='true'
				if lineCur not in dataCsv:
					dataCsv.append(lineCur)
	elif mode=='list':
		for ip in ips:
			lineCur=defaultLineHost.copy()
			lineCur[headers_host_ref['addresses*']]=ip['ip']
			lineCur[headers_host_ref['fqdn*']]=ip['reverse']
			lineCur[headers_host_ref['header-hostrecord']]='hostrecord'
			lineCur[headers_host_ref['view']]='default'
			lineCur[headers_host_ref['configure_for_dns*']]='true'
			if lineCur not in dataCsv:
				dataCsv.append(lineCur)	
	writeCsvData(filename,dataCsv)

			
def writeCsvData(filename_,datas):
	file=open(filename_,'w')

	writer=csv.writer(file,delimiter=";")
	
	with file:
		writer.writerows(datas)

def suppressLastPoint(Str__):
	if Str__[-1]=='.':
		return Str__[:-1]
	else:
		return Str__
		
def getOldEntry(ifsNew,ifOld,nameOld="",env='BNP',regex=None):
	oldEntry=[]
	ipAlreadyUsed=[]

	for hostname in ifsNew:
		for interface in ifsNew[hostname]:
			for ip__ in interface['ip']:
				ipCur=ip__.split()[0]
				entryDnsCur=getReverseDns(ipCur,DNSs[env])
				try:
					nameCur=suppressLastPoint(entryDnsCur[0][0].split()[-1])
				except IndexError as E:
					continue
				ifCur=interface['interface'][0]
				if ipCur not in ipAlreadyUsed:
					print(nameCur)
					if regex:
						if 'pe2' in nameCur and '-intra' in 'nameCur':
							pdb.set_trace()
							'stop'
						if re.search(regex,nameCur):
							oldEntry.append({'ip': ipCur ,'reverse': nameCur})
							ipAlreadyUsed.append(ipCur)							
					elif not nameOld:
						oldEntry.append({'ip': ipCur ,'reverse': nameCur})
						ipAlreadyUsed.append(ipCur)
						
						if ifOld.lower() not in nameCur:
							print(f'Warning: Verify if suppression is needed for {hostname}/{ifCur}/{ipCur} :  {nameCur}' )
						
						
					else:
						if nameOld.lower() in nameCur:
							oldEntry.append({'ip': ipCur ,'reverse': nameCur})
							ipAlreadyUsed.append(ipCur)							
			
			if 'ip secondary' in interface:
				ipCur=interface['ip secondary'][0].split()[0]
				entryDnsCur=getReverseDns(ipCur,DNSs[env])
				nameCur=suppressLastPoint(entryDnsCur[0][0].split()[-1])
				if nameOld.lower() in nameCur:
					oldEntry.append({'ip': ipCur ,'reverse': nameCur})
					ipAlreadyUsed.append(ipCur)							
				
	return oldEntry

def patchAnycast(ifs,nameOld,env='BNP',domain=""):

	patch={'suppress':[] , 'add':[] }
	ipAlreadyUsed=[]

	for hostname in ifs:
		for interface in ifs[hostname]:
			for ip__ in interface['ip']:
				ipCur=ip__.split()[0]
				entryDnsCur=getReverseDns(ipCur,DNSs[env])
				try:
					nameCur=suppressLastPoint(entryDnsCur[0][0].split()[-1])
				except IndexError as E:
					namecur=""
					print(E)
					print(f'DNS name missing for IP:{ipCur}')
					
					
				ifCur=interface['interface'][0]
				
				if not domain:
					domainCur='.'+".".join(nameCur.split('.')[1:])
				else:
					domainCur='.'+domain
				ifNameCur=getShortIf(interface['interface'][0])
				
				if not re.search(nameOld,nameCur,re.IGNORECASE):
					continue
					
				if ipCur not in ipAlreadyUsed:
					patch['suppress'].append({'ip': ipCur ,'reverse': nameCur})
					ipAlreadyUsed.append(ipCur)
					
					vrfCur=interface['vrf'][0].replace('+','-')
					newName=getAnycastSuffix(hostname)+'_'+ifNameCur.replace('/','-')+'_'+vrfCur+domainCur
					patch['add'].append({'ip': ipCur ,'reverse': newName})
					
			
				
	return patch
	
def replaceOldSuffix(OldName,NewNameDict):
	newName=OldName
	for oldSuffix in NewNameDict:
		if oldSuffix.lower() in OldName:
			newName=OldName.replace(oldSuffix.lower(),NewNameDict[oldSuffix].lower())
			break
	return newName

def getBranch(name,tdb):

	result=None
	data=tdb.getInfoEquipment(name,mode="normal")
	if data:
		result=data['Constructeur']
		
	return result
	
class node(object):
	def __init__(self,name,ip=None,branch=None):
		self.name=name.upper()
		self.ip=ip
		self.branch=branch		
		
		if not ip:
			self.ip=self.getIPfromName()
		if not branch:
			self.branch=self.getBranchFromName(TDB)
	
	def getIPfromName(self):
		IP__=None
		domains=[ 'xna.net.intra','fr.net.intra','uk.net.intra','net.intra' ]
		test_dns=False
		IP_DEFAULT=None
		for domain__ in domains:
			dns_requete=dns.query.udp(dns.message.make_query(self.name+'.'+domain__, dns.rdatatype.A, use_edns=0),'159.50.1.17')
			if dns_requete.rcode()==0:
				IP__=dns_requete.answer[0].__str__().split()[4]
				test_dns=True
				return IP__
		test_format_IP=False
		while not test_format_IP:
			IP__=input(f'Enter the IP for {self.name}:')
			try:
				ipaddress.ip_address(IP__)
				test_format_IP=True
			except:
				pass
		return IP__
	
	def getBranchFromName(self,tdb=None):
		ALL_BRANCH=['CHECKPOINT','PALOALTO','FORTINET','CISCO','ARISTA']
		if tdb:
			Branch=getBranch(self.name,tdb)
		else:
			Branch=None
		DEFAULT_BRANCH='CISCO'
		while not Branch:
			Branch=input(f'Enter the branch for {self.name}({DEFAULT_BRANCH}):')
			if not Branch:
				Branch=DEFAULT_BRANCH
			if Branch not in ALL_BRANCH:
				Branch=None
				
		return Branch
		
	def __str__(self):
		return pprs(self.__dict__)
		
	def __repr__(self):
		return pprs(self.__dict__)
		
class containerNodes(object):
	def __init__(self,ymlFile,host_file=""):
		
		self.filedump=ymlFile
		if os.path.exists(ymlFile) and os.stat(ymlFile).st_size != 0:
			self.load()
		else:
			self.nodes={}
			
		if host_file:
			self.loadCiscofile(cisco_file)
		else:
			self.filedump=ymlFile
			self.load()
			
		
			
	def load(self):
		self.nodes={}
		with open(self.filedump, 'r') as yml_r:
			nodes=yaml.load(yml_r,Loader=yaml.SafeLoader)
			
		if not nodes:
			return {}
		
		
		for cisco in nodes:
			self.nodes[cisco]=node(nodes[cisco]['name'],nodes[cisco]['ip'],nodes[cisco]['branch'])

			
	def save(self):
		nodes={}
		for ciscoName in self.nodes:
			try:
				nodes[ciscoName]= self.nodes[ciscoName].__dict__
			except AttributeError as E:
				pdb.set_trace()
				print(E)
			

		with open(self.filedump,'w') as yml_w:
			yaml.dump(nodes,yml_w ,default_flow_style=False)
			
	def loadCiscofile(self, file):
		with open(file,'r') as file_hostName:
			hostNames=[ host.upper() for host in  file_hostName.read().split() ]
			
	
		for name in hostNames:
			print(name)
			self.nodes[name]=node(name)
		
	def __str__(self):
		pprs(self.nodes)
	def __repr__(self):
		pprs(self.nodes)
		
	def getNodeInfo(self,hostname):
		infoNode=self.nodes.get(hostname.upper())
		if not infoNode:
			self.addNode(hostname)
			infoNode=self.nodes.get(hostname.upper())
			
		return infoNode
		
	def addNode(self,hostname):
		 self.nodes[hostname.upper()]=node(hostname.upper())
		 
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-e","--equipment",action="append",help="hostname")
	group.add_argument("-l","--list-equipment",dest='equipmentsLst',action="store",help="hostname")
	parser.add_argument("-y","--get-brand",dest='yaml_hosts',action="store_true",help="get brand, it will be used with no Cisco device")
	group.add_argument("--fabric",action="store",help="fabric name")
	parser.add_argument("--cache",action="store_true",help="use cache to get interface status",required=False)
	parser.add_argument("--env",action="store",default='BNP',help="DNS environment",required=False)
	parser.add_argument("--tag",action="store",help="TAG to save csv file to import in infoBlox",required=False)
	parser.add_argument("--domain",action="store",help="domain, default:fr.net.intra",default='fr.net.intra',required=False)
	parser.add_argument("--networks",action="store",help="networks list in txt file to filter reverse dns to add",required=False)
	parser.add_argument("--suppress",action="store",help="old_interface:new_interface",required=False)
	parser.add_argument("--rename",action="store",help="File format:old_hostname:new_hostname",required=False)
	parser.add_argument("--patch",action="store",help="File format:old_hostname:new_hostname",required=False)
	parser.add_argument("--migrate",action="store",help="regexthat match old entry",required=False)
	parser.add_argument("--force",action="store_true",default=False,help="find a reverse even if one already exists",required=False)
	parser.add_argument("--renew",action="store_true",help="renew cache older than 2 hours, only with cache",required=False)
	parser.add_argument("--verbose",action="store_true",help="verbose",required=False)
	args = parser.parse_args()
	
	RunIfs={}
	FWRunIfs={}
	verifData={}
	verifDataFiltered={}
	branches={}
	TDB=tdbContainer(dump=get_last_dump(PATH_TDB_DUMP))
	
	if args.equipment:
		equipments=args.equipment
	
	if args.equipmentsLst:
		equipments=getListNetFromFile(args.equipmentsLst)
		
	if args.fabric:
		with open(YAML_ENV, 'r') as yml__:
			allEnv=yaml.load(yml__,Loader__)
		try:
			equipments=allEnv[args.fabric]
		except KeyError as E:
			print('Known environments:')
			ppr(list(allEnv.keys()))
			raise E	
	
	if args.renew:
		aging=7200
	else:
		aging=0
		
	if not args.yaml_hosts:
		for equipment in equipments:
			TAG_RUNIF_HOST=f'{TAG_PREFIX_RUNIF}{equipment.upper()}'
			cacheRunIf=cc.Cache(TAG_RUNIF_HOST)
			if args.cache:
				if cacheRunIf.isOK(aging=aging):
					print(f'Caching interface from running is present for {equipment.upper()}')
					print(f'timestamp Interface for {equipment.upper()} :{cacheRunIf.get_timestamp()}')
					RunIfs[equipment]=cacheRunIf.getValue()
				else:
					print(f'Caching interface from running is not present for {equipment.upper()}')
					RunIfs[equipment]=getInterfaceRunning(equipment)
					cacheRunIf.save(RunIfs[equipment])
	
					
			
			else:
				RunIfs[equipment]=getInterfaceRunning(equipment)
				cacheRunIf.save(RunIfs[equipment])
	else:
		hosts_db=containerNodes(HOSTS)
		listHostByType=extractFW(equipments,TDB)
		fwCacheNOK=[]
		pdb.set_trace()
		for equipment in listHostByType['other']:
			infoCur=hosts_db.getNodeInfo(equipment)
			branchCur=infoCur.__dict__['branch']
			branches[equipment]=branchCur
			TAG_RUNIF_HOST=f'{TAG_PREFIX_RUNIF}{equipment.upper()}'
			cacheRunIf=cc.Cache(TAG_RUNIF_HOST)

			if args.cache:
				if cacheRunIf.isOK(aging=aging):
					print(f'Caching interface from running is present for {equipment.upper()}')
					print(f'timestamp Interface for {equipment.upper()} :{cacheRunIf.get_timestamp()}')
					RunIfs[equipment]=cacheRunIf.getValue()
				else:
					print(f'Caching interface from running is not present for {equipment.upper()}')
					RunIfs[equipment]=getInterfaceRunning(equipment)
					cacheRunIf.save(RunIfs[equipment])

			else:
				RunIfs[equipment]=getInterfaceRunning(equipment)
				cacheRunIf.save(RunIfs[equipment])
					
		for equipment in listHostByType['fw']:
			infoCur=hosts_db.getNodeInfo(equipment)
			branchCur=infoCur.__dict__['branch']
			branches[equipment]=branchCur
			TAG_RUNIF_HOST=f'{TAG_PREFIX_RUNIF}{equipment.upper()}'
			cacheRunIf=cc.Cache(TAG_RUNIF_HOST)
			
			if args.cache:
				if cacheRunIf.isOK(aging=aging):
					print(f'Caching interface from running is present for {equipment.upper()}')
					print(f'timestamp Interface for {equipment.upper()} :{cacheRunIf.get_timestamp()}')
					FWRunIfs[equipment]=cacheRunIf.getValue()
				else:
					fwCacheNOK.append(equipment)
					print(f'Caching interface from running is not present for {equipment.upper()}')

					
			
			else:
				fwCacheNOK.append(equipment)
				print(f'Caching interface from running is not used for {equipment.upper()}')
		
		if fwCacheNOK:
			print('Get Interface for these equipments')
			ppr(fwCacheNOK)
			FwCtx=containerFW(FWS)
			allIPFW=getAllIP(fwCacheNOK,FwCtx,secDb,caching=True)
		else:
			allIPFW={}
		
		if 	allIPFW:
			for branch in allIPFW:
				for equipment in allIPFW[branch]:
					FWRunIfs[equipment]=allIPFW[branch][equipment]
			
			
		for equipment in FWRunIfs:
			infoCur=FWRunIfs[equipment]
			branchCur=branches[equipment]
			if 'VSX' in equipment:
				branchCur='CHECKPOINT_VSX'
			ifsCurFW=infoCur
			if branchCur=='FORTINET':
				RunIfs[equipment]=ifsCurFW
			elif branchCur=='CHECKPOINT_VSX':
				for vs in FWRunIfs[equipment]: 
					for interface in FWRunIfs[equipment][vs]:
						interfaceCur=interface
						ipCur= " ".join(FWRunIfs[equipment][vs][interface])
						vrfCur='vs'+str(vs)
						if equipment in RunIfs:
							RunIfs[equipment].append({'interface':[interfaceCur] , 'vrf':[vrfCur],'vip':[ipCur]})
						else:
							RunIfs[equipment]=[{'interface':[interfaceCur] , 'vrf':[vrfCur],'vip':[ipCur] }]
			elif branchCur=='CHECKPOINT':
				maskCur={}
				for interface in FWRunIfs[equipment]['physical']['interface']:
					interfaceCur=interface
					maskCur[interfaceCur]=FWRunIfs[equipment]['physical']['interface'][interfaceCur][1]
					ipCur= " ".join(FWRunIfs[equipment]['physical']['interface'][interfaceCur])
					vrfCur='GRT'
					if equipment in RunIfs:
						RunIfs[equipment].append({'interface':[interfaceCur] , 'vrf':[vrfCur],'ip':[ipCur]})
					else:
						RunIfs[equipment]=[{'interface':[interfaceCur] , 'vrf':[vrfCur],'ip':[ipCur] }]

					
				for interface in FWRunIfs[equipment]['virtual']:
					interfaceCur=interface
					mask=maskCur[interface]
					ipCur=FWRunIfs[equipment]['virtual'][interfaceCur]+" "+mask
					if equipment in RunIfs:
						RunIfs[equipment].append({'interface':[interfaceCur] , 'vrf':[vrfCur],'vip':[ipCur]})
					else:
						RunIfs[equipment]=[{'interface':[interfaceCur] , 'vrf':[vrfCur],'vip':[ipCur] }]						

			elif branchCur=='PALOALTO':
				print('PALO ALTO not supported for now')
				pass
			else:
				print(f'{equipment}: {branch} not supported')
					
	RunIfsCur={}
	if args.networks:
		networks=getListNetFromFile(args.networks)
		for equipment in equipments:
			try:
				RunIfsCur[equipment]=[]
				for y in RunIfs[equipment]:
					if 'ip' in y:
						if testIPinNetworks(y['ip'][0].split()[0],networks):
							RunIfsCur[equipment].append(y)
					elif 'vip' in y:
						if testIPinNetworks(y['vip'][0].split()[0],networks):
							RunIfsCur[equipment].append(y)						
				#RunIfsCur[equipment]=list(filter(lambda y: testIPinNetworks(y['ip'][0].split()[0],networks) ,  RunIfs[equipment]))
			except KeyError as E:
				pdb.set_trace()
				print(E)
	else:
		RunIfsCur=RunIfs
		
	for equipment in equipments:
		print(f'Running check DNS for {equipment}')
		if not args.yaml_hosts:
			verifData[equipment]=checkReversePresence(equipment,RunIfsCur[equipment],domain=args.domain,force=args.force)
		else:
			verifData[equipment]=checkReversePresence(equipment,RunIfsCur[equipment],domain=args.domain,branch=branches[equipment],force=args.force)
			
	if args.tag:
	
		dirCurCsv=CSV_DNS_DIR+'/'+args.tag
		if not os.path.exists(dirCurCsv):
			os.makedirs(dirCurCsv)
		suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.csv", localtime())
		csvInfoBlox=dirCurCsv+'/hosts'+suffix
		
		writeCsvInfoblox(verifData,csvInfoBlox)
		
	ppr(verifData)
	
	if args.suppress:
		supLst=args.suppress.split(':')
		oldIf=supLst[0]
		newIf=supLst[1]
		
		RunIfsToBeModified={}
		for equipment in equipments:
			RunIfsToBeModified[equipment]=list(filter(lambda y: y['interface'][0].lower()==newIf.lower() ,  RunIfs[equipment]))
			ppr(RunIfsToBeModified)
		
		entryToSuppress=getOldEntry(RunIfsToBeModified,oldIf)
		entryToAdd=getNameFromInterface(RunIfsToBeModified,env=args.env,domain=args.domain)
		
		print('Entry to be suppressed:')
		ppr(entryToSuppress)

		print('Entry to be added:')
		ppr(entryToAdd)		
		if args.tag:
	
			dirCurCsv=CSV_DNS_DIR+'/'+args.tag
			if not os.path.exists(dirCurCsv):
				os.makedirs(dirCurCsv)
			suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.csv", localtime())
			csvInfoBloxDel=dirCurCsv+'/entry_to_suppress'+suffix
			csvInfoBloxAdd=dirCurCsv+'/entry_to_add'+suffix
			writeCsvInfoblox(entryToSuppress,csvInfoBloxDel,mode='list')
			writeCsvInfoblox(entryToAdd,csvInfoBloxAdd)
			
	if args.rename:
	
		hostsByOldHost={}
		with open(args.rename,'r') as FileHosts:
			allLines=FileHosts.read().split('\n')
		
		for line in allLines:
			if ':' in line:
				supLst=line.split(':')
				hostsByOldHost[supLst[0]]=supLst[1]
		
		#RunIfsToBeModified={}
		#for equipment in equipments:
		#	RunIfsToBeModified[equipment]=list(filter(lambda y: y['interface'][0].lower()==newIf.lower() ,  RunIfs[equipment]))
		#	ppr(RunIfsToBeModified)
		
		entryToSuppress=[]
		
		for oldSuffix in hostsByOldHost:
			entryToSuppress+=getOldEntry(RunIfs,"",oldSuffix)
			
			
		entryToAdd=[ {'ip':entry['ip'],'reverse':replaceOldSuffix(entry['reverse'],hostsByOldHost)}  for entry in entryToSuppress ] 
		
		print('Entry to be suppressed:')
		ppr(entryToSuppress)

		print('Entry to be added:')
		ppr(entryToAdd)		
		
		if args.tag:
	
			dirCurCsv=CSV_DNS_DIR+'/'+args.tag
			if not os.path.exists(dirCurCsv):
				os.makedirs(dirCurCsv)
			suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.csv", localtime())
			csvInfoBloxDel=dirCurCsv+'/entry_to_suppress'+suffix
			csvInfoBloxAdd=dirCurCsv+'/entry_to_add'+suffix
			writeCsvInfoblox(entryToSuppress,csvInfoBloxDel,mode='list')
			writeCsvInfoblox(entryToAdd,csvInfoBloxAdd,mode='list')

	if args.patch:
	

		if args.domain=='fr.net.intra':
			patchEntry= patchAnycast(RunIfs,args.patch)
		else:
			patchEntry= patchAnycast(RunIfs,args.patch,domain=args.domain)
			
			
		print('Entry to be suppressed:')
		ppr(patchEntry['suppress'])

		print('Entry to be added:')
		ppr(patchEntry['add'])

		
		if args.tag:
	
			dirCurCsv=CSV_DNS_DIR+'/'+args.tag
			if not os.path.exists(dirCurCsv):
				os.makedirs(dirCurCsv)
			suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.csv", localtime())
			csvInfoBloxDel=dirCurCsv+'/entries_to_suppress'+'_'+args.tag+suffix
			csvInfoBloxAdd=dirCurCsv+'/entries_to_add'+'_'+args.tag+suffix
			writeCsvInfoblox(patchEntry['suppress'],csvInfoBloxDel,mode='list')
			writeCsvInfoblox(patchEntry['add'],csvInfoBloxAdd,mode='list')
			
	if args.migrate:
	
		regexCur=args.migrate
		hostsByOldHost={}

		
		#RunIfsToBeModified={}
		#for equipment in equipments:
		#	RunIfsToBeModified[equipment]=list(filter(lambda y: y['interface'][0].lower()==newIf.lower() ,  RunIfs[equipment]))
		#	ppr(RunIfsToBeModified)
		
		entryToSuppress=[]
		
		
		entryToSuppress=getOldEntry(RunIfs,"",regex=regexCur)
		
		ipConcerned=[ entry['ip']  for entry in entryToSuppress ]
		
		RunIfsFiltered={}
		for host__ in RunIfs:
			
			ifsFiltered=[ interface for interface in RunIfs[host__] if interface['ip'][0].split()[0] in ipConcerned ]
			if ifsFiltered:
				RunIfsFiltered[host__]=ifsFiltered
		
		newDNSEntry=getNameFromInterface(RunIfsFiltered,env=args.env,domain=args.domain)	
		
		
		entryToAdd=[ {'ip':entry['ip'],'reverse':replaceOldSuffix(entry['reverse'],hostsByOldHost)}  for entry in entryToSuppress ] 
		entryToAdd=[]
		
		for host__ in newDNSEntry:
			for ip__ in newDNSEntry[host__]:
				entryToAdd.append({'ip':ip__,'reverse':newDNSEntry[host__][ip__]['possibleValue']})
				
		print('Entry to be suppressed:')
		ppr(entryToSuppress)

		print('Entry to be added:')
		ppr(entryToAdd)		
		
		if args.tag:
	
			dirCurCsv=CSV_DNS_DIR+'/'+args.tag
			if not os.path.exists(dirCurCsv):
				os.makedirs(dirCurCsv)
			suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.csv", localtime())
			csvInfoBloxDel=dirCurCsv+'/entry_to_suppress'+suffix
			csvInfoBloxAdd=dirCurCsv+'/entry_to_add'+suffix
			writeCsvInfoblox(entryToSuppress,csvInfoBloxDel,mode='list')
			writeCsvInfoblox(entryToAdd,csvInfoBloxAdd,mode='list')