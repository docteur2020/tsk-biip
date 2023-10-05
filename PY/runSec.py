#!/usr/bin/env python3.8
# coding: utf-8

import jinja2
import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
from getTdbInfo import PATH_TDB_DUMP , tdbContainer , get_last_dump
from ParsingShow import ParseCkpVsStat , ParseCkpVsIfconfig , ParseCkpCphaprobIf , ParsePaloAltoXmlInterface
from ipEnv import ifEntries
import argparse
import dns.resolver
import ipaddress
import yaml
import os
import sys
import pexpect
from getsec import *
import cache as cc
import threading
from time import gmtime, strftime , localtime,time, sleep
from concurrent.futures import ThreadPoolExecutor , wait , ALL_COMPLETED
from io import BytesIO

TDB=tdbContainer(dump=get_last_dump(PATH_TDB_DUMP))
BASTION='159.50.66.10'
TSK="/home/d83071/CONNEXION/pass.db"
FWS='/home/d83071/yaml/firewalls.yaml'
TAG_PREFIX_RUNIF='RUNIF_'
LIST_VSX=['FEST11-PRES-A3','FNORM6-PRES-A3','FEST11-PRES-B3','FNORM6-PRES-B3']

def getBranch(name,tdb):

	result=None
	data=tdb.getInfoEquipment(name,mode="normal")
	if data:
		result=data['Constructeur']
		
	return result


def rebond(login,passwd,bastion=BASTION,verbose=False):
	try:
		child=pexpect.spawn(f'ssh -l {login} {bastion}')
		if verbose:
			child.logfile = sys.stdout.buffer
		child.expect(['[Pp]assword:'])
		child.sendline(f'{passwd}')
		child.expect(['>','\$'])
		
	except:
		print('ERROR')
		pass
		
	return child

def incrName(name,oldNames):
	
	oldIndices=[]
	
	for oldName in oldNames:
		if name not in oldName:
			continue
		listOldName=oldName.split(':')
		if len(listOldName)==2:
			oldIndices
			indiceCur=int(listOldName[1])
			oldIndices.append(indiceCur)
		
	if len(	oldIndices)==0:
		resultat=name+':1'
		return resultat
		
	maxIndice=max(oldIndices)
	
	new_indice=str(maxIndice+1)
		
	resultat=name+':'+new_indice
	
	return resultat
	
class FW(object):
	def __init__(self,fwname,ip=None,branch=None,otherInfo={},tdb=TDB):
		self.name=fwname.upper()
		self.ip=ip
		self.branch=branch
		if not otherInfo:
			self.otherInfo={}
		else:
			self.otherInfo=otherInfo
		if not ip:
			self.ip=self.getIPfromName()
		if not branch:
			self.branch=self.getBranchFromName(tdb)
	
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
	
	def getBranchFromName(self,tdb):
		ALL_BRANCH=['CHECKPOINT','PALOALTO','FORTINET']
		Branch=getBranch(self.name,tdb)
		while not Branch:
			Branch=input('Enter the branch:')
			if Branch not in ALL_BRANCH:
				Branch=None
				
		return Branch
		
	def __str__(self):
		return pprs(self.__dict__)
		
	def __repr__(self):
		return pprs(self.__dict__)
		
