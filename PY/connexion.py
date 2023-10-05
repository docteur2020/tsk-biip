#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals

import time
from time import gmtime, strftime , localtime , sleep
import sys
import os
import argparse
import pdb
import re
from io import StringIO 
from io import BytesIO
import pexpect as px
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import pickle
from ipcalc import *
import dns.resolver
import ipaddress
import random
import pprint
from ParsingShow import *
sys.path.append('/home/d83071/py')
from ParseVlanListe import vlan , liste_vlans
from getsec import *
import cache as cc
import yaml
from concurrent.futures import ThreadPoolExecutor , wait , ALL_COMPLETED
#from getIPFromPaer import getIPFromtrace
import functools as ft
import json

PARSER={'MAC':'ParseMacCisco'  , 'DESC':ParseDescriptionCiscoOrNexus ,'VLAN':ParseVlanRun  , 'GETALLROUTE':ParseIpRouteString,'PORTCHANNEL':ParsePortChannelCisco , 'STATUS':ParseStatusCisco ,'SWITCHPORT':ParseSwitchPortString , 'CDPDETAIL':ParseCdpNeighborDetailString , 'TRANSCEIVER':ParseInterfaceTransceiverString , 'GETALLBGP':ParseBgpTableString  , 'GETBGPTABLE':ParseBgpTableString , 'FEX':ParseShFexString ,'VRF':ParseVrf ,'COUNTERERROR': ParseIntCounterError , 'BGPNEIGHBOR': ParseBgpNeighbor}
TSK="/home/d83071/CONNEXION/pass.db"
TMP="/home/d83071/TMP/"
DB_HOSTS="/home/d83071/CONNEXION/Equipement.db"
#REBOND='159.50.29.244'
REBOND='159.50.66.10'
TAG_GETALLVRF="ALLVRF_"
TAG_GETALLNEIGH="ALLNEIGHBOR_"
YAML_ENV="/home/d83071/yaml/DEFAULT_ENV.yml"
ACTION="/home/d83071/yaml/actions.yml"

ParseVrfArista=lambda y: list(json.loads(y)['vrfs'].keys())

def retry(checked_exception: Exception, *, tries: int=4, delay: int=3,
		  backoff: int=2):
	"""
	Retry calling a function

	Arguments:
		checked_exception: the exception to check, may also be a tuple of
						   Exceptions
		tries: number of times to retry <func>
		delay: time in seconds between retries
		backoff: multiplier of <delay> for each retry not used
	"""
	def decorate(func):
		@ft.wraps(func)
		def retrier(*args, **kwargs):
						
			tries=args[0].retry
			print(tries)
			while tries <= 10:
				try:
					return func(*args, **kwargs)
				except checked_exception as e:
					
					args[0].timeout=int(args[0].timeout*1.5)
					print(f'{e} .. retrying in {delay}s')
					args[0].retry+=1
					tries=args[0].retry
					#print(tries)
					time.sleep(delay)

			return func(*args, **kwargs)

		return retrier
	return decorate
	
def connect_parse_with_retry(connex,fct_parsing,retry):
	resultat=None
	try__id=1
	while try__id <= retry:
		try:
			print("Tentative:"+str(try__id))
			resultat=connex.launch_withParser(fct_parsing)
			break;
		except ErrorNeedRetry as error_retry:
			try__id=try__id+1
			print(error_retry)
			connex.rebond.close()

		
	return resultat

class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)
Loader__.add_constructor('!include', Loader__.include)

class CommandNotSupported(ValueError):
	def __init__(self, message):
		super(ValueError, self).__init__(message)

class ActionNotSupported(ValueError):
	def __init__(self, message):
		super(ValueError, self).__init__(message)
		
class ResetError(Exception):
	def __init__(self, message):
		super(ResetError, self).__init__(message)

class ErrorNeedRetry(Exception):
	def __init__(self, message,equipement,commande,repertoire,output,retry,type,commande_en_ligne,status):
		super(ErrorNeedRetry, self).__init__(message)
		self.equipement_to_retry=equipement
		self.commande_to_retry=commande
		self.repertoire_to_retry=repertoire
		self.output_to_retry=output
		self.retry=retry
		self.type_to_retry=type
		self.commande_en_ligne_to_retry=commande_en_ligne
		self.status=status
		self.message=message
		#print(self.__str__())
		
	def __str__(self):
		return(self.message)
		
class ErrorNeedRetryConnexion(Exception):
	def __init__(self, message,ErrorLevel2):
		super(ErrorNeedRetryConnexion, self).__init__(message)
		self.errorLevel2=ErrorLevel2

class ErrorUnknownHostname(Exception):
	def __init__(self, message,hostname):
		super(ErrorUnknownHostname, self).__init__(message)
		self.hostname=hostname
	
class equipement(object):
	"definit un equipement"
	def __init__(self,nom,OS="IOS",IP="0.0.0.0",type="SSH",db=DB_HOSTS):
		"Constructeur"
		self.nom=nom
		self.OS=OS
		self.IP=IP
		if self.IP=="0.0.0.0":
			self.init_from_db(db)
		self.type=type
		self.Vrfs=[]
		self.Neighbors={}
	
	def __str__(self):
		return(self.nom+",OS:"+self.OS+",IP:"+self.IP+",TYPE:"+self.type)
		
	def __eq__(self,other_equipement):
		return(self.nom==other_equipement.nom and self.OS==other_equipement.OS and self.IP==other_equipement.IP and self.type==other_equipement.type)
		
	def init_from_db(self,db_equipement):
		Liste_db_equipements=equipement_connus(db_equipement)
		
		if self.nom in Liste_db_equipements:
			self.OS=Liste_db_equipements[self.nom][0]
			self.IP=Liste_db_equipements[self.nom][1]
			self.type=Liste_db_equipements[self.nom][2]
		else:
			
			while self.nom not in Liste_db_equipements:
				Liste_db_equipements.append_read(self.nom)
			self.OS=Liste_db_equipements[self.nom][0]
			self.IP=Liste_db_equipements[self.nom][1]
			self.type=Liste_db_equipements[self.nom][2]

class equipement_connus(object):
	def __init__(self,db=DB_HOSTS):
		self.liste_equipements={}
		self.db=db
		db_file=open(db,'rb')
		while True:
			try:
				equipement_cur=pickle.load(db_file)
			except EOFError:
				break
			self.liste_equipements[equipement_cur.nom]=((equipement_cur.OS,equipement_cur.IP,equipement_cur.type))
		db_file.close()
		
	def append(self,equipement_,mode=''):

		if equipement_.nom not in self:	
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))
			with open(self.db,"a+b") as db_file:
				pickle.dump(equipement_,db_file)
		elif not mode:
			temp_db_r=[]
		
			with open(self.db,'rb') as db_file_r:
				while True:
					try:
						temp_db_r.append(pickle.load(db_file_r))
					except EOFError:
						break
			equipement_to_change=self.get_obj_equipement(equipement_.nom)
			print(equipement_to_change)
			print(equipement_to_change.nom)
			for indice in range(0,len(temp_db_r),1):
				if temp_db_r[indice] == equipement_to_change:
					del temp_db_r[indice]
					break
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))
			temp_db_r.append(equipement_)
			
			with open(self.db,'wb') as db_file_w:
				db_file_w.seek(0)
				db_file_w.truncate()
				for element in temp_db_r:
					pickle.dump(element,db_file_w)
	
	def suppress(self,equipement_nom):

		if equipement_nom in self:
			temp_db_r=[]
		
			with open(self.db,'rb') as db_file_r:
				while True:
					try:
						temp_db_r.append(pickle.load(db_file_r))
					except EOFError:
						break
						
			equipement_to_suppress=self.get_obj_equipement(equipement_nom)
			for indice in range(0,len(temp_db_r),1):
				if temp_db_r[indice] == equipement_to_suppress:
					del temp_db_r[indice]
					break
			del self.liste_equipements[equipement_nom]
			
			with open(self.db,'wb') as db_file_w:
				db_file_w.seek(0)
				db_file_w.truncate()
				for element in temp_db_r:
					pickle.dump(element,db_file_w)
		else:
			print(u"L'élément "+equipement_nom+u" n'est pas dans la base et ne peut donc être supprimé")
		

			
	def __contains__(self,nom_equipement):

		resultat=True
		try:
			test=self.liste_equipements[nom_equipement]
		except KeyError as E:
			resultat=False
			
		return resultat
		
	def append_read                                                                                                                                                                                                                                                              (self,nom_equipement_):
	
		OS_="NONE"
		TYPE_="NONE"
		domains=[ 'xna.net.intra','fr.net.intra','uk.net.intra','net.intra' ]
		if nom_equipement_ not in self:
			print(u"L'équipement "+nom_equipement_+u" n'est pas connu.")
		else:
			print(u"L'equipement "+nom_equipement_+u" est connu et va être modifier")
		while not ( OS_=="IOS" or OS_=="Nexus" or OS_=="XR" or OS_=="OLD-IOS" or OS_=="ACE" or OS_=="ACI" or OS_=="ACI-APIC" or OS_=="ARISTA"):
			OS_=input("Quel est l'OS [XR|IOS|Nexus|OLD-IOS|ACE|ACI|ACI-APIC|ARISTA](Nexus):")
			if not OS_:
				OS_="Nexus"
		
		test_dns=False
		IP_DEFAULT=None
		for domain__ in domains:
			dns_requete=dns.query.udp(dns.message.make_query(nom_equipement_+'.'+domain__, dns.rdatatype.A, use_edns=0),'159.50.1.17')
			if dns_requete.rcode()==0:
				IP_DEFAULT=dns_requete.answer[0].__str__().split()[4]
				test_dns=True
				break

		test_format_IP=False

		while not test_format_IP:
			if IP_DEFAULT:
				IP_=input('Quel est l\'IP('+IP_DEFAULT+'):')
				if IP_=="":
					IP_=IP_DEFAULT
			else:
				IP_=input('Quel est l\'IP:')
			try:
				ipaddress.ip_address(IP_)
				test_format_IP=True
			except ValueError as E:
				pass
								
		while not ( TYPE_=="TELNET" or TYPE_=="SSH"):
			TYPE_=input("Quel est le type de connexion [TELNET|SSH](SSH):")
			if not TYPE_:
				TYPE_="SSH"
		equipement_=equipement(nom_equipement_,OS_,IP_,TYPE_)	
		if nom_equipement_ not in self:
			with open(self.db,"a+b") as db_file:
				pickle.dump(equipement_,db_file)
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))

		
	def get_obj_equipement(self,nom_equipement):

		try:
			info_equipement_cur=self.liste_equipements[nom_equipement]
			resultat=equipement(nom_equipement,info_equipement_cur[0],info_equipement_cur[1],info_equipement_cur[2])
		except KeyError as E:
			resultat=None
			
		return resultat
	
	def  __getitem__(self,key):
		return self.liste_equipements[key]
		
	def __str__(self):

		resultat=""
		for nom_equipement,info_equipement in self.liste_equipements.items():
			resultat+=nom_equipement+",OS:"+info_equipement[0]+",IP:"+info_equipement[1]+",TYPE:"+info_equipement[2]+'\n'
			
		return resultat

	@staticmethod
	def getOS(hostname,dbHosts=DB_HOSTS):
		Liste_db_equipements=equipement_connus(dbHosts)
		if hostname in Liste_db_equipements:
			hostCur=Liste_db_equipements[hostname]
		else:
			return None
		OS=hostCur[0]
		
		return OS
		
			
			
