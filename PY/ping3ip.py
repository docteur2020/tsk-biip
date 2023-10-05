#!/usr/bin/env python3.8
# -*- coding: utf-8 -*- 

from __future__ import unicode_literals

import time
from time import gmtime, strftime , localtime
import threading
import sys
import os
import argparse
import pdb
import re
from io import StringIO 
from io import BytesIO
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import pickle
from ipcalc import *
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError 
from asciimatics.scene import Scene 

HOME="/home/d83071/"
LOG="/home/d83071/LOG"
REBOND="159.50.66.10"

def get_type_rebond(ip__):
	#pdb.set_trace()
	resultat="INCONNU"
	fichier_liste_rebond="/home/d83071/LIST/REBOND.TXT"
	
	with open(fichier_liste_rebond,'r') as file_rebond:
		for line in file_rebond:
			mots=line.split()
			if mots[0]==ip__:
				resultat=mots[1]
				break

	return resultat

def extract_vrf(ip__):
	vrf="GRT"
	ip_cur=ip__
	
	if ":" in ip__:
		mots=ip__.split(':')
		vrf=mots[0]
		ip_cur=mots[1]
		
	return (vrf,ip_cur)
	
def draw_rtt(screen,ping__):
	count=0
	posi_x_cur=0
	#pdb.set_trace()
	while count <=1000 or ping__.mode=='draw':
		posi_x_cur=0

		erase_ligne(screen,posi_x_cur,600)
		draw_ligne(screen,posi_x_cur,ping__)
		posi_x_cur=posi_x_cur+2
		screen.refresh()
		
		screen.refresh()		
		count=count+1
		time.sleep(0.1)
		
		ev = screen.get_key()

		if ev in (ord('Q'), ord('q')):
			ping__.stop()
			return

def draw_rtts(screen,pings__):
	count=0
	posi_x_cur=0
	#pdb.set_trace()
	while count <=1000 or pings__.mode=='draw':
		posi_x_cur=0
		for ping__ in pings__.pings:
			erase_ligne(screen,posi_x_cur,600)
			draw_ligne(screen,posi_x_cur,ping__)
			posi_x_cur=posi_x_cur+2
			#screen.refresh()
		
		time.sleep(0.1)
		screen.refresh()
		screen.reset()
		count=count+1
		
		
		ev = screen.get_key()

		if ev in (ord('Q'), ord('q')):
			pings__.stop()
			break;
			return

def draw_ligne(screen,posi_v,ligneping__):
	
	colour_ip=Screen.COLOUR_WHITE
	colour_cursor=Screen.COLOUR_GREEN
	colour_bg=Screen.COLOUR_BLUE
	
	rtt__=ligneping__.get_last_rtt()
	if rtt__.valeur=="N/A":
		rtt_valeur=1100
		colour_bg=Screen.COLOUR_MAGENTA
		colour_cursor=Screen.COLOUR_BLACK
	else:
		rtt_valeur=int(float(rtt__.valeur))
		colour_bg=Screen.COLOUR_BLUE
		colour_cursor=Screen.COLOUR_GREEN
		
	if rtt_valeur >= 1000:
		colour_cursor=Screen.COLOUR_RED
		colour_bg=Screen.COLOUR_MAGENTA
		
	screen.print_at(ligneping__.ip,
			0, posi_v,
			colour=colour_ip,
			bg=colour_bg,attr=Screen.A_BOLD)
	
	screen.print_at(ligneping__.description,
			16, posi_v,
			colour=Screen.COLOUR_BLACK,
			bg=Screen.COLOUR_WHITE,attr=Screen.A_BOLD)
			
	screen.print_at( u"\u2588"*rtt_valeur,
			32, posi_v,
			colour=colour_cursor,
			bg=Screen.COLOUR_BLACK,attr=Screen.A_BOLD)
			
def erase_ligne(screen,posi_v,max):
	screen.print_at(u"\u2588"*max,
			0, posi_v,
			colour=Screen.COLOUR_BLACK,
			bg=Screen.COLOUR_BLACK)
			
class rtt(object):
	"class round time trip"
	
	def __init__(self,valeur,pourcentage,time):
		self.date=time		
		self.valeur=valeur
		self.pourcentage=pourcentage
		self.status=self.set_status()
		
	def __str__(self):
		return self.date+'=='+self.valeur+'(ms)+==STATUS=='+self.status+'==PACKET LOSS=='+self.pourcentage
		
	def set_status(self):
		if self.pourcentage=="100%" or self.pourcentage=="N/A":
			status="KO"
		else:
			status="OK"
		
		return status
		