class containerFW(object):
	def __init__(self,ymlFile,fw_file="",tdb=TDB):
		
		self.filedump=ymlFile
		self.tdb=tdb

		if os.path.exists(ymlFile) and os.stat(ymlFile).st_size != 0:
			self.load()
		else:
			self.firewalls={}
			
		if fw_file:
			self.loadFwfile(fw_file)
		else:
			self.filedump=ymlFile
			self.load()

		'stop'
		
			
	def load(self):
		self.firewalls={}
		with open(self.filedump, 'r') as yml_r:
			fws=yaml.load(yml_r,Loader=yaml.SafeLoader)
		for fw in fws:
			if 'otherInfo' in fws[fw]:
				self.firewalls[fw]=FW(fws[fw]['name'],fws[fw]['ip'],fws[fw]['branch'],fws[fw]['otherInfo'])
			else:
				self.firewalls[fw]=FW(fws[fw]['name'],fws[fw]['ip'],fws[fw]['branch'])
			
	def save(self):
		fws={}
		for fwName in self.firewalls:
			try:
				fws[fwName]= self.firewalls[fwName].__dict__
			except AttributeError as E:
				pdb.set_trace()
				print(E)
			

		with open(self.filedump,'w') as yml_w:
			yaml.dump(fws,yml_w ,default_flow_style=False)
			
	def loadFwfile(self, file):
		with open(file,'r') as file_fwName:
			fwNames=[ fw.upper() for fw in file_fwName.read().split() ]
			
	
		for fwname in fwNames:
			print(fwname)
			self.firewalls[fwname]=FW(fwname,tdb=self.tdb)
		
		self.save()
		
	def __str__(self):
		pprs(self.firewalls)
	def __repr__(self):
		pprs(self.firewalls)
		
	def getFwInfo(self,hostname):
		infoFW=self.firewalls.get(hostname.upper())
		
		if not infoFW:
			self.addFw(hostname)
			infoFW=self.firewalls.get(hostname.upper())
			
		return infoFW
		
	def addFw(self,hostname):
		self.firewalls[hostname.upper()]=FW(hostname.upper(),tdb=self.tdb)
		self.save()
		 
	def addOtherInfo(self,hostname,otherInfo):
		curData=self.firewalls[hostname.upper()].otherInfo.copy()
		curData.update(otherInfo)
		self.firewalls[hostname.upper()].otherInfo=curData
		self.save()		

class runCmd(threading.Thread):
	def __init__(self,hostname,command='',output="",fwDb=None,customQueue=None,modeCommand=True,secDb=None,verbose=False):
		if customQueue:
			threading.Thread.__init__(self)
		else:
			threading.Thread.__init__(self,args=(customQueue,))
		self.hostname=hostname
		self.verbose=verbose
		commandOrFile=command
		if modeCommand:
			if isinstance(commandOrFile,str):
				self.commands=commandOrFile.split(',')
			else:
				self.commands=commandOrFile
		else:
			self.fileCommands=commandOrFile
		self.output=output
		
		self.modeCommand=modeCommand
		
		self.fwDb=fwDb

		self.infoHost=self.fwDb.getFwInfo(self.hostname).__dict__
		
		if not self.infoHost:
			self.fwDb.addFw(hostname)
			
		self.tsk=secDb
		self.prompts=['>','#','\$']
		
		if self.infoHost['branch']=='CHECKPOINT':
			self.prompt='>'
		elif self.infoHost['branch']=='FORTINET':	
			self.prompt='\n[a-zA-Z]\\S+ #'			
		elif self.infoHost['branch']=='PALOALTO':
			self.prompt='>'		
		else:
			self.prompt=self.prompts

		self.branch=self.infoHost['branch']
		
	def launch(self):

		self.result={}
		self.output={}
		data_output={}
		
		infoCon=self.tsk.getMode(self.hostname)
		
		loginCur=infoCon[0]
		passwd=infoCon[1]

		SSH_COMMAND=f'ssh -o "StrictHostKeyChecking=no" -l {loginCur} {self.hostname}'
		child=rebond(self.tsk['DEFAULT']['login'],self.tsk['ldap_old'],verbose=self.verbose)
		print(self.infoHost)
		#print('la')
		

		if self.verbose:
			child.logfile = sys.stdout.buffer

		child.sendline(SSH_COMMAND)
		child.expect('[pP]assword:')
		#print('stop')
		child.sendline(passwd)
		child.expect(self.prompt)

		child.send('\r')
		child.expect(self.prompt)

		if self.branch=='CHECKPOINT':
			self.expert(child)

			sleep(1.2)
			child.sendline()
			child.expect(self.prompt)
		
		if self.branch=='PALOALTO':
			self.prompt='\)\>'
		
		if self.modeCommand:
			for command in self.commands:
			
				if command in data_output:
					command_index=incrName(command,list(data_output.keys()))
				else:
					command_index=command
					
				#if self.branch=='PALOALTO':
				#	if re.search('show',command):
				#		self.prompt='\}\s+^\S*\)\>'
				#	else:
				#		self.prompt='\)\>'
				data_output[command_index]=BytesIO()
				child.logfile_read = data_output[command_index]
				child.sendline(command)
				child.expect(self.prompt)
				#print('ici0')
				if self.branch=='CHECKPOINT':
					sleep(0.5)
					child.sendline()
					child.expect(self.prompt)
				elif self.branch==['PALOALTO']:
					sleep(1)	
				
				

				self.result[command_index]=child.before.decode()
				self.output[command_index]=data_output[command_index].getvalue().decode('UTF-8')

		child.send('\r')
		child.expect(self.prompt)
		

		self.exit(child)
		
	def exit(self,child):
		if self.branch=='CHECKPOINT':
			for i in range(1,3):
				child.sendline('exit')
				child.expect('\>')
			
		child.sendline('exit')
		#print('-ici')
		child.expect('\$')
		#print('-ici2')
		child.sendline('exit')
		child.expect('\$')
		#print('-ici3')
		child.sendline('exit')
		child.expect(pexpect.EOF)
		#print('-ici4')
		child.close()
				
	def expert(self,child):
		child.sendline('lock database override')
		child.expect('\>')
		child.sendline('tacacs_enable TACP-15')
		#print('ici')
		expect_value=child.expect(['password:','Failure'])
		#print('ici2')
		if expect_value==0:
			child.sendline(self.tsk.tac)
		else:
			child.sendline()
		sleep(.5)
		child.sendline(' ')
		child.sendline('lock database override')
		child.expect('\>')	
		child.expect('\>')
		#print('ici3')
		child.sendline('expert')
		child.expect('assword:')

		child.sendline(self.tsk['tac'])
		sleep(.5)
		child.sendline(' ')
		child.expect('#')
		sleep(.5)
		child.sendline()
		child.expect('#')
		#print('ici5')
		self.prompt='#'
		
	
	def run(self):
		self.launch()

