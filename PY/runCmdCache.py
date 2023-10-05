#!/usr/bin/env python3.8
# coding: utf-8

import jinja2
import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
import dns.resolver
import ipaddress
import yaml
import os
import sys
import pexpect
from getsec import *
import threading
from time import gmtime, strftime , localtime,time, sleep
from concurrent.futures import ThreadPoolExecutor , wait , ALL_COMPLETED

BASTION='159.50.29.244'
TSK="/home/d83071/CONNEXION/pass.db"
HOSTS='/home/d83071/yaml/hosts.yaml'

def rebond(login,passwd,bastion=BASTION,verbose=False):
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

def getListFromFile(filename):
	with open(filename,'r') as file_r:
		listStr=file_r.read().split()
	return listStr

	
class CISCO(object):
	def __init__(self,cisconame,ip=None,branch=None):
		self.name=cisconame.upper()
		self.ip=ip
		self.branch="CISCO"		
		
		if not ip:
			self.ip=self.getIPfromName()
		if not branch:
			self.branch=self.getBranchFromName()
	
	def getIPfromName(self):
		IP__=None
		domains=[ 'xna.net.intra','fr.net.intra','uk.net.intra','net.intra' ]
		test_dns=False
		IP_DEFAULT=None
		for domain__ in domains:
			dns_requete=dns.query.udp(dns.message.make_query(self.name+'.'+domain__, dns.rdatatype.A, use_edns=0),'159.50.101.10')
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
	
	def getBranchFromName(self):
		ALL_BRANCH=['CHECKPOINT','PALOALTO','FORTINET','CISCO']
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
		
class containerCISCO(object):
	def __init__(self,ymlFile,cisco_file=""):
		
		self.filedump=ymlFile
		if os.path.exists(ymlFile) and os.stat(ymlFile).st_size != 0:
			self.load()
		else:
			self.hostnames={}
			
		if cisco_file:
			self.loadCiscofile(cisco_file)
		else:
			self.filedump=ymlFile
			self.load()
			
		
			
	def load(self):
		self.hostnames={}
		with open(self.filedump, 'r') as yml_r:
			ciscos=yaml.load(yml_r,Loader=yaml.SafeLoader)
			
		if not ciscos:
			return {}
		
		
		for cisco in ciscos:
			self.hostnames[cisco]=CISCO(ciscos[cisco]['name'],ciscos[cisco]['ip'],ciscos[cisco]['branch'])

			
	def save(self):
		ciscos={}
		for ciscoName in self.hostnames:
			try:
				ciscos[ciscoName]= self.hostnames[ciscoName].__dict__
			except AttributeError as E:
				pdb.set_trace()
				print(E)
			

		with open(self.filedump,'w') as yml_w:
			yaml.dump(ciscos,yml_w ,default_flow_style=False)
			
	def loadCiscofile(self, file):
		with open(file,'r') as file_ciscoName:
			ciscoNames=[ cisco.upper() for cisco in file_ciscoName.read().split() ]
			
	
		for cisconame in ciscoNames:
			print(cisconame)
			self.hostnames[cisconame]=CISCO(cisconame)
		
	def __str__(self):
		pprs(self.hostnames)
	def __repr__(self):
		pprs(self.hostnames)
		
	def getCiscoInfo(self,hostname):
		infoCISCO=self.hostnames.get(hostname.upper())
		if not infoCISCO:
			self.addCisco(hostname)
			infoCISCO=self.hostnames.get(hostname.upper())
			
		return infoCISCO
		
	def addCisco(self,hostname):
		 self.hostnames[hostname.upper()]=CISCO(hostname.upper())
		 self.save()

