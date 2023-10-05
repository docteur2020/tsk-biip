#!/usr/bin/env python3.7
# coding: utf-8

import csv
import pdb
import argparse
import pickle
import os
import pprint
import glob
from pathlib import Path
from tabulate import tabulate
from collections import OrderedDict
import xlsxwriter
from paramiko import SSHClient
from scp import SCPClient
from ipcalc import Network
from time import  strftime , localtime , ctime
from ipEnv import *
import pyparsing as pp
import dns.resolver


BASTION="192.64.10.129"
USERNAME="x112097"
LISTE_DNS=['192.16.207.80','184.12.21.17']

csv.field_size_limit(2000000000)
CSV_NETMAP="/home/X112097/CSV/NETMAP/current-netmap-export.csv"
PATH_CSV="/home/X112097/CSV/NETMAP/"
PATH_NET_DUMP="/home/X112097/CSV/NETMAP/DUMP/"
NETMAP_PAER="/home/reslocal/dmoScripts/dmoConf/COMMON/current-netmap-export.csv"

def getReverseDns(IP):
		resultat=[]
		for DNS in LISTE_DNS:
			name_cur=None
			try:
				name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),DNS).answer[0].__str__().split()[-1]
			except IndexError:
				pass
			if name_cur:
				resultat.append(name_cur)
		return resultat

def writeCsv(list_result,fichier_csv):
	
	with open(fichier_csv,'w+') as csvfile:
		csvwriter=csv.writer(csvfile,delimiter=';',quotechar='"',quoting=csv.QUOTE_ALL)
		for entry in list_result:
			csvwriter.writerow(entry)
	
	return None

def getSCPFile(username,bastion,file__,savepath):
	ssh_client=SSHClient()
	ssh_client.load_system_host_keys()
	ssh_client.connect(bastion, username=username)
	scp = SCPClient(ssh_client.get_transport())
	scp.get(file__,local_path=savepath)
	scp.close()


def get_last_dump(directory):
	return max(glob.glob(directory+'/*'),key=os.path.getctime)
	
def print_tabulate_dict(dict__):
	print(tabulate([[ val for val in dict__.values()]] ,headers=dict__.keys(),tablefmt='psql'))
	
def getbasefilename(file_with_path):
	return Path(file_with_path).stem
	
def gettimestamp():
    return strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	
def getLongestPrefix(prefix,lst_prefix,parserObj=None,mode='normal'):
	resultat=[]
	
	longuest_bit=0
	prefix_obj=Network(prefix)
	
	exception=[':1/16']
	
	
	
	for prefix_cur in lst_prefix:
		if prefix_cur not in exception:
			try:
				prefix_cur_obj=Network(prefix_cur)
			except ValueError as e:
				if parserObj:
					try:
						prefix_cur_other=parserObj.parseString(prefix_cur)[0]
						try:
							prefix_cur_obj=Network(prefix_cur_other)
						except ValueError as e0:
							print("Parsing issue, verify IPv4 Network format:",prefix_cur)
							pass
					except pp.ParseException as e1:
						print("Parsing issue, verify IPv4 Network format:",prefix_cur)
						pass
					except IndexError as e2:
						print("Parsing issue, verify IPv4 Network format:",prefix_cur)
						pass
					except ValueError as e3:
						print("Parsing issue, verify IPv4 Network format:",prefix_cur)
						pass
				else:
					print(e)
					
			
			if prefix_obj in prefix_cur_obj and prefix_cur_obj.subnet()> longuest_bit:
				if mode=='normal':
					resultat.append(prefix_cur)
				elif mode=='best':
					longuest_bit=prefix_cur_obj.subnet()
					resultat=prefix_cur
	
	return resultat
	
	