def initVsx(hostnames,FWdb,secDb,max_workers=8,debug=False):
	fs=[]
	mCon={}

	with ThreadPoolExecutor(max_workers=8) as e:
		for hostname in hostnames:
			hostname=hostname.upper()
			infoCur=FWdb.getFwInfo(hostname)
			branchCur=infoCur.__dict__['branch']
			if branchCur != 'CHECKPOINT':
				print(f'{hostname} is not a CHECKPOINT')
				continue
			if 'VSX' not in hostname.upper() and hostname.upper() not in LIST_VSX:
				print(f'{hostname} do not contains VSX')
				continue
			mCon[hostname]=runCmd(hostname,'vsx stat -l',output='test',modeCommand=True,fwDb=FWdb,secDb=secDb,verbose=debug)
			print(f'Launch for {hostname}')
			fs.append(e.submit(mCon[hostname].launch))
			
		if debug:
			while True:
				all_finished = True
			
				print("\nHave the workers finished?")
			
				for i, future in enumerate(fs):
					if future.done():
						print(f"Task {i} has finished")
					else:
						all_finished = False
						print(f"Task {i} is running...")
			
				if all_finished:
					break
			
				sleep(10)	
	
	for hostname in hostnames:
		hostname=hostname.upper()
		resultCur=mCon[hostname].output['vsx stat -l']
		vsCur=ParseCkpVsStat(resultCur,modestr=True)
		FWdb.addOtherInfo(hostname,{'vs':vsCur})
		