class runCmd(threading.Thread):
	def __init__(self,hostname,commandOrFile,output="",ciscoDb=None,customQueue=None,modeCommand=True,secDb=None,verbose=False):
		if customQueue:
			threading.Thread.__init__(self)
		else:
			threading.Thread.__init__(self,args=(customQueue,))
		self.hostname=hostname
		self.verbose=verbose
		if modeCommand:
			if isinstance(commandOrFile,str):
				self.commands=commandOrFile.split(',')
			else:
				self.commands=commandOrFile
		else:
			self.fileCommands=commandOrFile
		self.output=output
		
		self.modeCommand=modeCommand
		
		self.ciscoDb=ciscoDb
		self.infoHost=self.ciscoDb.getCiscoInfo(self.hostname).__dict__
		
		if not self.infoHost:
			self.ciscoDb.addCisco(hostname)
			
		self.tsk=secDb
		self.prompts=['>','#','\$']
		
		if self.infoHost['branch']=='CHECKPOINT':
			self.prompt='>'
		elif self.infoHost['branch']=='FORTINET':	
			self.prompt='\$'
		elif self.infoHost['branch']=='PALOALTO':
			self.prompt='\)\>'
		elif self.infoHost['branch']=='CISCO':
			self.prompt=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']				
		else:
			self.prompt=self.prompts
			pdb.set_trace()
			
	def launch(self):
		self.result={}
		loginCur=self.tsk['DEFAULT']['login']
		SSH_COMMAND=f'ssh -o "StrictHostKeyChecking=no" -l {loginCur} {self.hostname}'
		passwd=self.tsk.tac
		
		try:
			child=rebond(self.tsk['DEFAULT']['login'],self.tsk['ldap_old'],verbose=self.verbose)
			print(self.infoHost)
			
	
			if self.verbose:
				child.logfile = sys.stdout.buffer
	
			child.sendline(SSH_COMMAND)
			child.expect('[pP]assword:')
			#print('stop')
			child.sendline(passwd)
			child.expect(self.prompt)
	
			child.send('\r')
			child.expect(self.prompt)
			
			if self.modeCommand:
				for command in self.commands:
					child.sendline(command)
					child.expect(self.prompt)
					self.result[command]=child.before.decode()
				
			child.send('\r')
			child.expect(self.prompt)
			
			self.exit(child)
		except pexpect.exceptions.TIMEOUT:
			print(f'connection to {self.hostname} failed: TIMEOUT' )
		
	def exit(self,child):
		child.sendline('exit')
		child.expect('>')
		child.sendline('exit')
		child.expect('>')
		child.sendline('exit')
		child.expect(pexpect.EOF)
		child.close()
				
		
	def run(self):
		self.launch()
		
	def saveOutput(self,directory):
		list_command=list(filter( lambda y: y!='terminal length 0',self.commands) )
		
		if not os.path.exists(directory):
			os.makedirs(directory)
		
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())		
		for command in list_command:
			name_cur=command.replace(' ','_')
			filename=directory+'/'+self.hostname+suffixe_time+'_'+name_cur+'.log'
			with open(filename,'w+') as file_w:
				try:
					file_w.write(self.result[command])
				except KeyError:
					print(f'command {command} failed for {self.hostname}')
		
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-y","--yaml",action="store",default=HOSTS,help="yaml file that contains all firewall information ",required=False)
	parser.add_argument("-f","--file" ,action="store",default="",help="file contains firewall to add to dump ",required=False)
	parser.add_argument("-v","--verbose" ,action="store_true",default="",help="mode verbose ",required=False)
	parser.add_argument("-s","--save" ,action="store",default="",help="save output ",required=False)
	parser.add_argument("--tsk",action="store",default=TSK,help="Do not ask",required=False)
	group1.add_argument("--hostname",action="store",help="Hostname",required=False)
	group1.add_argument("--filehost",action="store",help="file that contains host",required=False)
	group2.add_argument("-c",'--commands',action="store",help="commands separate by comma",required=False)
	group2.add_argument("-a",'--action',action="store",help="predefined Action",required=False)
	args = parser.parse_args()
	
	if not args.tsk:
		secDb=TSKDB
	
	else:
		secDb=secSbe(args.tsk)
	
	CISCOdb=containerCISCO(args.yaml,args.file)
	
	if args.commands or args.action:
		modeCommand=True
	else:
		modeCommand=False
	
	if args.action:
		if args.action == 'FAILOVERSTATUS':
			commandes={'CHECKPOINT': ['cphaprob state'] ,'PALOALTO': ['set cli pager off','show high state','set cli pager on'], 'FORTINET': [ 'config global' , 'get sys ha status'] }
		elif args.action == 'RUNNING':
			commandes={'CISCO':['terminal length 0','sh run'] }
		else:
			raise ValueError(f'unknown action,known action ')
	if args.hostname:
		if args.action:
			infoCur=CISCOdb.getCiscoInfo(args.hostname)
			branchCur=infoCur.__dict__['branch']
			curCon=runCmd(args.hostname,commandes[branchCur],output='test',modeCommand=modeCommand,ciscoDb=CISCOdb,secDb=secDb,verbose=args.verbose)
			curCon.start()
			curCon.join()
			ppr(curCon.result)		
		else:
			curCon=runCmd(args.hostname,args.commands,output='test',modeCommand=modeCommand,ciscoDb=CISCOdb,secDb=secDb,verbose=args.verbose)
			curCon.start()
			curCon.join()
			ppr(curCon.result)
			
			print( curCon.result['cphaprob stat'].decode() )
			'stop'
		if args.save:
			curCon.saveOutput(args.save)
	if args.filehost:
		hostnames=getListFromFile(args.filehost)
		mCon={}
		infoCur={}
		branchCur={}
		fs=[]
		if args.action:
			for hostname in hostnames:
				infoCur[hostname]=CISCOdb.getCiscoInfo(hostname)
				branchCur[hostname]=infoCur[hostname].__dict__['branch']
			with ThreadPoolExecutor(max_workers=8) as e:
				for hostname in hostnames:
					mCon[hostname]=runCmd(hostname,commandes[branchCur[hostname]],output='test',modeCommand=modeCommand,ciscoDb=CISCOdb,secDb=secDb,verbose=args.verbose)
					print(f'Launch for {hostname}')
					fs.append(e.submit(mCon[hostname].launch))
				
				#while True:
				#	all_finished = True
				#
				#	print("\nHave the workers finished?")
				#
				#	for i, future in enumerate(fs):
				#		if future.done():
				#			print(f"Task {i} has finished")
				#		else:
				#			all_finished = False
				#			print(f"Task {i} is running...")
				#
				#	if all_finished:
				#		break
				#
				#	sleep(1)				
			wait(fs,timeout=30,return_when=ALL_COMPLETED)
			
		if args.save:			
			for hostname in hostnames:
				mCon[hostname].saveOutput(args.save)

			