class NETMAPContainer(object):
	"NETMAP Container"
	
	def __init__(self,csv_file="",dump=""):
			
		if csv_file:
			reader=csv.DictReader(open(csv_file, "r",encoding="iso-8859-1"),delimiter=';')
			self.header=['subnet_id','base_network_address','network_bits','provider','customer','responsible','building_floor','comments','subnet_name']
			self.allDataBySubnet={}
			self.allDataBySubnetId={}
			
			for row in reader:
				self.allDataBySubnet[row['base_network_address']+'/'+row['network_bits']]={ key:value for key , value in dict(row).items() if key in self.header }
				self.allDataBySubnetId[row['subnet_id']]={ key:value for key , value in dict(row).items() if key in self.header }
			
		if dump:
			self.load(dump)
		

		
	def getInfoNet(self,subnet):
		resultat={}
		try:
			resultat=self.allDataBySubnet[hostname]
			#pprint.pprint(resultat)
		except KeyError as e:
			print('%s prefix non présent dans le fichier NETMAP' % hostname)
			
		return resultat
		
	
	def getBestMatchInfoNet(self,subnet,mode='normal'):
		resultat=[]
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
		Network_pp=pp.Combine(pp.MatchFirst([ipAddress+pp.Literal('/')+pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ),ipAddress]))
		best_entries=getLongestPrefix(subnet,self.allDataBySubnet.keys(),parserObj=Network_pp,mode=mode)
		
		if isinstance(best_entries,list):
			for best_entry  in best_entries:
				resultat.append(self.allDataBySubnet[best_entry])
		elif  isinstance(best_entries,str):
			resultat=self.allDataBySubnet[best_entries]
			
		
		return resultat
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pdb.set_trace()
			pickle.dump(self,file__)
			
	def load(self,filename):
		base=None
		
		with open(filename,'rb') as file__:
			base=pickle.load(file__)
		
		try:
			self.allDataBySubnetId=base.allDataBySubnetId
			self.allDataBySubnet=base.allDataBySubnet
		except:
			print('ERROR')
			

	def __str__(self):
		return str(self.allDataBySubnet)

	def __repr__(self):
		return str(self.allDataBySubnet)
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=False)
	group.add_argument("-p", "--prefix",  action="store",help="prefix pour lequel on cherche les infos netmap",required=False)
	group.add_argument("-f", "--file",  action="store",help="fichier de préfixes pour lesquels on cherche les infos netmap",required=False)
	parser.add_argument("-c", "--csv",  action="store",help="fichier csv contenant les informations NETMAP",required=False)
	parser.add_argument("-u", "--update",  action="store_true",help="Update CSV  SCP get de PAER",required=False)
	parser.add_argument("-s", "--save",  action="store",help="Sauvegarde dans csv",required=False)
	parser.add_argument("-P", "--Printing",  action="store_true",help="Affichage",required=False)
	args = parser.parse_args()
	
	if args.save and not args.file:
		raise argparse.ArgumentTypeError('l\'option update nécessite l\'option file')
	
	DUMPFILE=PATH_NET_DUMP+'netmap'+gettimestamp()+'.dump'
	
	if args.update:
		getSCPFile(USERNAME,BASTION,NETMAP_PAER,PATH_CSV)
		BaseNETMAP=NETMAPContainer(csv_file=CSV_NETMAP)
		print('DUMP FILE:',DUMPFILE)
		BaseNETMAP.save(DUMPFILE)
		
	elif args.csv:
		BaseNETMAP=NETMAPContainer(csv_file=args.csv)
		BaseNETMAP.save(DUMPFILE)
	
	else:
		if os.listdir(PATH_NET_DUMP):
			#print("On cherche dans le dump %s" % PATH_NET_DUMP)
			BaseNETMAP=NETMAPContainer(dump=get_last_dump(PATH_NET_DUMP))
		else:
			print("Ajouter un dump")
			
	if args.prefix:
			pprint.pprint(BaseNETMAP.getBestMatchInfoNet(args.prefix))
			
	if args.save:
		result=[]
		intEntries=ifEntries(dump=get_last_dump(PATH_IP_DUMP))
			
	if args.file:
		with open(args.file) as file_network:
			liste_network=file_network.read().split()
			for net__ in liste_network:
				result_cur=BaseNETMAP.getBestMatchInfoNet(net__)
				interfaces_cur=intEntries.getConnected(net__)
				try:
					ip_cur__=net__.split('/')[0]
					net_cur__=net__.split('/')[1]
				except IndexError as e:
					ip_cur__=net__.split('/')[0]
					net_cur__='32'
				
				if net_cur__=='32':
					cname__=intEntries.searchIP(ip_cur__)
					reverse_dns=getReverseDns(ip_cur__)
				else:
					cname__=None
					reverse_dns=None
					
				pprint.pprint(result_cur)
				if args.save:
					result.append([net__,result_cur,interfaces_cur,cname__,reverse_dns])
					
	if args.save:
		writeCsv(result,args.save)
			
	if args.Printing:
		pprint.pprint(BaseNETMAP)

				
			
