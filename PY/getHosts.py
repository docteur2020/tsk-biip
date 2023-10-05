#!/bin/python3.7


import sys
import argparse
import pyparsing as pp
import pdb
import glob
import re
from time import gmtime, strftime , localtime
import pickle
import os
from pprint import pprint as ppr

from paramiko import SSHClient
from scp import SCPClient

PATH_HOST="/home/x112097/HOSTS"
PAER="192.64.10.129"
DEFAULT_USERNAME="x112097"

def get_last_dump_host(path__):
	lastDump=max(glob.glob(path__+'/DUMP/*.dump'),key=os.path.getctime)
	#print("dump:",lastDump)
	return lastDump
	
def getSCPFile(username,bastion,file__,savepath):
	ssh_client=SSHClient()
	ssh_client.load_system_host_keys()
	ssh_client.connect(bastion, username=username)
	scp = SCPClient(ssh_client.get_transport())
	scp.get(file__,local_path=savepath)
	scp.close()
	
def parseHostsFile(File__):
	Result={}
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	Commentaire=pp.Suppress(pp.Group((pp.Literal('#')| pp.Literal('*'))+pp.OneOrMore(pp.CharsNotIn('\n'))))
	Nom=pp.Word(pp.alphanums+'-_./').addCondition(lambda tokens:  tokens[0][0] not in pp.nums and '\n' not in tokens[0])
	EntryHost=pp.Group(ipAddress+pp.Group(pp.OneOrMore(Nom))+pp.Optional(pp.OneOrMore(pp.CharsNotIn('\n'))))
	Port=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <65536 and int(tokens[0]) >= 0 )
	EntryPort=pp.Suppress(ipAddress+Port+pp.Group(pp.OneOrMore(Nom))+pp.Optional(pp.OneOrMore(pp.CharsNotIn('\n'))))
	Entry=pp.MatchFirst([Commentaire,EntryHost,pp.Suppress(pp.Literal('#')),EntryPort,pp.Suppress(pp.Word(pp.nums)+pp.OneOrMore(pp.CharsNotIn('\n'))),pp.Suppress(Nom+pp.OneOrMore(pp.CharsNotIn('\n'))),pp.Suppress(pp.Word('-'))])
	Entries=pp.OneOrMore(Entry)
	Result__=Entries.parseFile(File__,parseAll=True)
	
	for host in Result__.asList():
		for nom__ in host[1]:
			if nom__.lower() not in Result:
				Result[nom__.lower()]=[host[0]]
			else:
				Result[nom__.lower()].append(host[0])
		
	
	return Result
	
class Hosts(object):
	def __init__(self,repertoire=PATH_HOST, dump=''):
		if dump:
			self.load(dump)
		else:
			self.hosts={}
			for file__ in glob.glob(repertoire+'/*'):
				if not re.search('dump',file__, re.IGNORECASE):
					self.hosts.update(parseHostsFile(file__))
			self.repertoire=repertoire
			
	def save(self):
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		filename=self.repertoire+'/DUMP/'+'hosts'+suffixe_time+'.dump'
		
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		host__=None
		
		with open(filename,'rb') as file__:
			try:
				host__=pickle.load(file__)
			except AttributeError as E:
				pdb.set_trace()
				print(E)
				
			
		try:
			self.hosts=host__.hosts
			self.repertoire=host__.repertoire
		except:
			print('ERROR LOAD HOST DUMP:'+filename)
			
	def getIP(self,nom):
		try:
			return self.hosts[nom.lower()]
		except KeyError:
			return [nom]
			
	def getHostname(self,ip):
		result=[]
		for name__ in self.hosts:
			for ip_cur in self.hosts[name__]:
				if ip_cur==ip:
					result.append(name__)
		return result
			
	def __str__(self):
		return str(self.hosts)
		
	def research(self,reg):
		resultat=[]
		for nom in self.hosts:
			if re.search(reg,nom,re.IGNORECASE):
				resultat.append({'nom':nom,'ip':self.hosts[nom]})
				
				
		return resultat
		
	@staticmethod
	def update(username=DEFAULT_USERNAME,rebond=PAER,savepath=PATH_HOST):
		getSCPFile(username,PAER,'/etc/hosts',PATH_HOST)
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group()
	group.add_argument("-f", "--file",  action="store",help="fichier hosts")
	group.add_argument("-r", "--repertoire",default=PATH_HOST,  action="store",help="repertoire fichier hosts")
	group.add_argument("-d", "--dump",  action="store_true",help="dump fichier hosts")
	parser.add_argument("-s", "--save",  action="store_true",help="Sauvegarde")
	parser.add_argument("-P", "--Print",  action="store_true",help="Affichage")
	parser.add_argument("-n", "--nom",  action="store",help="resolution nom/ip")
	parser.add_argument("-u", "--update",  action="store_true",help="update host file")
	parser.add_argument("--ip", action="store",help="get host name for an ip")
	parser.add_argument( "-S" "--search",dest='search' , action="store",help="search host")
	args = parser.parse_args()
	
	if args.update:
		Hosts.update()
	
	if args.file:
		resultat=parseHostsFile(args.file)
		print(resultat)
		
	if args.repertoire:
		hosts__=Hosts(repertoire=args.repertoire)
		
		if args.save:
			hosts__.save()
			
		if args.Print:
			print(hosts__.__str__())
			
		if args.search:
			result_search=hosts__.research(args.search)
			ppr(result_search,width=100)
			
		if args.ip:
			result_ip=hosts__.getHosts(args.ip)
			ppr(result_ip,width=100)
			
	if args.dump:
		hosts__=Hosts(dump=get_last_dump_host(PATH_HOST+'/DUMP'))
		
		if args.save:
			hosts__.save()
			
		if args.nom:
			print(hosts__.getIP(args.nom))
			
		if args.Print:
			print(hosts__.__str__())
			
		if args.search:
			result_search=hosts__.research(args.search)
			ppr(result_search,width=100)
			
		if args.ip:
			result_ip=hosts__.getHosts(args.ip)
			ppr(result_ip,width=100)
			