class connexion(object):
	"lance une connexion automatique avec commande"
	def __init__(self,equipement__,liste_commande,mode="SSH",output="NONE",repertoire="",commande_en_ligne="",retry=0,status="NOT INITIATED",verbose=False,timeout=300,dictData={},noTimestamp=False):
		
		
		self.hostname=equipement__.nom
		self.Equipement=equipement__
		self.commande=liste_commande
		self.mode=mode
		self.resultat=""
		self.resultatByCommand={}
		
			
	
		
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		
		if noTimestamp:
			suffixe_time=""
		self.repertoire=repertoire
		self.retry=retry
		self.retry_delay=1.3
		self._status=status
		self.verbose=verbose
		self.timeout=timeout
		self.tsk=secSbe(TSK)
		
		self.dictData=dictData

		if output=="NONE" and repertoire=="":
			self.output="OUTPUT/"+equipement__.nom+suffixe_time+".log"
		elif output!="" and output!="NONE":
			self.output=output
		elif repertoire:
			if not os.path.exists(repertoire):
				os.makedirs(repertoire)
			self.output=repertoire+"/"+equipement__.nom+suffixe_time+".log"
		else:
			self.output=output
	
		
		self.commande_en_ligne=commande_en_ligne
		#print("\n\n"+retry.__str__()+"=="+self.__str__()+"\n\n")*
		
		self.commande_short=""
		if isinstance(self.commande_en_ligne,str):
			self.commande_short=self.commande_en_ligne
		elif isinstance(self.commande_en_ligne,list):
			try:
				self.commande_short=self.commande_en_ligne[0]+"..."
			except IndexError as E:
				pdb.set_trace()
				print(E)
	
	def __str__(self):
		resultat=""
		if isinstance(self.commande_en_ligne,str):
			resultat=self.Equipement.__str__()+'=='+self.commande_en_ligne
		elif isinstance(self.commande_en_ligne,list):
			resultat=self.Equipement.__str__()+'=='+self.commande_en_ligne[0]+"..."
		else:
			resultat="self.Equipement.__str__()"+'==Unknown'
		return resultat
	
	@property
	def status(self):
		return self._status
		

	@status.setter
	def status(self,new_status):
		self._status=f'{self.Equipement.nom} {new_status}:{self.commande_short} RETRY:{self.retry} TIMEOUT:{self.timeout}'

		
	def launch(self):

		
		if self.get_status() == "NOT INITIATED":
			self.status="RUNNING"

		
		self.print_status()
		
		if self.commande_en_ligne:
			#print("ici")
			self.launch_commande_en_ligne()
		else:
			#print('là')
			self.launch_commandes()	
		
		
	
	@retry(checked_exception=ErrorNeedRetry)
	def launch_commandes(self):
	
		self.rebond=pxssh.pxssh(timeout=self.timeout,maxread=100000,options={'StrictHostKeyChecking':'no'},searchwindowsize=1000,env = {"TERM": "xterm-256color"})
		#self.rebond.delaybeforesend=None
		try:
			print("Debut:")
			#self.rebond.logfile = sys.stdout.buffer
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','[a-zA-Z0-9]#']
			self.rebond.login(REBOND,'ld83071',self.tsk.tac, original_prompt='[$>]',password_regex='(?i)(?:Password:)|(?:passphrase for key)',login_timeout=40,quiet=False)
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.Equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.Equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.Equipement.nom)[0])
			else:
				self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.Equipement.nom)[0]+' '+self.Equipement.nom )

				
			expect_value=self.rebond.expect(['assword','yes','Could not resolve hostname'])
			print("COUCOU:"+expect_value.__str__())
			print(f'expect_value:{expect_value}')
			if expect_value==0:
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==2:
				self.rebond.sendline('exit')
				self.rebond.close()
				self.status="FAILED_UNKNOWN_HOST"
				raise ErrorUnknownHostname(self.status,self.Equipement.nom)
			else:
				os.exit(4)
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			try:
			
				fichier_commande=open(self.commande,"r")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
			try:
				fichier_output=open(self.output,"w+")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
			for ligne in fichier_commande:
				timeoutCur=self.timeout
				if 'timeout' in self.dictData:
					if isinstance(self.dictData['timeout'],dict):
						if ligne.strip() in self.dictData['timeout']:
							timeoutCur=self.dictData['timeout'][ligne.strip()]
					else:
						timeoutCur=int(self.dictData['timeout'])
				else:
					timeoutCur=self.timeout
				self.rebond.sendline(ligne.strip())
				self.rebond.expect(regex_match,timeout=timeoutCur)
				self.resultatByCommand[ligne.strip()]=self.rebond.before.decode()
				print("LIGNE:"+ligne)
				
			fichier_output.write(data_output.getvalue().decode('UTF-8'))
			self.resultat=data_output.getvalue().decode('UTF-8')
			time.sleep(1)
			self.rebond.sendline('exit')
			self.rebond.close()
			fichier_output.close()
			self.status="DONE"
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"
			print(str(e))
			

			print(str(e))
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED pexpect failed on login:"+str(ep)+'=='+self.Equipement.__str__()+'=='+self.commande_short
			print(str(ep))

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
		except ResetError as E:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.Equipement.__str__()+'=='+self.commande_short
			print(E)

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
		except exceptions.TIMEOUT:
			print("Timeout...")

			self.status="FAILED:"+"TIMEOUT"+'=='+self.Equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			


	@retry(checked_exception=ErrorNeedRetry)		
	def launch_withParser(self,parser_fct):
		Resultat=None
		self.rebond=pxssh.pxssh(timeout=self.timeout,maxread=100000,options={'StrictHostKeyChecking':'no'},searchwindowsize=1000,env = {"TERM": "xterm-256color"})
		try:
			print(u"Parsing "+self.Equipement.nom+" Method:"+parser_fct.__name__)
			#self.rebond.logfile = sys.stdout.buffer
			#regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+>','\r[a-zA-Z]\\S+>,"[a-zA-Z]#"']
			regex_match=["(\n|\r)[^\r\n#]+[#]\s*$","(\n|\r)[^\r\n#>]+[#>]\s*$",'\r\n[^\r\n#]+[#]$','\r\n[^\r\n>]+[>]$','\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+>"]
			self.rebond.login(REBOND,'ld83071',self.tsk.tac,original_prompt='[$>]', password_regex='(?i)(?:[Pp]assword:)|(?:passphrase for key)',login_timeout=40,quiet=False)
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[>#$]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.Equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.Equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.Equipement.nom)[0])
			else:
				self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.Equipement.nom)[0]+' '+self.Equipement.nom )
			expect_value=self.rebond.expect(['assword:','yes'])
			#print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				param_login=self.tsk.getMode(self.Equipement.nom)[1]
				loginCur=param_login
				if isinstance(param_login,dict):
					loginCur=param_login['login']
					passwdCur=param_login['passwd']
				else:
					passwdCur=param_login
				self.rebond.sendline(passwdCur)
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			else:
				os.exit(4)
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			
			if self.commande_en_ligne:
				if isinstance(self.commande_en_ligne,str):
					self.rebond.sendline(self.commande_en_ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
					self.resultatByCommand[self.commande_en_ligne.strip()]=self.rebond.before.decode().replace(self.commande_en_ligne,'')
				elif isinstance(self.commande_en_ligne,list):
					for commande_str in self.commande_en_ligne:
						self.rebond.sendline(commande_str)
						self.rebond.expect(regex_match,timeout=self.timeout)
						self.resultatByCommand[commande_str.strip()]=self.rebond.before.decode().replace(commande_str,'')
			else:
				for ligne in fichier_commande:
					self.rebond.sendline(ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
					self.resultatByCommand[ligne.strip()]=self.rebond.before.decode().replace(ligne.strip(),'')
					print("LIGNE:"+ligne)
				
	
			try:
				if isinstance(self.commande_en_ligne,str):
					if re.search('json',self.commande_en_ligne):
						self.resultat=data_output.getvalue().decode('UTF-8')
						outputRaw=self.resultat.replace(self.commande_en_ligne,'')
						suffixeRaw=outputRaw.split('}')[-1]
						finalOuputRaw=outputRaw.replace(suffixeRaw,'').strip()
						Resultat=parser_fct(finalOuputRaw)
					else:
						self.resultat=data_output.getvalue().decode('UTF-8')
						Resultat=parser_fct(self.resultat)
				else:
					self.resultat=data_output.getvalue().decode('UTF-8')
					Resultat=parser_fct(data_output.getvalue().decode('UTF-8'))
			except UnicodeDecodeError as e:
				self.resultat=data_output.getvalue().decode('ISO-8859-1')
				Resultat=parser_fct(data_output.getvalue().decode('ISO-8859-1'))
			
			with open(self.output,"w+") as fichier_output:
				try:
					fichier_output.write(data_output.getvalue().decode('UTF-8'))
				except UnicodeDecodeError as e:
					fichier_output.write(data_output.getvalue().decode('ISO-8859-1'))
				
			self.rebond.sendline('exit')
			self.rebond.close()
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)

			print(str(e))
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED pexpect failed on login:"+str(ep)+'=='+self.Equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)

			print(str(ep))
		except ResetError:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.Equipement.__str__()+'=='+self.commande_short

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			
		except exceptions.TIMEOUT:
			print("Timeout...")
			self.status="FAILED:"+"TIMEOUT"+'=='+self.Equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)



		return Resultat

	@retry(checked_exception=ErrorNeedRetry)		
	def launch_withJsonParser(self):
		Resultat=None
		self.rebond=pxssh.pxssh(timeout=self.timeout,maxread=100000,options={'StrictHostKeyChecking':'no'},searchwindowsize=1000,env = {"TERM": "xterm-256color"})
		try:
			print(u"Parsing "+self.Equipement.nom+" Method: default json")
			#self.rebond.logfile = sys.stdout.buffer
			#regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+>','\r[a-zA-Z]\\S+>,"[a-zA-Z]#"']
			regex_match=["(\n|\r)[^\r\n#$]+[#$]\s*$","(\n|\r)[^\r\n#$>]+[#$>]\s*$",'\r\n[^\r\n#$]+[#$]$','\r\n[^\r\n>$]+[>$]$','\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+>"]
			self.rebond.login(REBOND,'ld83071',self.tsk.tac,original_prompt='[$>]', password_regex='(?i)(?:[Pp]assword:)|(?:passphrase for key)',login_timeout=40,quiet=False)
			self.rebond.PROMPT=r"\r\n[^\r\n#]+[>#]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.Equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.Equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.Equipement.nom)[0])
			else:
				self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.Equipement.nom)[0]+' '+self.Equipement.nom )
			expect_value=self.rebond.expect(['assword:','yes'])
			#print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			else:
				os.exit(4)
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			
			if self.commande_en_ligne:
				if isinstance(self.commande_en_ligne,str):
					self.rebond.sendline(self.commande_en_ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
					self.resultatByCommand[self.commande_en_ligne.strip()]=self.rebond.before.decode().replace(self.commande_en_ligne,'')
					ResultatRaw=self.rebond.before.decode().replace(self.commande_en_ligne,'')
					self.resultatByCommand[self.commande_en_ligne.strip()]=ResultatRaw
					Resultat=json.loads(ResultatRaw)
				elif isinstance(self.commande_en_ligne,list):
					Resultat={}
					for commande_str in self.commande_en_ligne:
						self.rebond.sendline(commande_str)
						self.rebond.expect(regex_match,timeout=self.timeout)
						ResultatRaw=self.rebond.before.decode().replace(commande_str,'')
						self.resultatByCommand[commande_str.strip()]=ResultatRaw
						ResultatCur=json.loads(ResultatRaw)
						Resultat[commande_str.strip()]=ResultatCur
			else:
				for ligne in fichier_commande:
					self.rebond.sendline(ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
					self.resultatByCommand[ligne.strip()]=self.rebond.before.decode().replace(ligne.strip(),'')
					print("LIGNE:"+ligne)
				
	
			try:
				self.resultat=data_output.getvalue().decode('UTF-8')
				#Resultat=parser_fct(data_output.getvalue().decode('UTF-8'))
			except UnicodeDecodeError as e:
				self.resultat=data_output.getvalue().decode('ISO-8859-1')
				#Resultat=parser_fct(data_output.getvalue().decode('ISO-8859-1'))
			
			with open(self.output,"w+") as fichier_output:
				try:
					fichier_output.write(data_output.getvalue().decode('UTF-8'))
				except UnicodeDecodeError as e:
					fichier_output.write(data_output.getvalue().decode('ISO-8859-1'))
				
			self.rebond.sendline('exit')
			self.rebond.close()
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)

			print(str(e))
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED pexpect failed on login:"+str(ep)+'=='+self.Equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)

			print(str(ep))
		except ResetError:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.Equipement.__str__()+'=='+self.commande_short

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			
		except exceptions.TIMEOUT:
			print("Timeout...")
			self.status="FAILED:"+"TIMEOUT"+'=='+self.Equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)



		return Resultat
		
	def rebond_con(self,login,passwd,bastion=REBOND,verbose=False):
		try:
			child=px.spawn(f'ssh -l {login} {bastion}',timeout=self.timeout)
			if verbose:
				child.logfile = sys.stdout.buffer
			child.expect(['[Pp]assword:'])
			child.sendline(f'{passwd}')
			child.expect(['>','$'])
		except Exception as E: 
			#print('ERROR')
			print(f'connection to {REBOND} failed, ...')
			print(type(E))
			print(E)

		
		return child
	
	@retry(checked_exception=ErrorNeedRetry)	
	def launch_commande_en_ligne(self):

		#self.rebond=pxssh.pxssh(timeout=self.timeout,maxread=100000,options={'StrictHostKeyChecking':'no'},searchwindowsize=1000)
		
		try:

			regex_match=["(\n|\r)[^\r\n#$]+[#$]\s*$","(\n|\r)[^\r\n#$>]+[#$>]\s*$",'\r\n[^\r\n#$]+[#$]$','\r\n[^\r\n>$]+[>$]$','\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+>"]
			regex_match=['\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+>"]

			self.rebond=self.rebond_con('ld83071',self.tsk.tac,REBOND,self.verbose)
			self.rebond.PROMPT=r"\r\n[^\r\n#>]+[#>]$"
			#self.rebond.delaybeforesend=None
			
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.Equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.Equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.Equipement.nom)[0])
			else:
				try:
					self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.Equipement.nom)[0]+'          '+self.Equipement.nom )
				except pxssh.ExceptionPxssh as e:
					print("pxssh failed on login")
					self.status="FAILED SSH:"+str(e)+'=='+self.Equipement.__str__()+'=='+self.commande_en_ligne
					print(str(e))
			
				except ExceptionPexpect as ep:
					print("pxssh failed on login")
					self.status="FAILED SSH:"+str(ep)+'=='+self.Equipement.__str__()+'=='+self.commande_en_ligne
					print(str(ep))
			
				except exceptions.TIMEOUT:
					print("Timeout...")
					self.status="FAILED SSH:"+"TIMEOUT"+'=='+self.Equipement.__str__()+'=='+self.commande_en_ligne
			expect_value=self.rebond.expect(['assword:','yes','Connection reset by peer','Could not resolve hostname'],timeout=self.timeout)
			print("COUCOU4123:"+expect_value.__str__())
			infoLogin=self.tsk.getMode(self.Equipement.nom)[1]
			if isinstance(infoLogin,dict):
				passCur=infoLogin['passwd']
			else:
				passCur=infoLogin
			if expect_value==0:
				self.rebond.sendline(passCur+'\r')
				self.rebond.expect('[#>]')
				self.rebond.sendline("terminal length 0")
				expect_value2=self.rebond.expect(regex_match)
				#print("COUCOU:"+expect_value2.__str__())
				if expect_value2==3:
					self.rebond.sendline("en")
					self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.Equipement.nom)[1])
				#print('ici')
				self.rebond.expect(regex_match)
				#print('la')
				self.rebond.sendline("terminal length 0")
				expect_value2=self.rebond.expect(regex_match)
				if expect_value2==3:
					self.rebond.sendline("en")
					self.rebond.expect(regex_match)				
			elif expect_value==2:
				self.rebond.close()
				print("!!! Connection reset by peer !!!")
				raise ResetError("!!! SSH Reset Error !!!")
				return
			elif expect_value==3:
				self.rebond.sendline('exit')
				self.rebond.close()
				self.status="FAILED_UNKNOWN_HOST"
				raise ErrorUnknownHostname(self.status,self.Equipement.nom)
				return
			else:
				os.exit(4)
				
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$>]$"
			#print("PROMPT:"+self.rebond.PROMPT)
			try:
				fichier_output=open(self.output,"w+")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
	
			if isinstance(self.commande_en_ligne,str):
				self.rebond.sendline(self.commande_en_ligne)
				self.rebond.expect(regex_match,timeout=self.timeout)
				self.resultatByCommand[self.commande_en_ligne.strip()]=self.rebond.before.decode().replace(self.commande_en_ligne.strip(),'')
			elif isinstance(self.commande_en_ligne,list):
				regex_match=['\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+>","(\n|\r)\\s+[a-zA-Z]\\S+#"]
				for commande_str in self.commande_en_ligne:
					timeoutCur=self.timeout
					if 'timeout' in self.dictData:
						if isinstance(self.dictData['timeout'],dict):
							if commande_str in self.dictData['timeout']:
								timeoutCur=self.dictData['timeout'][commande_str]
								print(f'timeout temporarily changed for {self.Equipement.nom} {commande_str} {timeoutCur} to {self.timeout}')
					#print(f'commande:{commande_str}')
					self.rebond.sendline(commande_str)

					#print('ici')
					self.rebond.expect(regex_match,timeout=timeoutCur)
					#print('la')

					#print('toto')
					self.resultatByCommand[commande_str.strip()]=self.rebond.before.decode().replace(commande_str.strip(),'')
					#print('titi')
			else:
				print("Erreur sur la variable commande")
				print(type(self.commande_en_ligne))
				sys.exit(8)
			print("COUCOU FFFF:")
			
			
			fichier_output.write(data_output.getvalue().decode('UTF-8'))
			self.resultat=data_output.getvalue().decode('UTF-8')
			self.rebond.sendline('exit')
			self.rebond.close()
			fichier_output.close()
			self.status="DONE"
			
			
		except pxssh.ExceptionPxssh as e:
			print("pexpect failed on login 2")
			self.set_status(self.commande_short,"FAILED")
			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError("Coucou")

			print(str(e))
			
		except ExceptionPexpect as ep:
			print("pexpect failed on login 4")
			self.set_status(self.commande_short,"FAILED")
			#print(ep)
			#print(type(ep))

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status)
		except ResetError as E:
			print(E)
			self.set_status(self.commande_short,"FAILED")

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError("Coucou")
		except exceptions.TIMEOUT:
			print("Timeout...")
			self.set_status(self.commande_short,"FAILED")

			raise ErrorNeedRetry(self.status,self.Equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError("Coucou")
		except AssertionError as E:
			message=E.__str__()
			print("All...")
			raise E

		
	def set_status(self,commande,status):

		self.status=status
		
	def get_status(self):
		return self.status
		
	def print_status(self):
		print(self.status)

class connexions(object):
	"lance une connexion automatique avec commande"
	def __init__(self,fichier_liste_equipement,known_equipments,liste_commandes="shrun.txt",repertoire="",commande_en_ligne="",action="",suffixe="",liste_equipement=None,timeout=300,verbose=False,format=False,Yaml=False,maxCurconn=12,dictData=None,listData=None,noTimestamp=False,caching=False,renew=False):

		self.filename=fichier_liste_equipement
		self.liste_equipement=[]
		self.connexion_liste=[]
		self.known_equipments=known_equipments
		self.commandes=liste_commandes
		self.repertoire=repertoire
		self.commande_en_ligne=commande_en_ligne
		self.action=action
		self.start_test=False
		self.nb_connexion=0
		self.retry_delay=1
		self.status_all={}
		self.liste_thread_to_wait=[]
		self.suffixe=suffixe
		self.timeout=timeout
		self.verbose=verbose
		self.format=format
		self.Yaml=Yaml
		self.maxCurconn=maxCurconn
		self.queueGrp=[]
		self.hostsCur=[]
		self.dictData=dictData
		self.listData=listData
		self.noTimestamp=noTimestamp
		self.caching=caching
		self.renew=renew
		step=1
		if not self.action:
			if not liste_equipement and self.format is False and self.Yaml is False and self.dictData is None and self.listData is None:
				with open(fichier_liste_equipement,'r') as file_equipements:
					for ligne in file_equipements:
						nom_equipement=ligne.lower().replace('\n',"").replace('\r',"").replace(' ',"")
	
						if nom_equipement in self.known_equipments:
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						else:
							while nom_equipement not in self.known_equipments:
								self.known_equipments.append_read(nom_equipement)
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						if(commande_en_ligne):
							self.connexion_liste.append(connexion(equipement_cur,self.commandes,repertoire=self.repertoire,commande_en_ligne=self.commande_en_ligne,timeout=self.timeout,verbose=self.verbose,noTimestamp=self.noTimestamp))
						else:
							self.connexion_liste.append(connexion(equipement_cur,self.commandes,repertoire=self.repertoire,timeout=self.timeout,verbose=self.verbose,noTimestamp=self.noTimestamp))
						step+=1
			elif not liste_equipement and self.format is True:
				with open(fichier_liste_equipement,'r') as file_equipements_format:
					for ligne in file_equipements_format:
						tab_ligne=ligne.split(';')
						nom_equipement=tab_ligne[0].lower().replace('\n',"").replace('\r',"").replace(' ',"")
						commandes_cur=tab_ligne[1].split(',')
						
						if nom_equipement in self.known_equipments:
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						else:
							while nom_equipement not in self.known_equipments:
								self.known_equipments.append_read(nom_equipement)
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						
						self.connexion_liste.append(connexion(equipement_cur,commandes_cur,repertoire=self.repertoire,commande_en_ligne=commandes_cur,timeout=self.timeout,verbose=self.verbose))
						step+=1
			elif not liste_equipement and self.Yaml:
				with open(fichier_liste_equipement, 'r') as yml__:
					dataYaml=yaml.load(yml__,Loader__)
					
					if isinstance(dataYaml,dict):
						self.initConnexionsFromDict(dataYaml,verbose=self.verbose,caching=self.caching,renew=self.renew)
					elif isinstance(dataYaml,list):
						self.initConnexionsFromList(dataYaml,verbose=self.verbose,caching=self.caching,renew=self.renew)
						

			elif not liste_equipement and self.dictData:
				self.initConnexionsFromDict(self.dictData,verbose=self.verbose,caching=self.caching,renew=self.renew)
				
			elif not liste_equipement and self.listData:
				self.initConnexionsFromList(self.listData,verbose=self.verbose,caching=self.caching,renew=self.renew)

			else:
				for nom_equipement_element in liste_equipement.split(":"):
					nom_equipement=nom_equipement_element.lower().replace('\n',"").replace('\r',"").replace(' ',"")
					
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					if(commande_en_ligne):
						self.connexion_liste.append(connexion(equipement_cur,self.commandes,repertoire=self.repertoire,commande_en_ligne=self.commande_en_ligne,timeout=self.timeout,verbose=self.verbose,noTimestamp=self.noTimestamp))
					else:
						self.connexion_liste.append(connexion(equipement_cur,self.commandes,repertoire=self.repertoire,timeout=self.timeout,verbose=self.verbose,noTimestamp=self.noTimestamp))
					step+=1
		elif self.action=='VRF':
			with open(fichier_liste_equipement,'r') as file_equipements_vrf:
				for ligne in file_equipements_vrf:
					tab_ligne=ligne.split()
					nom_equipement=tab_ligne[0]
					OS=tab_ligne[1]
					vrf=tab_ligne[2:]
				
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					OS_cur=self.known_equipments.liste_equipements[nom_equipement][0]
					type_cur=self.known_equipments.liste_equipements[nom_equipement][2]
					for vrf_cur in vrf:
						
						if OS_cur=='IOS' or OS_cur=="OLD-IOS":
							commande_cur='sh ip route vrf '+vrf_cur
						elif OS_cur=='Nexus':
							commande_cur='sh ip route vrf '+vrf_cur
						elif OS_cur=='XR':
							commande_cur='sh route vrf '+vrf_cur
						else:
							sys.stderr.write('type OS '+OS_cur+' non pris en charge')
							os.exit('6')
						repertoire_cur=self.repertoire+'/'+vrf_cur
						if not os.path.exists(repertoire_cur):
							os.makedirs(repertoire_cur)
						if suffixe:
							output_cur=repertoire_cur+"/"+suffixe+nom_equipement.lower()+".log"
						else:
							output_cur=repertoire_cur+"/"+nom_equipement.lower()+".log"
						self.connexion_liste.append(connexion(equipement_cur,liste_commandes,type_cur,output_cur,repertoire_cur,commande_cur,timeout=self.timeout,verbose=self.verbose))
						step+=1
	
	
		elif self.action=='MAC' or self.action=='DESC' or self.action=='GETALLARP' or re.search('^VLAN:',self.action) or self.action=='PORTCHANNEL' or self.action=='STATUS' or self.action=='SWITCHPORT' or self.action=='GETALLROUTE' or self.action=='CDPDETAIL' or self.action=='TRANSCEIVER' or self.action=='GETALLBGP' or self.action=='GETBGPTABLE' or self.action=='FEX' or self.action=='LLDPDETAIL' or self.action=='COUNTERERROR' or self.action=='RUN' or self.action=='VPC' or self.action=='MLAG':
			liste_equipement__=[]
			if not liste_equipement:
				with open(fichier_liste_equipement,'r') as file_equipements:
					liste_equipement__=file_equipements.read().splitlines()
			else:
				liste_equipement__=liste_equipement.split(":")
				
			step=1	
			for ligne in liste_equipement__:
				nom_equipement=ligne.lower().replace('\n',"").replace('\r',"").replace(' ',"")
				
				if nom_equipement in self.known_equipments:
					equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
					self.liste_equipement.append(equipement_cur)
				else:
					while nom_equipement not in self.known_equipments:
						self.known_equipments.append_read(nom_equipement)
					equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
					self.liste_equipement.append(equipement_cur)
				OS_cur=self.known_equipments.liste_equipements[nom_equipement][0]
				type_cur=self.known_equipments.liste_equipements[nom_equipement][2]
				if self.action=='MAC':
					if OS_cur=='IOS':
						commande_cur='sh mac address-table'
					elif OS_cur=='Nexus':
						commande_cur='sh mac address-table'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh mac-address-table'
					elif OS_cur=='ARISTA':
						commande_cur='sh mac address-table'
					else:
						sys.stderr.write('type OS '+OS_cur+' non pris en charge')
						sys.exit('6')
				elif self.action=='DESC':
					commande_cur='sh interface description'

				elif self.action=='VPC':
					commande_cur='sh vpc'

				elif self.action=='MLAG':
					commande_cur='sh mlag'
					
				elif re.search('^VLAN:',self.action):
					liste_vlan=self.action.split(":")[1]
					if OS_cur=='OLD-IOS':
						commande_cur=[]
						liste_vlan_cur=liste_vlans(liste_vlan)
						liste_vlan_cur_long=liste_vlan_cur.explode()
						for vlan_cur in liste_vlan_cur_long:
							commande_cur.append('sh vlan id '+vlan_cur)
					else:
						commande_cur='sh vlan id '+liste_vlan
						
				elif self.action=='GETALLARP':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						TAG_VRF=TAG_GETALLVRF+equipement_cur.nom.upper()
						cacheCurVrf=cc.Cache(TAG_VRF)
						if not args.cache:
							con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
							equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)

							cacheCurVrf.save(equipement_cur.Vrfs)
						else:
							if cacheCurVrf.isOK():
								print('Cache is used, timestamp:',cacheCurVrf.get_timestamp())
								equipement_cur.Vrfs=cacheCurVrf.getValue()
							else:
								con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
								cacheCurVrf.save(equipement_cur.Vrfs)
						
						commande_cur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip arp")
							
					
						
					elif OS_cur=='Nexus':
						TAG_VRF=TAG_GETALLVRF+equipement_cur.nom.upper()
						cacheCurVrf=cc.Cache(TAG_VRF)
						if not args.cache:
							con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
							equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)

							cacheCurVrf.save(equipement_cur.Vrfs)
						else:
							if cacheCurVrf.isOK():
								print('Cache is used, timestamp:',cacheCurVrf.get_timestamp())
								equipement_cur.Vrfs=cacheCurVrf.getValue()
							else:
								con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
								cacheCurVrf.save(equipement_cur.Vrfs)
						commande_cur='sh ip arp vrf all'
						commande_cur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						'stop'

					elif OS_cur=='ARISTA':
						TAG_VRF=TAG_GETALLVRF+equipement_cur.nom.upper()
						cacheCurVrf=cc.Cache(TAG_VRF)
						ParserCur=lambda y: list(json.loads(y)['vrfs'].keys())
						if not args.cache:
							con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf | json",timeout=self.timeout,verbose=self.verbose)
							equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParserCur,3)

							cacheCurVrf.save(equipement_cur.Vrfs)
						else:
							if cacheCurVrf.isOK():
								print('Cache is used, timestamp:',cacheCurVrf.get_timestamp())
								equipement_cur.Vrfs=cacheCurVrf.getValue()
							else:
								con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParserCur,3)
								cacheCurVrf.save(equipement_cur.Vrfs)
						commande_cur='sh ip arp vrf all'
						commande_cur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						
					elif OS_cur=='XR':
						commande_cur='sh arp vrf all'
						
				elif self.action=='GETALLROUTE':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":

						con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip route")
						
					elif OS_cur=='Nexus':
						if not args.cache:
							con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
							equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
							TAG_VRF=TAG_GETALLVRF+equipement_cur.nom.upper()
							cacheCurVrf=cc.Cache(TAG_VRF)
							cacheCurVrf.save(equipement_cur.Vrfs)
						else:
							TAG_VRF=TAG_GETALLVRF+equipement_cur.nom.upper()
							cacheCurVrf=cc.Cache(TAG_VRF)
							if cacheCurVrf.isOK():
								print('Cache is used, timestamp:',cacheCurVrf.get_timestamp())
								equipement_cur.Vrfs=cacheCurVrf.getValue()
							else:
								con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
								cacheCurVrf.save(equipement_cur.Vrfs)
						commande_cur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip route")
						
						with open(f'/home/d83071/TMP/ROUTE/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))					
						
					elif OS_cur=='XR':
						commande_cur=['sh ip route vrf all','sh route']
						
						with open(f'/home/d83071/TMP/ROUTE/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))	

					elif OS_cur=='ARISTA':
						commande_cur=['sh ip route vrf all','sh route']
				elif self.action=='GETALLBGP':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						commande_cur=[]
						tentative=1
						while tentative <=3:
							try:
								con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=con_get_vrf_cur.launch_withParser(ParseVrf)
								break
							except ErrorNeedRetry as error_retry:
								tentative=tentative+1
								print(error_retry)
								print("Tentative:"+str(tentative))
								pass

						
						commande_bgp_sum=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in  equipement_cur.Vrfs ]
						commande_bgp_sum.append("sh ip bgp summary")
						con_get_neigh_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getbgpneigh_"+nom_equipement.lower()+".log","TMP",commande_bgp_sum,timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							if Vrf__ !='GRT':
								commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" summary")
								commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__)
								if dict_neighbor[Vrf__]:
									for Neigh__ in dict_neighbor[Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
												commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
							else:
								commande_cur.append("sh ip bgp summary")
								commande_cur.append("sh ip bgp ")
								if dict_neighbor[Vrf__]:
									for Neigh__ in dict_neighbor[Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_cur.append("sh ip bgp  neighbor "+Neigh__[0]+" routes")
												commande_cur.append("sh ip bgp  neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
						print(commande_cur)
						
						
					elif OS_cur=='Nexus':
						commande_cur=[]
						con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=con_get_vrf_cur.launch_withParser(ParseVrf)
						commande_bgp_sum=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  equipement_cur.Vrfs ]
						con_get_neigh_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getbgpneigh_"+nom_equipement.lower()+".log","TMP",commande_bgp_sum,timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh ip bgp vrf "+Vrf__+" summary")
							commande_cur.append("sh ip bgp vrf "+Vrf__)
							if dict_neighbor[Vrf__]:
								for Neigh__ in dict_neighbor[Vrf__]:
									try:
										if Neigh__[2].isdigit():
											commande_cur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
											commande_cur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
									except TypeError:
										pass
						print(commande_cur)
						with open(f'/home/d83071/TMP/BGP/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))
										
					elif OS_cur=='XR':
						commande_cur=[]
						con_get_all_neighbor=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallneigh_"+nom_equipement.lower()+".log","TMP",'sh bgp vrf all summary',timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_all_neighbor.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh bgp vrf "+Vrf__+" summary")
							commande_cur.append("sh bgp vrf "+Vrf__)
							if dict_neighbor[Vrf__]:
								for Neigh__ in dict_neighbor[Vrf__]:
									if Neigh__[2].isdigit():
										commande_cur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
										commande_cur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
						#print(commande_cur)
						with open(f'/home/d83071/TMP/BGP/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))						
						
				elif self.action=='GETBGPTABLE':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip bgp vpnv4 vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip bgp")
						print(equipement_cur.nom)
						print("\n".join(commande_cur))
						with open(f'/home/d83071/TMP/BGPTABLE/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))						
					elif OS_cur=='Nexus':
						con_get_vrf_cur=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip bgp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						print(equipement_cur.nom)
						print("\n".join(commande_cur))
						with open(f'/home/d83071/TMP/BGPTABLE/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))		
										
					elif OS_cur=='XR':
						commande_cur=[]
						con_get_all_neighbor=connexion(equipement_cur,liste_commandes,type_cur,"TMP/"+"_getallneigh_"+nom_equipement.lower()+".log","TMP",'sh bgp vrf all summary',timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_all_neighbor.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh bgp vrf "+Vrf__)
						for str__ in commande_cur:
							print(str__)
						with open(f'/home/d83071/TMP/BGPTABLE/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
							file_w.write(" \n".join(commande_cur))							
							
				elif self.action=='PORTCHANNEL':
					if OS_cur=='IOS':
						commande_cur='sh etherchannel summary'
					elif OS_cur=='Nexus':
						commande_cur='sh port-channel summary'
					elif OS_cur=='ARISTA':
						commande_cur='sh port-channel summary'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh etherchannel summary'
					elif OS_cur=='XR':
						commande_cur='sh bundle'
						
				elif self.action=='STATUS':
					if OS_cur=='IOS':
						commande_cur='sh interface status'
					elif OS_cur=='Nexus':
						commande_cur='sh interface status'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh interface status'
					elif OS_cur=='ARISTA':
						commande_cur='sh interface status'
					elif OS_cur=='XR':
						commande_cur='sh interface brief'
				
				elif self.action=='SWITCHPORT':
					if OS_cur=='IOS':
						commande_cur='sh interface switchport'
					elif OS_cur=='Nexus':
						commande_cur='sh interface switchport'
					elif OS_cur=='ARISTA':
						commande_cur='sh interface switchport'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh interface switchport'

				elif self.action=='CDPDETAIL':
					commande_cur='sh cdp neighbor detail'
					
				elif self.action=='TRANSCEIVER':
					commande_cur='sh interface transceiver'
				
				elif self.action=='LLDPDETAIL':
					commande_cur='sh lldp neighbor detail'
					
				elif self.action=='COUNTERERROR':
					commande_cur='sh interface counter error'
					
				elif self.action=='RUN':
					commande_cur='sh run'					
				elif self.action=='FEX':
					if OS_cur=='Nexus':
						commande_cur='sh fex'
						
					else:
						commande_cur='! NON SUPPORTE'
						raise CommandNotSupported("Action:FEX "+nom_equipement+" "+OS_cur) from ValueError(OS_cur)
				
				repertoire_cur=self.repertoire
				if not os.path.exists(repertoire_cur):
					os.makedirs(repertoire_cur)
				if self.suffixe:
					output_cur=repertoire_cur+"/"+self.suffixe+nom_equipement.lower()+".log"
				else:
					output_cur=repertoire_cur+"/"+nom_equipement.lower()+".log"
				self.connexion_liste.append(connexion(equipement_cur,liste_commandes,type_cur,output_cur,repertoire_cur,commande_cur,timeout=self.timeout,verbose=self.verbose))
				step+=1
		random.shuffle(self.connexion_liste)
		self.init_all_status()
		
		
	

	def __iter__(self):
		return iter(self.connexion_liste)
		
	def launch_commandes(self):


		self.fs=[]
		mCon={}
		
		with ThreadPoolExecutor(max_workers=self.maxCurconn) as e:
			for connexion_cur in self.connexion_liste:
				self.fs.append(e.submit(connexion_cur.launch))
				
			if self.verbose:
				while True:
					all_finished = True
				
					print("\nHave the workers finished?")
				
					for i, future in enumerate(self.fs):
						if future.done():
							print(f"Task {i} has finished")
						else:
							all_finished = False
							print(f"Task {i} is running...")
				
					if all_finished:
						break
				
					sleep(10)			
				

		
	def get_fin(self):
		result=True
		for connexion_cur in self.connexion_liste:
			if connexion_cur.is_alive():
				result=False
				
		for connexion_cur in self.liste_thread_to_wait:
			if connexion_cur.is_alive():
				result=False
				
		return result
	
	def isStarted(self):
		return self.start_test
			
	def print_status(self):
		for connexion_cur in self.connexion_liste:
			print(connexion_cur.equipement.nom+" "+self.action+":"+connexion_cur.status+" "+connexion_cur.commande_en_ligne)
			

				
	def attendre_fin(self):
		print('finished')

			
	def init_all_status(self):
		for connexion_cur in self.connexion_liste:
			if isinstance(connexion_cur.commande_en_ligne,str):
				self.status_all[connexion_cur.Equipement.nom,connexion_cur.commande_en_ligne]="NOT INITIATED"
			elif isinstance(connexion_cur.commande_en_ligne,list):
				self.status_all[connexion_cur.Equipement.nom,connexion_cur.commande_en_ligne[0]]="NOT INITIATED"
			
	def set_status(self,equipement,commande,status):
		if isinstance(commande,str):
			self.status_all[equipement,commande]=status
		elif isinstance(commande,list):
			self.status_all[equipement,commande[0]]=status
		
	def get_status(self,equipement,commande):
		resultat=""
		if isinstance(commande,str):
			resultat=self.status_all[equipement,commande]
		elif isinstance(commande,list):
			resultat=self.status_all[equipement,commande[0]]
		#print(resultat)
		return resultat
		
	def set_status_final(self):
		for connexion_cur in self.connexion_liste:
			if isinstance(connexion_cur.commande_en_ligne,str):
				commande_to_return=connexion_cur.commande_en_ligne
			elif isinstance(connexion_cur.commande_en_ligne,list):
				commande_to_return=connexion_cur.commande_en_ligne[0]+"..."
			else:
				commande_to_return="Something wrong..."

			if "DONE:" not in connexion_cur.status:
				self.status="UNSUCCESS"

	
	def print_status_final(self):
		for connexion_cur in self.connexion_liste:
			try:
				print(connexion_cur.status)
			except ValueError as E:
				print("ERROR GET STATUS")
	
	def runFailedConn(self):
		self.thread_retry=threading.Thread(target=self.worker_connexions_failed)	
		self.thread_retry.start()	

	def initConnexionsFromList(self,listData,verbose=False,caching=False,renew=False):
		step=0
		hostNeedVrf=[]
		hostNeedBgpNeigh=[]
		Vrfs={}
		BgpNeighbors={}
		actions={}
		
		with open(ACTION, 'r') as yml__:
			actions=yaml.load(yml__,Loader__)
		
			
		for entry in listData:
			if 'action' in entry:
				actionCur=entry['action']
				if 'hostname'in entry:
					nom_equipement=entry['hostname']
					equipements=[nom_equipement]	

				
				elif 'environment'in entry:
					envCur=entry['environment']
					equipements=getHostsFromEnv(envCur)
					
				elif 'hostnames' in entry:
					equipements=entry['hostnames']					
					
				for host in equipements:
					if host in self.known_equipments:
						equipement_cur=equipement(host,self.known_equipments.liste_equipements[host][0],self.known_equipments.liste_equipements[host][1],self.known_equipments.liste_equipements[host][2])
					else:
						while host not in self.known_equipments:
							self.known_equipments.append_read(host)
						equipement_cur=equipement(host,self.known_equipments.liste_equipements[host][0],self.known_equipments.liste_equipements[host][1],self.known_equipments.liste_equipements[host][2])
					OSCur=equipement_cur.OS
					
					if actionCur in actions['needVrf'][OSCur]:
						hostNeedVrf.append(host )

					if actionCur in actions['needBgpNeigh'][OSCur]:
						hostNeedBgpNeigh.append(host)				
				
		if hostNeedVrf:
			Vrfs=getVrfsForHostnames(hostNeedVrf,caching=caching,renew=renew,timeout=200,verbose=verbose)	
			
		if hostNeedBgpNeigh:
			BgpNeighbors=getBgpNeighForHostnames(hostNeedBgpNeigh,Vrfs,caching=False,renew=False,timeout=200,verbose=False)
				
		for entry in listData:
			if 'commande' in entry or 'file' in entry or 'configuration_file' in entry:
				if 'hostname'in entry:
					nom_equipement=entry['hostname']
					equipements=[nom_equipement]
					if 'commande' in entry:
						commandes_cur=entry['commande']
					elif 'file' in entry:
						with open(entry['file']) as file_r:
							commandes_cur=file_r.read().split('\n')
					elif 'configuration_file' in entry:
						with open(entry['configuration_file']) as file_r:
							commandes_cur=['conf t']
							commandes_cur+=file_r.read().split('\n')
							commandes_cur.append('end')
				elif 'environment'in entry:
					envCur=entry['environment']
					equipements=getHostsFromEnv(envCur)						
					if 'commande' in entry:
						commandes_cur=entry['commande']
					elif 'file' in entry:
						with open(entry['file']) as file_r:
							commandes_cur=file_r.read().split('\n')
					elif 'configuration_file' in entry:
						with open(entry['configuration_file']) as file_r:
							commandes_cur=['conf t']
							commandes_cur+=file_r.read().split('\n')
							commandes_cur.append('end')
				elif 'hostnames'in entry:
					equipements=entry['hostnames']					
					if 'commande' in entry:
						commandes_cur=entry['commande']
					elif 'file' in entry:
						with open(entry['file']) as file_r:
							commandes_cur=file_r.read().split('\n')
					elif 'configuration_file' in entry:
						with open(entry['configuration_file']) as file_r:
							commandes_cur=['conf t']
							commandes_cur+=file_r.read().split('\n')
							commandes_cur.append('end')					
				if 'directory' in entry:
					repertoireCur=entry['directory']
				else:
					repertoireCur=self.repertoire
			
				if 'sub-directory' in entry:
					repertoireCur=repertoireCur+'/'+entry['sub-directory']
					
				if 'timeout' in entry:
					timeoutCur=entry['timeout']
				else:
					timeoutCur=self.timeout
					
				for nom_equipement	 in equipements:
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

						
						
					try:
						self.connexion_liste.append(connexion(equipement_cur,commandes_cur,repertoire=repertoireCur,commande_en_ligne=commandes_cur,timeout=timeoutCur,verbose=self.verbose))
					except UnboundLocalError:
						pdb.set_trace()
						'stop'
					step+=1
					
			if 'action' in entry:
				actionCur=entry['action']
				if 'hostname'in entry:
					nom_equipement=entry['hostname']
					equipements=[nom_equipement]	
		
				elif 'environment'in entry:
					envCur=entry['environment']
					equipements=getHostsFromEnv(envCur)		

				if 'hostnames'in entry:

					equipements=entry['hostnames']	
					
					
				if 'directory' in entry:
					repertoireCur=entry['directory']
				else:
					repertoireCur=self.repertoire
			
				if 'sub-directory' in entry:
					repertoireCur=repertoireCur+'/'+entry['sub-directory']
					
				if 'timeout' in entry:
					timeoutCur=entry['timeout']
				else:
					timeoutCur=self.timeout
					
				for nom_equipement	 in 	equipements:
					hostnameCur=nom_equipement
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

					OSCur=equipement_cur.OS
					
					if actionCur not in actions['needVrf'][OSCur] and actionCur not in actions['needBgpNeigh'][OSCur]:
						commandeCur=actions['default'][actionCur][OSCur]['commande']
						if isinstance(commandeCur,str):
							commandeCur=[commandeCur]
						self.connexion_liste.append(connexion(equipement_cur,commandeCur,repertoire=repertoireCur,commande_en_ligne=commandeCur,timeout=timeoutCur,verbose=self.verbose))
					else:
						if actionCur=='GETALLROUTE':
							if OSCur=='IOS' or OSCur=="OLD-IOS":
								commandeCur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  Vrfs[hostnameCur] ]
								commandeCur.append("sh ip route")
						
							elif OSCur=='Nexus':
								commandeCur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  Vrfs[hostnameCur] ]
								commandeCur.append("sh ip route")
							
							with open(f'/home/d83071/TMP/ROUTE/CONF/{hostnameCur.upper()}.TXT','w') as file_w:
								file_w.write(" \n".join(commandeCur))	
								
						elif actionCur=='GETALLARP':
							if OSCur=='IOS' or OSCur=="OLD-IOS":
								commandeCur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  Vrfs[hostnameCur] ]
								commandeCur.append("sh ip arp")
									
							
								
							elif OSCur=='Nexus':
								commandeCur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  Vrfs[hostnameCur] ]
								'stop'
		
							elif OSCur=='ARISTA':
								commandeCur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  Vrfs[hostnameCur] ]
								
						
						elif actionCur=='GETALLBGP':
							commandeCur=[]
							if OSCur=='IOS' or OSCur=="OLD-IOS":

								for Vrf__ in BgpNeighbors[hostnameCur]:
									if Vrf__ !='GRT':
										commandeCur.append("sh ip bgp vpnv4 vrf "+Vrf__+" summary")
										commandeCur.append("sh ip bgp vpnv4 vrf "+Vrf__)
										if BgpNeighbors[Vrf__]:
											for Neigh__ in BgpNeighbors[hostnameCur][Vrf__]:
												try:
													if Neigh__[2].isdigit():
														commandeCur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
														commandeCur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
												except TypeError:
													pass
									else:
										commandeCur.append("sh ip bgp summary")
										commandeCur.append("sh ip bgp ")
										if BgpNeighbors[Vrf__]:
											for Neigh__ in BgpNeighbors[hostnameCur][Vrf__]:
												try:
													if Neigh__[2].isdigit():
														commandeCur.append("sh ip bgp  neighbor "+Neigh__[0]+" routes")
														commandeCur.append("sh ip bgp  neighbor "+Neigh__[0]+" advertised-routes")
												except TypeError:
													pass
								print(commandeCur)
								
								
							elif OSCur=='Nexus':
								commandeCur=[]

								for Vrf__ in BgpNeighbors[hostnameCur]:
									commandeCur.append("sh ip bgp vrf "+Vrf__+" summary")
									commandeCur.append("sh ip bgp vrf "+Vrf__)
									if BgpNeighbors[hostnameCur][Vrf__]:
										for Neigh__ in BgpNeighbors[hostnameCur][Vrf__]:
											try:
												if Neigh__[2].isdigit():
													commandeCur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
													commandeCur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
											except TypeError:
												pass
								print(commandeCur)
								with open(f'/home/d83071/TMP/BGP/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
									file_w.write(" \n".join(commandeCur))
												
							elif OSCur=='XR':
								commandeCur=[]
								for Vrf__ in BgpNeighbors[hostnameCur]:
									commandeCur.append("sh bgp vrf "+Vrf__+" summary")
									commandeCur.append("sh bgp vrf "+Vrf__)
									if BgpNeighbors[hostnameCur][Vrf__]:
										for Neigh__ in BgpNeighbors[hostnameCur][Vrf__]:
											if Neigh__[2].isdigit():
												commandeCur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
												commandeCur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
								#print(commande_cur)
								with open(f'/home/d83071/TMP/BGP/CONF/{equipement_cur.nom.upper()}.TXT','w') as file_w:
									file_w.write(" \n".join(commandeCur))	
						if isinstance(commandeCur,str):
							commandeCur=[commandeCur]
							
						if not commandeCur:
							pdb.set_trace()
							'stop'
						self.connexion_liste.append(connexion(equipement_cur,commandeCur,repertoire=repertoireCur,commande_en_ligne=commandeCur,timeout=timeoutCur,verbose=self.verbose))	

						
	def initConnexionsFromDict(self,dictData,verbose=False,caching=False,renew=False):
		step=0
		for hostname__ in dictData:
			nom_equipement=hostname__
			commandes_cur=[]
			if 'configuration' in dictData[nom_equipement]:
				commandes_cur.append('conf t')
				commandes_cur+=dictData[nom_equipement]['configuration']
				commandes_cur.append('end')
			elif 'commande' in dictData[nom_equipement]:
				commandes_cur=dictData[nom_equipement]['commande']
			elif 'file' in dictData[nom_equipement]:
				with open(dictData[nom_equipement]['file']) as file_r:
					commandes_cur=file_r.read().split('\n')
			if nom_equipement in self.known_equipments:
				equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

			else:
				while nom_equipement not in self.known_equipments:
					self.known_equipments.append_read(nom_equipement)
				equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])

				
			entry=dictData[nom_equipement]

			if 'directory' in entry:
				repertoireCur=entry['directory']
			else:
				repertoireCur=self.repertoire
			
			if 'sub-directory' in entry:
				repertoireCur=repertoireCur+'/'+entry['sub-directory']
				
			if 'timeout' in entry:
				timeoutCur=entry['timeout']
			else:
				timeoutCur=self.timeout
			
			dictDataCur=dictData[hostname__].copy()
			if 'configuration' in dictDataCur:
				del dictDataCur['configuration']
			if 'commande' in dictDataCur:
				del dictDataCur['commande']
				
			self.connexion_liste.append(connexion(equipement_cur,commandes_cur,repertoire=repertoireCur,commande_en_ligne=commandes_cur,timeout=timeoutCur,verbose=self.verbose,dictData=dictDataCur))
			step+=1
				