def getAllVsxIP(hostnames,FWdb,secDb,max_workers=8,debug=False):
	fs=[]
	mCon={}

	with ThreadPoolExecutor(max_workers=8) as e:
		for hostname in hostnames:
			hostname=hostname.upper()
			infoCur=FWdb.getFwInfo(hostname)
			branchCur=infoCur.__dict__['branch']
			if branchCur != 'CHECKPOINT':
				print(f'{hostname} is not a CHECKPOINT')
				continue
			if 'VSX' not in hostname.upper() and hostname.upper() not in LIST_VSX:
				print(f'{hostname} do not contains VSX')
				continue
			if 'vs' not in infoCur.__dict__['otherInfo']:
				print(f'{hostname} do not contains vs informations, please run option --get-vsx before')
				continue
			vsCur=infoCur.__dict__['otherInfo']['vs']

			commandCur=[ ]
			
			for vs in vsCur:
				commandCur.append(f'vsenv {vs}')
				commandCur.append(f'ifconfig')
				commandCur.append(f'cphaprob -a if')
			mCon[hostname]=runCmd(hostname,commandCur,output='test',modeCommand=True,fwDb=FWdb,secDb=secDb,verbose=debug)
			print(f'Launch for {hostname}')
			fs.append(e.submit(mCon[hostname].launch))
			
		if debug:
			while True:
				all_finished = True
			
				print("\nHave the workers finished?")
			
				for i, future in enumerate(fs):
					if future.done():
						print(f"Task {i} has finished")
					else:
						all_finished = False
						print(f"Task {i} is running...")
			
				if all_finished:
					break
			
				sleep(10)	
	
	vsIP={}
	for hostname in hostnames:
		hostname=hostname.upper()
		vsIP[hostname]={}
		for command in mCon[hostname].output:
			if 'ifconfig' in command:
				resultCur=mCon[hostname].output[command]
				vsCur=ParseCkpVsIfconfig(resultCur,modestr=True)
				vsIP[hostname][vsCur['vsid']]=vsCur['interface']
		
	ppr( vsIP)
	
	return vsIP


def getAllCheckpointIP(hostnames,FWdb,secDb,max_workers=8,debug=False):
	fs=[]
	mCon={}

	with ThreadPoolExecutor(max_workers=8) as e:
		for hostname in hostnames:
			hostname=hostname.upper()
			infoCur=FWdb.getFwInfo(hostname)
			branchCur=infoCur.__dict__['branch']
			if branchCur != 'CHECKPOINT':
				print(f'{hostname} is not a CHECKPOINT')
				continue
			
			commandCur=[ ]
			
			
			commandCur.append(f'ifconfig')
			commandCur.append(f'cphaprob -a if')
			mCon[hostname]=runCmd(hostname,commandCur,output='test',modeCommand=True,fwDb=FWdb,secDb=secDb,verbose=debug)
			print(f'Launch for {hostname}')
			fs.append(e.submit(mCon[hostname].launch))
			
		if debug:
			while True:
				all_finished = True
			
				print("\nHave the workers finished?")
			
				for i, future in enumerate(fs):
					if future.done():
						print(f"Task {i} has finished")
					else:
						all_finished = False
						print(f"Task {i} is running...")
			
				if all_finished:
					break
			
				sleep(10)	
	
	IPs={}
	for hostname in hostnames:
		hostname=hostname.upper()
		IPs[hostname]={'physical':{} , 'virtual':{}}
		
		for command in mCon[hostname].output:
			if 'ifconfig' in command:
				resultCur=mCon[hostname].output[command]
				IPsCur=ParseCkpVsIfconfig(resultCur,modestr=True)
				IPs[hostname]['physical']=IPsCur
			elif 'cphaprob' in command and 'if' in command:
				resultCur=mCon[hostname].output[command]
				vipCur=ParseCkpCphaprobIf(resultCur,modestr=True)
				IPs[hostname]['virtual']=vipCur
				
	ppr( IPs)
	
	return IPs