class pingResult(object):	
	def __init__(self,dump=None):
		self.Results={}	

		if dump:
			self.load(dump)

	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		pRes__=None
		
		with open(filename,'rb') as file__:
			pRes__=pickle.load(file__)
		
		try:
			self.Results=pRes__.Results
		except:
			print('ERROR LOAD DUMP')
			
	def add_entry(self,hostname,rtt__):
		if hostname in self.Results.keys():
			self.Results[hostname].append(rtt__)
		else:
			self.Results[hostname]=[rtt__]
			
	def __str__(self):
		resultat=StringIO()
		for hostname in self.Results.keys():
			resultat.write("Résultat pour "+hostname+":")
			for rtt__ in self.Results[hostname]:
				resultat.write(str(rtt__)+"\n")
			
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
			
class pingip(threading.Thread):
	"lance un ping via un rebond"
	
	def __init__(self,bastion,ip,count=4,verbose=True,occurence=5,mode='texte',description="NONE",resultat=None):
		threading.Thread.__init__(self)
		(vrf_,ip_)=extract_vrf(ip)
		self.ip=ip_
		self.vrf=vrf_
		self.bastion=bastion
		self.count=count
		self.verbose=verbose
		self.status="INIT"
		self.delay=0.5
		self.occurence_max=occurence
		self.description=description
		self.proxy=pxssh.pxssh()
		self.resultat_brut=[]
		self.rtt_liste=[]
		self.mode=mode
		self.resultat=resultat
		if self.verbose:
			self.proxy.logfile = sys.stdout.buffer
		
	def run(self):
		#pdb.set_trace()
		time.sleep(self.delay)
		self.status="RUN"
		type_rebond=get_type_rebond(self.bastion)
		
		if self.mode=='texte':
			print("Test Ping vers "+self.ip+" REBOND TYPE:"+type_rebond)
			
		
		
		#pdb.set_trace()
		
		if type_rebond == "CISCO" or type_rebond == "Nexus":
			self.rebond_cisco()
			#pdb.set_trace()
		elif type_rebond == "linux":
			self.rebond_linux(login,password)
		else:
			self.rebond()
			
		occurence=0
		
		while ( occurence <= int(self.occurence_max) or self.mode=="draw" ) and self.status!='STOP':
			#print(type_rebond)
			occurence=occurence+1

			if type_rebond == "CISCO":
				self.ping_cisco()
			elif type_rebond == "NEXUS":
				self.ping_nexus()
			else:
				self.ping()

			
		self.proxy.close()
		
	
	def rebond(self):
		try:
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
			if self.verbose:
				self.proxy.logfile = sys.stdout.buffer
			self.proxy.login(REBOND,'ld83071','Tek3pmac!Tek3pmac!')
				
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			
	def rebond_cisco(self,type="SSH"):
		"Connexion Cisco, type SSH|TELNET"
		#pdb.set_trace()
		try:
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
			if self.verbose:
				self.proxy.logfile = sys.stdout.buffer
			self.proxy.login(REBOND,'ld83071','Tek3pmac!Tek3pmac!')
			
			if type=="TELNET":
				self.proxy.sendline ('telnet '+self.bastion )
				self.proxy.expect ('sername' )
				self.proxy.sendline ('ld83071')
			else:
				self.proxy.sendline ('ssh -l ld83071 '+self.bastion )
			expect_value=self.proxy.expect(['assword','yes'])
			#print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				self.proxy.sendline('Tek3pmac!Tek3pmac!')
				self.proxy.expect(regex_match)
				self.proxy.sendline("terminal length 0")
				self.proxy.expect(regex_match)
			elif expect_value==1:
				self.proxy.sendline("yes")
				self.proxy.expect ('assword:' )
				self.proxy.sendline('TTek3pmac!Tek3pmac!')
				self.proxy.expect(regex_match)
				self.proxy.sendline("terminal length 0")
				self.proxy.expect(regex_match)
			else:
				print("Input non géré")
				os.exit(4)
		
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
	
	def ping(self):
	
		regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+\$','\n[a-zA-Z]\\S+\$','\$']
		data_output = BytesIO()
		self.proxy.logfile_read = data_output
		now=time.time()
		time_ms=repr(now).split('.')[1][:3]
		try:
			self.proxy.sendline('ping -c '+str(self.count)+" "+self.ip)
			self.proxy.expect(regex_match)
			time_=strftime("%Y%m%d_%Hh%Mm%Ss.", localtime())+time_ms
			self.resultat_brut.append( ( time_ , data_output.getvalue().decode('UTF-8') ))
			result_formatage=self.formatage_output(data_output.getvalue().decode('UTF-8'))
			self.rtt_liste.append(rtt(result_formatage[1],result_formatage[0],time_))
			self.resultat.add_entry(self.ip,rtt(result_formatage[1],result_formatage[0],time_))
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(e))
		
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED PING:"+"TIMEOUT SSH"+'=='+self.ip
	
	def ping_cisco(self):
		regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+\$','\n[a-zA-Z]\\S+\$','\$']
		data_output = BytesIO()
		self.proxy.logfile_read = data_output
		now=time.time()
		time_ms=repr(now).split('.')[1][:3]
		#pdb.set_trace()
		try:
			if self.vrf != "GRT":
				self.proxy.sendline('ping vrf '+self.vrf+" "+" "+self.ip +" repeat "+ str(self.count) )
			else:
				self.proxy.sendline("ping "+self.ip +" repeat "+ str(self.count) )
			self.proxy.expect(regex_match)
			time_=strftime("%Y%m%d_%Hh%Mm%Ss.", localtime())+time_ms
			self.resultat_brut.append( ( time_ , data_output.getvalue().decode('UTF-8') ))
			result_formatage=self.formatage_output_cisco(data_output.getvalue().decode('UTF-8'))
			self.rtt_liste.append(rtt(result_formatage[1],result_formatage[0],time_))
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(e))
		
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED PING:"+"TIMEOUT SSH"+'=='+self.ip
	
	def ping_nexus(self):
		regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+\$','\n[a-zA-Z]\\S+\$','\$']
		data_output = BytesIO()
		self.proxy.logfile_read = data_output
		now=time.time()
		time_ms=repr(now).split('.')[1][:3]
		#pdb.set_trace()
		try:
			if self.vrf != "GRT":
				self.proxy.sendline('ping '+" "+self.ip +" count "+ str(self.count) + " vrf "+self.vrf )
			else:
				self.proxy.sendline('ping '+" "+self.ip +" count "+ str(self.count) )
			self.proxy.expect(regex_match)
			time_=strftime("%Y%m%d_%Hh%Mm%Ss.", localtime())+time_ms
			self.resultat_brut.append( ( time_ , data_output.getvalue().decode('UTF-8') ))
			result_formatage=self.formatage_output_nexus(data_output.getvalue().decode('UTF-8'))
			self.rtt_liste.append(rtt(result_formatage[1],result_formatage[0],time_))
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(e))
		
		except ExceptionPexpect as e:
			print("pexpect failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED PING:"+"TIMEOUT SSH"+'=='+self.ip	
			
	def print_resultat_brut(self):
		
		print("Resultat pour "+self.ip+" :")
		for resultat in self.resultat_brut:
			print("timestamp:")
			print(resultat[0])
			print("output brut:")
			print(resultat[1])
		
	def print_resultat(self):
		
		print("Resultat:")
		for rtt__ in self.rtt_liste:
			print("timestamp:")
			print(rtt__.date)
			print("RTT AVG:")
			print(rtt__.valeur)
			print("Pourcentage")
			print(rtt__.pourcentage)
			print("Status")
			print(rtt__.status)
			
	def attendre_fin(self):
		self.join()	
		
	def stop(self):
		self.status="STOP"

	def formatage_output(self,raw_output):
		#pdb.set_trace()
		if re.search(r'packet loss',raw_output):
			p=re.search('(?P<pourcent>\S+) packet loss',self.grep(r'packet loss',raw_output))
			pourcentage=p.groups('pourcent')[0]

		else:
			pourcentage="N/A"
		if re.search(r'rtt min',raw_output):
			rtt__=self.grep(r'rtt min', raw_output).split()[3]
			rtt_avg=rtt__.split('/')[2]
		else:
			rtt_avg="N/A"
		#print(pourcentage)
		#print(rtt)
		
		return ((pourcentage,rtt_avg))

	def formatage_output_cisco(self,raw_output):
		if re.search(r'Success rate',raw_output):
			p=re.search('(?P<pourcent>\S+) percent',self.grep(r'percent',raw_output))
			pourcentage=str(100-int(p.groups('pourcent')[0]))+"%"
		
		elif re.search(r'packet loss',raw_output):
			p=re.search('(?P<pourcent>\S+) packet loss',self.grep(r'packet loss',raw_output))
			pourcentage=p.groups('pourcent')[0]

			
		else:
			pourcentage="N/A"
			
		if re.search(r'round-trip',raw_output):
			rtt__=self.grep(r'round-trip', raw_output).split()[9]
			rtt_avg=rtt__.split('/')[1]
		elif re.search(r'rtt min',raw_output):
			rtt__=self.grep(r'rtt min', raw_output).split()[3]
			rtt_avg=rtt__.split('/')[2]
		
		else:
			rtt_avg="N/A"
		#print(pourcentage)
		#print(rtt)
		
		return ((pourcentage,rtt_avg))
		
	def formatage_output_nexus(self,raw_output):
		
		if re.search(r'packet loss',raw_output):
			p=re.search('(?P<pourcent>\S+) packet loss',self.grep(r'packet loss',raw_output))
			pourcentage=p.groups('pourcent')[0]

		else:
			pourcentage="N/A"
		if re.search(r'round-trip',raw_output):
			#pdb.set_trace()
			rtt__=self.grep(r'round-trip', raw_output).split()[3]
			rtt_avg=rtt__.split('/')[2]
		else:
			rtt_avg="N/A"
		#print(pourcentage)
		#print(rtt)
		
		return ((pourcentage,rtt_avg))
		
	def grep(self,regex,texte):
		result=""
		for line in texte.split('\n'):
			if re.search(regex,line):
				result=line+'\n'+result
		return result
		
	def get_last_rtt(self):
	
		try:
			result=self.rtt_liste[-1]
		except:
			result=rtt("N/A","N/A","N/A")
			
		return result
				
class pingips(object):

	def __init__(self,fichier_liste_ip,verbose,mode='texte'):
		"""Format fichier:
		BASTION IP COUNT OCCURENCE"""
	
		self.ips=[]
		self.pings=[]
		self.verbose=verbose
		self.mode=mode
		self.pingResult__=pingResult()
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		self.logfile=LOG+"/PING/"+fichier_liste_ip.split(".")[0].split("/")[-1]+suffixe_time+".log.dump"
		print(self.logfile)
				
		with open(fichier_liste_ip,'r') as file_ips:
			for ligne in file_ips:
				mots=ligne.split()
				bastion__=mots[0]
				ip__=mots[1]
				count__=mots[2]
				occurence__=mots[3]
				try:
					description__=mots[4]
				except IndexError:
					description__="NONE"
				#pdb.set_trace()
				self.ips.append(ip__)
				self.pings.append(pingip(bastion__,ip__,count=count__,verbose=self.verbose,occurence=occurence__,mode=self.mode,description=description__,resultat=self.pingResult__))
				
	def print_last_rtt(self):
		for ping__ in self.pings:
			print(ping__.ip)
			print(ping__.get_last_rtt())
			
	def attendre_fin(self):
		for ping__ in self.pings:
			ping__.attendre_fin()
			
		print('===================')
		print('Sauvegarde des données dans '+self.logfile)
		self.pingResult__.save(self.logfile)
			
	def launch(self):
		for ping__ in self.pings:
			ping__.start()
			time.sleep(0.2) 
	
	def stop(self):
		for ping__ in self.pings:
			ping__.stop()
		
	def get_result(self):
		return str(self.pingResult__)
	
			
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-e", "--equipement",action="store",type=str, help="Nom de l'equipement")
	group1.add_argument("-f", "--fichier",action="store",help="fichier contenant la liste d'equipement")
	group1.add_argument("-l", "--liste_equipement",action="store",type=str, help=u"Liste d'équipements séparés par des \':\'  ")
	group1.add_argument("-D", "--Dump",action="store",type=str, help=u"Load dump file ")
	group2.add_argument("-V", "--Verbose",action="store_true",help="Affiche le stdout / Verbose",required=False)
	group2.add_argument("-d", "--draw",action="store_true",help=u"mode graphique avec barre non compatible verbose \u2588=1ms",required=False)
	group2.add_argument("-p", "--print",action="store_true",help=u"affiche les résultats",required=False)
	parser.add_argument("-r","--rebond",action="store",help="rebond/bastion/proxy",required=False,default=REBOND)
	
	args = parser.parse_args()
	
	if not args.draw and not args.Dump :
		if args.equipement:
			#pdb.set_trace()
			Ping=pingip(args.rebond,args.equipement,verbose=args.Verbose)
			Ping.start()
			Ping.attendre_fin()
			Ping.print_resultat_brut()
			Ping.print_resultat()
			
			print(Ping.get_last_rtt())
		elif args.fichier:
			Pings=pingips(args.fichier,args.Verbose)
			Pings.launch()
			Pings.attendre_fin()
			Pings.print_last_rtt()
			
	elif args.Dump:
		pingRes__=pingResult(dump=args.Dump)
		print(str(pingRes__))
		
	else:
		if args.equipement:
			Ping=pingip(args.rebond,args.equipement,verbose=False)
			Ping.start()
			Screen.wrapper(draw_rtt,arguments=[Ping])
			Ping.attendre_fin()
			Ping.print_resultat()

			
		elif args.fichier:
			Pings=pingips(args.fichier,verbose=False,mode="draw")
			Pings.launch()
			try:
				Screen.wrapper(draw_rtts,arguments=[Pings])
			except KeyboardInterrupt:
				print ('KeyboardInterrupt exception is caught')
				Pings.stop()
			Pings.attendre_fin()
			Pings.print_last_rtt()
			
			print(Pings.get_result())