def getHostsFromEnv(env,yamlFile=YAML_ENV):
	list_hosts=[]
	with open(yamlFile, 'r') as yml__:
		allEnv=yaml.load(yml__,Loader__)
	try:
		list_hosts=allEnv[env]
	except KeyError as E:
		print('Known environments:')
		ppr(list(allEnv.keys()))
		raise E
		
	return list_hosts

def getVrf(host__,caching=False,renew=False,timeout=200,verbose=False):
	Vrfs=None
	commande={'IOS':'show ip vrf','ARISTA':'show vrf | json','XR':None,'Nexus':'show vrf'}
	parsers={'IOS':ParseVrf,'ARISTA':lambda y: list(json.loads(y)['vrfs'].keys()),'XR':None,'Nexus':ParseVrf}
	
	if host__.OS=='XR':
		return
		
	commandeCur=commande[host__.OS]
	parserCur=parsers[host__.OS]
	
	
	
	TAG_VRF=TAG_GETALLVRF+host__nom.upper()
	cacheCurVrf=cc.Cache(TAG_VRF)
	aging=0
	if renew:
		aging=300
	if not caching or not cacheCurVrf.isOK(aging=aging):
		con_get_vrf_cur=connexion(host__,[],host__.OS,"TMP/"+"_getallvrf_"+host__.nom.lower()+".log","TMP","show ip vrf",timeout=timeout,verbose=verbose)
		host__.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParserCur,3)
		Vrfs=host__.Vrfs
		cacheCurVrf.save(Vrfs)
	else:
		print('Cache is used, timestamp:',cacheCurVrf.get_timestamp())
		host__.Vrfs=cacheCurVrf.getValue()
		Vrfs=host__.Vrfs
	
	return Vrfs