def getAllFortinetIP(hostnames,FWdb,secDb,max_workers=8,debug=False):
	fs=[]
	mCon={}

	with ThreadPoolExecutor(max_workers=8) as e:
		for hostname in hostnames:
			hostname=hostname.upper()
			infoCur=FWdb.getFwInfo(hostname)
			branchCur=infoCur.__dict__['branch']
			if branchCur != 'FORTINET':
				print(f'{hostname} is not a FORTINET')
				continue
			
			commandCur=[ ]
				
			commandCur.append(f'show')
			
			mCon[hostname]=runCmd(hostname,commandCur,output='test',modeCommand=True,fwDb=FWdb,secDb=secDb,verbose=debug)
			print(f'Launch for {hostname}')
			fs.append(e.submit(mCon[hostname].launch))
			
		if debug:
			while True:
				all_finished = True
			
				print("\nHave the workers finished?")
			
				for i, future in enumerate(fs):
					if future.done():
						print(f"Task {i} has finished")
					else:
						all_finished = False
						print(f"Task {i} is running...")
			
				if all_finished:
					break
			
				sleep(10)	
	
	IPs={}
	command='show'
	for hostname in hostnames:
		hostname=hostname.upper()
		IPs[hostname]={}
		
		resultCur=mCon[hostname].result[command]
		ifRun=ifEntries.ParseFortigateInterface(resultCur)
		parsingInterface=ifRun
		parsingElement=next(parsingInterface)
		temp_list_interfaces=[ element.asDict() for element in  parsingElement[0][0] ]
		
		list_int_cur=[]
		for dict_in in temp_list_interfaces:
			try:
				if dict_in['ip']!='None':
					list_int_cur.append(dict_in)
					
			except KeyError:
				pass
		
		
		IPs[hostname]=list_int_cur
		
	ppr( IPs)
	
	return IPs

def getAllPaloAltoIP(hostnames,FWdb,secDb,max_workers=8,debug=False):
	fs=[]
	mCon={}

	with ThreadPoolExecutor(max_workers=8) as e:
		for hostname in hostnames:
			hostname=hostname.upper()
			infoCur=FWdb.getFwInfo(hostname)
			branchCur=infoCur.__dict__['branch']
			if branchCur != 'PALOALTO':
				print(f'{hostname} is not a PALOALTO')
				continue
			
			commandCur=[ 'set cli pager off','show config running','set cli pager on'  ]
				
			
			mCon[hostname]=runCmd(hostname,commandCur,output='test',modeCommand=True,fwDb=FWdb,secDb=secDb,verbose=debug)
			print(f'Launch for {hostname}')
			fs.append(e.submit(mCon[hostname].launch))
			
		if debug:
			while True:
				all_finished = True
			
				print("\nHave the workers finished?")
			
				for i, future in enumerate(fs):
					if future.done():
						print(f"Task {i} has finished")
					else:
						all_finished = False
						print(f"Task {i} is running...")
			
				if all_finished:
					break
			
				sleep(10)	
	
	IPs={}
	command='show config running'
	for hostname in hostnames:
		hostname=hostname.upper()
		IPs[hostname]={}
		
		resultCur=mCon[hostname].result[command]
		pdb.set_trace()
		ifRun=ParsePaloAltoXmlInterface(resultCur,modeStr=True)
		
		IPs[hostname]=ifRun
		
	ppr( IPs)
	
	return IPs
	
def sortHostByBranch(hostnames,FWdb=""):
	result={}
	
	if not FWdb:
		FWdb=containerFW(FWS)
		
	for hostname in hostnames:
		infoCur=FWdb.getFwInfo(hostname)
		branchCur=infoCur.__dict__['branch']
		if 'VSX' in hostname or hostname in LIST_VSX:
			branchCur='CHECKPOINT_VSX'
			
		if branchCur not in result:
				result[branchCur]=[hostname]
		else:
			result[branchCur].append(hostname)
			
	return result

