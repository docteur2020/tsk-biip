#!/usr/bin/env python3.8
# coding: utf-8

import getpass
import argparse
import yaml
import pyAesCrypt
from os import stat, remove , getpid
import pyparsing as pp
import pdb
import re
from pprint import pprint as ppr
from random import randrange

TMP="/home/d83071/TMP/filetsk"
TSK="MaisTueSF0uKouKouTskBillyJoeAzertyRienOublieRubiK5794"
BYPASS="/home/d83071/CONNEXION/LISTE_BYPASS.TXT"
DEFAULT_DB="/home/d83071/CONNEXION/pass.db"
DEFAULT_LOGIN="ld83071"
bufferSize = 64 * 1024

def saveData(data,filename):
	with open(filename,'w') as yml_w:
		yaml.dump(data,yml_w ,default_flow_style=False)


def loadData(yaml_file):
	data__=None
	with open(yaml_file) as io_yml:
		data__=yaml.load(io_yml,Loader=yaml.SafeLoader)
	return data__

class secSbe(object):
	def __init__(self,db__=None):
		self.initFileTmp()
		self.otherAttr=['pid','filetmp','db','passContainer','otherAttr','alea']

		if db__:
			self.db=db__
			self.load(self.db)
		else:
			self.getInitTac()
			self.getInitUnix()
			self.getInitWin()
			self.getInitLdap()
			self.getInitLocal()
			
		self.initPwdContainer()
	
	def __getitem__(self,key):
		try:
			return self.passContainer[key]
		except KeyError as E:
			return {'login':DEFAULT_LOGIN , 'passwd':self.passContainer['tac']}
		
	def initPwdContainer(self):
		self.passContainer={}
		
		for key in self.__dict__:
			if key not in self.otherAttr:
				self.passContainer[key]=self.__dict__[key]

		
	def getInitTac(self):
		self.tac=getpass.getpass('Entre le tacacs:')
		
	def getInitUnix(self):
		self.unix=getpass.getpass('Entre l\'unix:')
		
	def getInitWin(self):
		self.win=getpass.getpass('Entre le windows:')
		
	def getInitLdap(self):
		self.ldap=getpass.getpass('Entre le ldap:')  
		
	def getInitLocal(self):
		self.local=getpass.getpass('Entre le local:') 
		
	def setNewPass(self,name):
		new_p=getpass.getpass(f'Entre le {name}:') 
		login__=input(f'login({DEFAULT_LOGIN}):')
		if not login__:
			login__="ld83071"
			super().__setattr__(name,new_p)
			self.passContainer[name]=new_p
		else:
			super().__setattr__(name,{'login':login__,'passwd':new_p})
			self.passContainer[name]={'login':login__,'passwd':new_p}
		
	def deletePwd(self,name):
		if name in self.passContainer:
			del self.passContainer[name]
			
		if name in self.__dict__ and name not in self.otherAttr:
			super().__delattr__(name)
		
	def initFileTmp(self):
		self.pid=getpid()
		self.alea=randrange(0, 10000000, 2)
		self.filetmp=f'{TMP}__{self.pid}__{self.alea}.txt'
		
	def pri(self):
		ppr(self.passContainer)
		
	def save(self,file):
		saveData(self.passContainer,self.filetmp)
		pyAesCrypt.encryptFile(self.filetmp, file, TSK, bufferSize)
		remove(self.filetmp)
			
	def getMode(self,equipement):
		all_tsk=self.load_bypass(BYPASS)
		connexion=('ld83071',self.tac)

		try:
			info_cur=all_tsk[equipement.upper()]
			#print("connexion speciale")
			if info_cur[0]=='CUSTOM':
				connexion=(info_cur[1],info_cur[2])
			if info_cur[0]=='CUSTOM_IP':
				connexion=(info_cur[1],info_cur[2])
			if info_cur[0]=='DOMAN':
				connexion=("d83071",self.unix)
			if re.search('^LOCAL',info_cur[0]):
				if info_cur[0]=='LOCAL1':
					login__=self.passContainer[info_cur[0].lower()]['login']
					pass__ =self.passContainer[info_cur[0].lower()]['passwd']
					connexion=(login__,pass__)
				else:
					connexion=("admin",self.local)
			if info_cur[0]=='TSK':
				try:
					login__=self.passContainer[info_cur[1].lower()]['login']
					pass__ =self.passContainer[info_cur[1].lower()]['passwd']
					connexion=(login__,pass__)
				except KeyError as E:
					print(f'Le mode {info_cur[1]} n\'existe pas')
					print(E)
			if info_cur[0]=='VAULT':
				connexion=(info_cur[1],info_cur[2])
		except KeyError:
			#print("connexion normale")
			pass
		
		#print(str(connexion))
		
		return connexion
		
	def load(self,db):
		pyAesCrypt.decryptFile(db, self.filetmp, TSK, bufferSize)
		
		self.passContainer=loadData(self.filetmp)
		
		for key in self.passContainer:
			super().__setattr__(key,self.passContainer[key])

		
		try:
			remove(self.filetmp)
		except FileNotFoundError:
			pass
		
		return
		
	def load_bypass(self,filename):
		Hostname=pp.Word(pp.alphanums+'-_#').setParseAction(lambda t : t[0].upper())
		Mode=pp.Literal("ALTEON_PROXY_EXP")|pp.Literal("CDN")|pp.MatchFirst([pp.Literal("CUSTOM_VPX"),pp.Literal("CUSTOM_IP"),pp.Literal("CUSTOM")])|pp.Literal("EXPOSE_2")|pp.Literal("LOGIN_ACS_TELNET")|pp.Literal("TACACS_SSH_SPEC")|pp.Literal("MODE")|pp.Literal("DOMAN")|pp.Literal("LOCAL0_IP")|pp.Literal("TSK")|pp.Literal("LOCAL0")|pp.Literal("LOCAL1")|pp.Literal("VAULT")|pp.Literal("CKP")|pp.Literal("ITGP")
		Info=pp.OneOrMore(pp.CharsNotIn('\n')).setParseAction(lambda t : t[0].split())
		Entry=pp.dictOf(Hostname,pp.Group(Mode+pp.Optional(Info,default=None)))
		All_tsk=Entry.parseFile(filename).asDict()
		return(All_tsk)

		
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-d", "--db",action="store",default=DEFAULT_DB,help="db tsk",required=False)
	parser.add_argument("-p", "--printing",action="store_true",help=argparse.SUPPRESS,required=False)
	parser.add_argument("--element",action="store",help=argparse.SUPPRESS,required=False)
	group.add_argument("-s", "--save",action="store",help='Sauvegarde dans le fichier',required=False)
	parser.add_argument('-e',"--equipement",action="store",help='Chercher les u/p pour un equipement',required=False)
	parser.add_argument("--add",action="store",help='add a p type',required=False)
	parser.add_argument("--del",dest="delete",action="store",help='delete a p type',required=False)
	parser.add_argument("--login",action="store_true",help='get login only',required=False)
	
	args = parser.parse_args()
	
	if args.login and not args.element:
		raise argparse.ArgumentError(None,'--element  is manadatory with --login ')
	
	if args.db:
		A=secSbe(args.db)
	else:
		A=secSbe()
		
	if args.add:
		A.setNewPass(args.add)
		if args.db:
			A.save(args.db)
		
	if args.delete:
		A.deletePwd(args.delete)
		if args.db:
			A.save(args.db)
			
	if args.save:
		A.save(args.save)
		
	if args.printing:
		if not args.element:
			A.pri()
		elif args.element=='tacacs':
			if args.login:
				print(DEFAULT_LOGIN)
			else:
				print(A.tac)
		elif args.element=='windows':
			if args.login:
				print(DEFAULT_LOGIN)
			else:
				print(A.win)
		elif args.element:
			if args.login:
				if isinstance(A[args.element],dict):
					print(A[args.element]['login'])
				else:
					print(DEFAULT_LOGIN)
			else:
				if isinstance(A[args.element],dict):
					print(A[args.element]['passwd'])
				else:
					print(A[args.element])
		
		if args.equipement:
			A.getMode(args.equipement)
			
	if args.equipement:
		A.getMode(args.equipement)
		