def getBgpNeighbors(host__,Vrfs,caching=False,renew=False,timeout=200,verbose=False):
	Neighbors=None
	OSCur=host__.OS
	
	if OSCur=='IOS' or OSCur=='OLD-IOS':
		commande_bgp_sum=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in Vrfs ]
		commande_bgp_sum.append("sh ip bgp summary")
		parserCur=ParseBgpNeighbor
		
	if OSCur=='Nexus':
		commande_bgp_sum=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  Vrfs ]
		commande_bgp_sum.append("sh ip bgp summary")
		parserCur=ParseBgpNeighbor


	if OSCur=='XR':
		commande_bgp_sum=[ 'sh bgp vrf all summary' ]
		parserCur=ParseBgpNeighbor
		
						
	
	TAG_NEIGH=TAG_GETALLNEIGH+host__nom.upper()
	cacheCurNeigh=cc.Cache(TAG_NEIGH)
	aging=0
	if renew:
		aging=300
		
	if not caching or not cacheCurNeigh.isOK(aging=aging):
		con_get_neigh_cur=connexion(host__,[],host__.OS,"TMP/"+"_getallbgpneigh_"+host__.nom.lower()+".log","TMP",commande_bgp_sum,timeout=timeout,verbose=verbose)
		Neighbors=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
		cacheCurNeigh.save(Neighbors)
		

	else:
		print('Cache is used, timestamp:',cacheCurNeigh.get_timestamp())
		Neighbors=cacheCurNeigh.getValue()
	
	return Neighbors