def getAllIP(hostnames,FWdb,secDb,max_workers=8,caching=False,verbose=False):
	listSortedHost=sortHostByBranch(hostnames)

	resultAllIP={}
	for branch in listSortedHost:
		if branch=='CHECKPOINT_VSX':
			resultCur=getAllVsxIP(listSortedHost[branch],FWdb,secDb,debug=verbose)
		elif branch=='CHECKPOINT':
			ppr(verbose)
			resultCur=getAllCheckpointIP(listSortedHost[branch],FWdb,secDb,debug=verbose)
		elif branch=='FORTINET':
			resultCur=getAllFortinetIP(listSortedHost[branch],FWdb,secDb,debug=verbose)
		elif branch=='PALOALTO':
			resultCur=getAllPaloAltoIP(listSortedHost[branch],FWdb,secDb,debug=verbose)
		else:
			print(f'Branch not supported:{branch}')
			continue
		resultAllIP[branch]=resultCur
	
	if caching:
		for branch in resultAllIP:
			for hostname in resultAllIP[branch]:
				hostname=hostname.upper()
				TAG_RUNIF_HOST=f'{TAG_PREFIX_RUNIF}{hostname}'
				cacheRunIf=cc.Cache(TAG_RUNIF_HOST)
				cacheRunIf.save(resultAllIP[branch][hostname])
	
	ppr(resultAllIP)
	
	return resultAllIP
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-y","--yaml",action="store",default=FWS,help="yaml file that contains all firewall information ",required=False)
	parser.add_argument("-f","--file" ,action="store",default="",help="file contains firewall to add to dump ",required=False)
	parser.add_argument("-v","--verbose" ,action="store_true",help="mode verbose ",required=False)
	parser.add_argument("--tsk",action="store",default=TSK,help="Do not ask",required=False)
	
	group1.add_argument("--hostname",action="append",help="Hostname",required=False)
	group1.add_argument("--filehost",action="store",default=TSK,help="file that contains host",required=False)
	group2.add_argument("-c",'--commands',action="store",help="commands separate by comma",required=False)
	group2.add_argument("-a",'--action',action="store",help="predefined Action",required=False)
	group2.add_argument("--get-vsx",dest='getvsx',action="store_true",help="get and save in db vsx, only for checkpoint",required=False)
	group2.add_argument("--get-ip",dest='getip',action="store_true",help="get and save in db ip",required=False)
	
	parser.add_argument("--caching",action="store_true",help="save in cache result, only with option --get-ip",required=False)
	
	args = parser.parse_args()
	
	if  args.caching and not args.getip:
		raise argparse.ArgumentError(None,'--get-ip  is manadatory with --caching ')
		
	if not args.tsk:
		secDb=TSKDB
	
	else:
		secDb=secSbe(args.tsk)
	
	FWdb=containerFW(args.yaml,args.file)
	
	if args.commands or args.action:
		modeCommand=True
	else:
		modeCommand=False
		
	if args.action:
		if args.action == 'FAILOVERSTATUS':
			commandes={'CHECKPOINT': ['cphaprob state'] ,'PALOALTO': ['set cli pager off','show high state','set cli pager on'], 'FORTINET': [ 'config global' , 'get sys ha status'] }
		if args.action == 'GET_INTERFACE':
			commandes={'CHECKPOINT': ['cphaprob state'] ,'PALOALTO': ['set cli pager off','show high state','set cli pager on'], 'FORTINET': [ 'config global' , 'get sys ha status'] }
	if args.hostname:
		if args.action:
			infoCur=FWdb.getFwInfo(args.hostname)
			branchCur=infoCur.__dict__['branch']
			curCon=runCmd(args.hostname,commandes[branchCur],output='test',modeCommand=modeCommand,fwDb=FWdb,secDb=secDb,verbose=args.verbose)
			curCon.start()
			curCon.join()
			ppr(curCon.result)
		elif args.getvsx:
			listSortedHost=sortHostByBranch(args.hostname)
			for hostname in listSortedHost['CHECKPOINT_VSX']:
				initVsx(args.hostname,FWdb,secDb,debug=args.verbose)
			for branch in listSortedHost:
				if branch !='CHECKPOINT_VSX':
					for hostname in listSortedHost[branch]:
						print(f'{hostname} is not a CHECKPOINT VSX ({branch}), option --getvsx not supported')
		elif args.getip:
			getAllIP(args.hostname,FWdb,secDb,verbose=args.verbose,caching=args.caching)
		else:
			curCon=runCmd(args.hostname,args.commands,output='test',modeCommand=modeCommand,fwDb=FWdb,secDb=secDb,verbose=args.verbose)
			curCon.start()
			curCon.join()
			ppr(curCon.result)
			
			print( curCon.result['cphaprob stat'].decode() )
			'stop'
		
	