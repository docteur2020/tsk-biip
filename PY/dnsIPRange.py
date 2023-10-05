#!/usr/bin/env python3.8
# coding: utf-8


import pdb
import argparse
from netaddr import IPAddress, IPNetwork
import sys
from pprint import pprint as ppr
import dns.resolver
from dns.exception  import DNSException
from time import gmtime, strftime , localtime ,ctime , sleep

import yaml

DNSs={'BNL':[] ,'FORTIS':['10.18.1.200'], 'BNP':['159.50.101.10','159.50.169.10']}
DIR_YAML_SAVE='/home/d83071/yaml/ptr/'

def saveData(data,yaml_tag):
	suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())

	filename=DIR_YAML_SAVE+'/'+yaml_tag+'.yml'
	with open(filename,'w') as yml_w:
		print(f"Saving file:{filename}")
		yaml.dump(data,yml_w ,default_flow_style=False)

def getReverseDns(IP,LISTE_DNS):
		resultat=[]
		for DNS in LISTE_DNS:
			name_cur=None
			try:
				answerCur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR,  use_edns=0),DNS,timeout=3)
				name_cur=answerCur.answer[0].__str__().split()[-1]
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
		
def extractNetworkFile(filenetwork):

	liste_network=[]
	with open(args.file) as file_network:
		liste_network=file_network.read().split()
		
	return liste_network
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-e", "--env",action="store",help="environment",default="BNP")
	group1.add_argument("-n", "--network",action="store")
	group1.add_argument("-f", "--file",action="store",help="Network List")
	parser.add_argument("-s", "--save",action="store",help=u"Sauvegarde dans fichier dump",required=False)
	args = parser.parse_args()
	
	if args.env not in DNSs:
		print(f'environment unknown:{" ".join(DNSs)}',file=sys.stderr)
	else:
		DNSList=DNSs[args.env]
		
	result={}
		
	if args.network:
		for ip__ in IPNetwork(args.network):
			ip_str=str(ip__)
			res_cur=getReverseDns(ip_str,DNSList)
			print(ip_str)
			sleep(0.1)
			if res_cur:
				result[ip_str]=res_cur
				print(f'net:{args.network} , ip:{ip_str} , ptr:{res_cur}')
	
	if args.file:
		listNet=extractNetworkFile(args.file)
		
		for net in listNet:
			sleep(1)
			for ip__ in  IPNetwork(net):
				ip_str=str(ip__)
				print(ip_str)
				sleep(0.5)
				res_cur=getReverseDns(ip_str,DNSList)
				if res_cur:
					if net not in result:
						result[net]={ip_str:res_cur}
					else:
						result[net][ip_str]=res_cur
					print(f'net:{net} , ip:{ip_str} , ptr:{res_cur}')
	ppr(result)		
	
	if args.save:
		saveData(result,f'{args.env}_{args.save}')
			
	