def runCmdCache(hostnames,commandes,verbose=False,caching=False,renew=False,timeout=100,parser=None,dbHosts=DB_HOSTS):
	''' run the same command'''
	results={}
	
	repertoireCur=TMP
	hostnamesCur=[]
	for hostname in hostnames:
		results[hostname]={}
		
	if caching:
		for hostname in hostnames:
			for commande in commandes:
				TAG_CUR=hostCur+'_'+commande.upper().replace(' ','_')
				cacheCur=cc.Cache(TAG_CUR)
				if not cacheCur.isOK(aging=300):
					hostnamesCur.append(hostname)
					break
				else:
					if not results[hostname]:
						results[hostname]={}
					results[hostname][commande]=cacheCur.getValue()
	
	else:
		hostnamesCur=hostnames
	
	commandesList=[ {'hostname': hostnamesCur,'commande':commandes}  for hostname in hostnames ]
	
	dbHostsObj=equipement_connus(dbHosts)
	listCon=connexions("",dbHostsObj,liste_commandes=[],repertoire=repertoireCur,commande_en_ligne=None,timeout=timeout,verbose=verbose,listData=commandesList,caching=caching,renew=renew)
	listCon.launch_commandes()
	
	for Con in listCon:
		hostCur=Con.hostname.upper()
		if not parser:
			results[hostCur]=Con.resultatByCommand
		else:
			for commande in Con.resultatByCommand:
				if commande in parser:
					results[hostCur]=parser[commande](Con.resultatByCommand[commande])
				else:
					print(f'no parser found for this command {commande}, raw output will be used')
					results[hostCur][commande]=Con.resultatByCommand[commande]

	return results

def runActionCache(hostnames,action,verbose=False,caching=False,renew=False,timeout=100,parsing=False,dbHosts=DB_HOSTS):
	''' run the default and simple action'''
	results={}
	
	repertoireCur=TMP
	hostnamesCur=[]
	

	for hostname in hostnames:
		results[hostname]={}
		
	aging=0
	if renew:
		aging=300
		
	if caching:
		for hostname in hostnames:
			TAG_CUR=action.upper()+'_'+hostCur
			cacheCur=cc.Cache(TAG_CUR)
			if not cacheCur.isOK(aging=aging):
				hostnamesCur.append(hostname)
				break
			else:
				results[hostname]=cacheCur.getValue()
	
	else:
		hostnamesCur=hostnames
	
	commandesList=[]
	
	with open(ACTION, 'r') as yml__:
		actions=yaml.load(yml__,Loader__)
			
	CtnEquipment=equipement_connus(dbHosts)
	for hostname in hostnamesCur:
		

		if hostname in CtnEquipment:
			equipement_cur=equipement(hostname,CtnEquipment.liste_equipements[hostname][0],CtnEquipment.liste_equipements[hostname][1],CtnEquipment.liste_equipements[hostname][2])
		else:
			while hostname  not in CtnEquipment:
				CtnEquipment.append_read(hostname)
			equipement_cur=equipement(hostname,CtnEquipment.liste_equipements[hostname][0],CtnEquipment.liste_equipements[hostname][1],CtnEquipment.liste_equipements[hostname][2])
		OSCur=equipement_cur.OS
		
		try:
			commandCur=actions['default'][action][OSCur]['commande']
		except KeyError as E:
			message=f'Action not supported {action} for {OSCur}'
			raise ActionNotSupported(message)
		
		if parsing:
			try:
				parserCurName=actions['default'][action][OSCur]['parser']
				parseCur=eval(parserCurName)
			except KeyError as E:
				message=f'Parser not supported {action} for {OSCur}'
				raise ActionNotSupported(message)
			
		commandesList.append({'hostname':hostname,'commande':commandCur})
		
	dbHostsObj=equipement_connus(dbHosts)
	listCon=connexions("",dbHostsObj,liste_commandes=[],repertoire=repertoireCur,commande_en_ligne=None,timeout=timeout,verbose=verbose,listData=commandesList,caching=caching,renew=renew)
	listCon.launch_commandes()
	
	for Con in listCon:
		hostCur=Con.hostname.upper()
		if not parsing:
			results[hostCur]=Con.resultat
		else:
			results[hostCur]=parseCur(Con.resultat)

	return results

def runListData(listData,verbose=False,timeout=100,parser=None,dbHosts=DB_HOSTS):
	''' run the command extract information from listData
	    format {'hostname'}: HOST, 'commande': [commande1,commande2,...]'''
		
	results={}
	
	
	dbHostsObj=equipement_connus(dbHosts)
	listCon=connexions("",dbHostsObj,liste_commandes=[],repertoire=TMP,commande_en_ligne=None,timeout=timeout,verbose=verbose,listData=listData)
	listCon.launch_commandes()
	
	for Con in listCon:
		hostCur=Con.hostname.upper()
		results[hostCur]={}
		if not parser:
			results[hostCur]=Con.resultatByCommand
		else:
			results[hostCur]=parser(Con.resultat)

	return results
	
def getVrfsForHostnames(hostnames,caching=False,renew=False,timeout=30,verbose=False):

	Vrfs=None
	Vrfs=runActionCache(hostnames,'VRF',verbose=verbose,caching=caching,renew=renew,timeout=timeout,parsing=True)
	
	
	return Vrfs



	
def getBgpNeighForHostnames(hostnames,Vrfs,caching=False,renew=False,timeout=30,verbose=False,dbHosts=DB_HOSTS):

	
	BgpNeighs=None
	
	listData=[]
	
	for hostname in hostnames:
		OSCur=equipement_connus.getOS(hostname)
		commandeCur=[]
		if OSCur=='IOS' or OSCur=="OLD-IOS":
		
			commandeCur=[ "sh ip bgp vpnv4 vrf "+Vrf__ for Vrf__ in Vrfs[hostname] ]
			commandeCur.append("sh ip bgp")
			parserCur=ParseBgpNeighbor
			
		elif OSCur=='Nexus':
			commandeCur=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  Vrfs[hostname] ]
			parserCur=ParseBgpNeighbor

        					
		elif OSCur=='XR':
			commandeCur=['sh bgp vrf all summary']
			parserCur=ParseBgpNeighbor
			
		else:
			'stop'
		
		listData.append({'hostname':hostname , 'commande':commandeCur})
		
	BgpNeighs=runListData(listData,verbose=False,timeout=100,parser=parserCur)
	
	
	return BgpNeighs
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=True)
	group3=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-e", "--equipement",action="store",type=str, help="Nom de l'equipement")
	group1.add_argument("-f", "--fichier",action="store",help="fichier contenant la liste d'equipement")
	group1.add_argument("--environment",action="store",help="environnement importé via yaml")
	group1.add_argument("-l", "--liste_equipement",action="store",type=str, help=u"Liste d'équipements séparés par des \':\'  ")
	group1.add_argument("-E", "--Editdb",action="store",help="Edition d'une database d'equipement")
	group2.add_argument("-c", "--commandes",action="store",help="fichier contenant les commandes")
	group2.add_argument("-C", "--commande_en_ligne",action="store",help="commdande directement en argument")
	group2.add_argument("-a", "--action",action="store",help=u'Parse les outputs - actions predéfinies - exemple RUN ARP MAC')
	group2.add_argument("-m", "--modifydb_equipement",action="store",help=u'équipement à modifier')
	group2.add_argument("-s", "--suppress_db_equipement",action="store",help=u'équipement à supprimer')
	group2.add_argument("-p", "--printdb",action="store_true",help=u"afficher la base d'équipement")
	group2.add_argument("-F", "--Format",action="store_true",help=u'Fichier avec format spécifque:NOM;commande1,commande2,commande3,...',required=False)
	group2.add_argument("-Y", "--Yaml",action="store_true",help=u'Fichier format yaml',required=False)
	group3.add_argument("-o", "--output",action="store",type=str, default="NONE", help="fichier output")
	group3.add_argument("-r", "--repertoire",action="store",type=str,default="OUTPUT",help=u"répertoire contenant les outputs")
	parser.add_argument("-d", "--dbliste",action="store",type=str,default="/home/d83071/CONNEXION/Equipement.db",help="Liste des equipements connus",required=False)
	parser.add_argument("-S", "--Suffixe",action="store",type=str,help="Suffixe des fichiers Output",required=False)
	parser.add_argument("-V", "--Verbose",action="store_true",help="Affiche le stdout / Verbose",required=False)
	parser.add_argument("-t", "--timeout",action="store",type=int,default=300,help="timeout expect",required=False)
	parser.add_argument("-P", "--Parsing",action="store",type=str,default=None,help="Mode de parsing: ex VRF, MAC , ARPCISCO",required=False)
	parser.add_argument("--cache",action="store_true",default=None,help="Use cache for certains option",required=False)
	parser.add_argument("--renew",action="store_true",default=None,help="Only with cache,renew value if aging exceed 300s",required=False)
	parser.add_argument("--no-timestamp",dest='noTimestamp',action="store_true",default=False,help="suppress time stamp",required=False)
	args = parser.parse_args()
	

	
	#print(args.Verbose)
	
	if args.environment:
		list_hosts=getHostsFromEnv(args.environment)
		args.liste_equipement=":".join(list_hosts)
			
	if args.equipement:
		E=equipement(args.equipement)
		if(args.commandes):
			C=connexion(E,args.commandes,"DEFAULT",output=args.output,repertoire=args.repertoire,verbose=args.Verbose,timeout=args.timeout)
			C.launch_commandes()
		elif(args.commande_en_ligne):
			C=connexion(E,args.commandes,"DEFAULT",output=args.output,repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,verbose=args.Verbose,timeout=args.timeout)
			C.launch_commande_en_ligne()
		elif(args.action):
			if re.search('^ARP:',args.action):
				print("ARP")
			else:
				print ("Action non supportée")
	elif args.fichier or args.liste_equipement or args.Format or args.Yaml:
		Liste_db_equipements=equipement_connus(args.dbliste)
		if(args.action):
				if re.search('^ARP:',args.action):
					print("ARP")
				elif args.action=='VRF':
					if args.fichier:
						Liste_E=connexions(args.fichier,Liste_db_equipements,"",repertoire=args.repertoire,action='VRF')
					elif args.liste_equipement:
						print("Action VRF incompatible avec option -l")
						sys.exit(10)
					Liste_E.launch_commandes()
					Liste_E.attendre_fin()
					Liste_E.set_status_final()
					Liste_E.print_status_final()
					
				elif args.action=='MAC' or args.action=='DESC' or re.search('^VLAN:',args.action) or args.action=='GETALLARP' or args.action=='GETALLROUTE' or args.action=='PORTCHANNEL' or args.action=='STATUS' or args.action=='SWITCHPORT' or args.action=='CDPDETAIL' or args.action=='TRANSCEIVER' or args.action=='GETALLBGP' or args.action=='GETBGPTABLE' or args.action=='FEX'  or args.action=='LLDPDETAIL' or args.action=='COUNTERERROR' or args.action=='RUN' or args.action=='VPC' or args.action=='MLAG':
					
					if args.fichier:
						Liste_E=connexions(args.fichier,Liste_db_equipements,"",repertoire=args.repertoire,action=args.action,suffixe=args.Suffixe,verbose=args.Verbose,timeout=args.timeout)
					elif args.liste_equipement:
						Liste_E=connexions("",Liste_db_equipements,"",repertoire=args.repertoire,action=args.action,suffixe=args.Suffixe,liste_equipement=args.liste_equipement,verbose=args.Verbose,timeout=args.timeout)
					Liste_E.launch_commandes()
					Liste_E.attendre_fin()
					Liste_E.set_status_final()
					Liste_E.print_status_final()

				else:
					print ("Action non supportée")
					sys.exit(40)
				
				if args.Parsing:
					for conn__ in Liste_E.connexion_liste:
						pprint.pprint(PARSER[args.Parsing](conn__.resultat))

		elif(args.commandes):
			if args.fichier:
				Liste_E=connexions(args.fichier,Liste_db_equipements,args.commandes,repertoire=args.repertoire,timeout=args.timeout,verbose=args.Verbose,noTimestamp=args.noTimestamp)
			elif args.liste_equipement:
				Liste_E=connexions("",Liste_db_equipements,args.commandes,repertoire=args.repertoire,liste_equipement=args.liste_equipement,timeout=args.timeout,verbose=args.Verbose,noTimestamp=args.noTimestamp)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()
		elif(args.commande_en_ligne):
			
			if args.fichier:
				Liste_E=connexions(args.fichier,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,timeout=args.timeout,verbose=args.Verbose,noTimestamp=args.noTimestamp)
			else:
				Liste_E=connexions("",Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,liste_equipement=args.liste_equipement,timeout=args.timeout,verbose=args.Verbose,noTimestamp=args.noTimestamp)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()
			
		elif(args.Format):
			
			Liste_E=connexions(args.fichier,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=None,timeout=args.timeout,verbose=args.Verbose,format=args.Format)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()

		elif(args.Yaml):
			Liste_E=connexions(args.fichier,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=None,timeout=args.timeout,verbose=args.Verbose,Yaml=args.Yaml)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()

	elif args.Editdb:
		DB=equipement_connus(args.Editdb)
		if args.modifydb_equipement:
			#equipement__=input(u'Quel équipement doit être modifié ou ajouté:')
			DB.append_read(args.modifydb_equipement)
		elif args.suppress_db_equipement:
			#equipement__=input(u'Quel équipement doit être modifié ou ajouté:')
			DB.suppress(args.suppress_db_equipement)
		elif args.printdb:
			print(DB)		
