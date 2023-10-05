#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
from ipcalc import Network , IP
import argparse
import pdb
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

class grepIpError(Exception):
	"Classe Exception pour grep-ip"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitée'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un réseau IPV4 valide'
		super(grepIpError, self).__init__(self.message[code])
 
def genere_mask_list():
	return [ Network("0.0.0.0/"+str(i)).netmask().__str__() for i in range(0,33) ]
	
def genere_wildcard_list():
	return [ netmask_to_wildcard(Network("0.0.0.0/"+str(i)).netmask()) for i in range(0,33) ]
	
def match_wildcard(network_to_test,network,wildcard,option_v=False,option_e=False):

	
	result=False
	wildcard_possible=genere_wildcard_list()
	
	network_mask=Network(str(network.network())+"/"+wildcard_to_netmask(wildcard.network()))
	
	#pdb.set_trace()
	if str(wildcard.network()) in wildcard_possible:
		if option_e:
			if network_to_test == network_mask:
				result=True		
		else:
			if network_mask in network_to_test and network_mask>=network_to_test:
				result=True		
	else:
		for ip in network_to_test:
			if int(network)==int(ip)&(~int(wildcard)):
				result=True
				break
			
	return result
	
def match_wildcard_longer(network_to_test,network,wildcard,option_v=False,option_e=False):

	
	result=False
	wildcard_possible=genere_wildcard_list()
	
	network_mask=Network(str(network.network())+"/"+wildcard_to_netmask(wildcard.network()))
	
	#pdb.set_trace()
	if str(wildcard.network()) in wildcard_possible:
		if option_e:
			if network_to_test == network_mask:
				result=True		
		else:
			if network_mask in network_to_test  and  network_mask<=network_to_test:
				result=True		
	else:
		for ip in network_to_test:
			if int(network)==int(ip)&(~int(wildcard)):
				result=True
				break
			
	return result

def print_verbose(line,option_v=False,level=1):

	if option_v:
		if option_v >= level:
			print(line)
	#print("OPTION_V",str(option_v))
	
		
def match(network,lines,option_v=False,option_e=False,option_n=False,option_l=False,option_p=False):

	mask_possible=genere_mask_list()
	wildcard_possible=genere_wildcard_list()
	number=0
	number_line_list_printed=[]
	pattern_network_mask_or_wildcard='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])(\s+|[a-z]+|[A-Z]+)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])'
	pattern_network_net='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])/([0-9]|[12][0-9]|[3][0-2])(\s+|$)'
	pattern_ip='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])'
	regex_network_mask_or_wildcard= re.compile(pattern_network_mask_or_wildcard)
	regex_network_net=re.compile(pattern_network_net)
	regex_ip=re.compile(pattern_ip)
	for line in lines.splitlines() : 
		#print_verbose(mask_possible)
		print_verbose("\nLINE:"+line,option_v,level=2)
		network_mask_or_wildcard_list =  regex_network_mask_or_wildcard.finditer(line)
		network_net_list =  regex_network_net.finditer(line)
		ip_list =  regex_ip.finditer(line)
		number=number+1
		if network_mask_or_wildcard_list:
			#pdb.set_trace()
			if option_v:
				for network_mask_or_wildcard in network_mask_or_wildcard_list:
					print_verbose("NETWORK MASK OR WILDCARD LIST:"+network_mask_or_wildcard.__str__(),option_v)
				network_mask_or_wildcard_list =  regex_network_mask_or_wildcard.finditer(line)
				
			for network_mask_or_wildcard in network_mask_or_wildcard_list:
				print_verbose("\n=====================",option_v)
				print_verbose("Valid Network (mask) present",option_v)
				print_verbose("=====================",option_v)
				print_verbose(network_mask_or_wildcard.__str__(),option_v)
				try:
					res_cur_line=Network(network_mask_or_wildcard.group(0).split()[0])
				except:
					raise grepIpError(code=2,value1=network_mask_or_wildcard.group(0).split()[0])
					
				possible_mask=network_mask_or_wildcard.group(0).split()[1]
				if possible_mask in mask_possible:
					print_verbose("PO:"+possible_mask+" is a mask",option_v)
					try:
						net_cur_line=Network((network_mask_or_wildcard.group(0).split()[0]+"/"+possible_mask).replace(" ",""))
					except:
						raise grepIpError(code=2,value1=network_mask_or_wildcard.group(0).split()[0]+"/"+possible_mask)
						
					
					if option_e:
						if net_cur_line == network and number not in number_line_list_printed:
							if option_n:
								if option_p:
									print (str(number)+"-EXACT MATCH("+str(network)+"):"+line)
								else:
									print (str(number)+"-EXACT MATCH:"+line)
							else:
								if option_p:
									print ("EXACT MATCH("+str(network)+"):"+line)
								else:
									print ("EXACT MATCH:"+line)
							if number not in number_line_list_printed:
									number_line_list_printed.append(number)
									
					elif option_l:
						print_verbose(u"Option -l activée",option_v)
						if network in net_cur_line and network >= net_cur_line and number not in number_line_list_printed:
							#pdb.set_trace()
							if option_n:
								if option_p:
									print(str(number)+"-MATCH("+str(network)+"):"+line)
								else:
									print(str(number)+"-MATCH:"+line)
							else:
								if option_p:
									print("MATCH("+str(network)+"):"+line)
								else:
									print("MATCH:"+line)
							if number not in number_line_list_printed:
									number_line_list_printed.append(number)
						
					else:
						#pdb.set_trace()
						if net_cur_line in network and network <=net_cur_line and number not in number_line_list_printed:
							if option_n:
								if option_p:
									print(str(number)+"-MATCH("+str(network)+"):"+line)
								else:
									print(str(number)+"-MATCH:"+line)
							else:
								if option_p:
									print("MATCH("+str(network)+"):"+line)
								else:
									print("MATCH:"+line)
							if number not in number_line_list_printed:
									number_line_list_printed.append(number)
									
				elif possible_mask in wildcard_possible:
					print_verbose("PO:"+possible_mask+" is a wildcard",option_v)
					
					try:
						wild_cur_line=Network(possible_mask)
					except:
						raise grepIpError(code=2,value1=possible_mask)
						
					if option_l:
						if match_wildcard_longer(network,res_cur_line,wild_cur_line,option_v,option_e) and number not in number_line_list_printed:
							if option_n:
								if option_p:
									print(str(number)+"-MATCH("+str(network)+"):(WILDCARD):"+line)
								else:
									print(str(number)+"-MATCH (WILDCARD):"+line)
							else:
								if option_p:
									print("MATCH("+str(network)+"):(WILDCARD):"+line)
								else:
									print("MATCH (WILDCARD):"+line)
							if number not in number_line_list_printed:
								number_line_list_printed.append(number)
					else:					
						if match_wildcard(network,res_cur_line,wild_cur_line,option_v,option_e) and number not in number_line_list_printed:
							if option_n:
								if option_p:
									print(str(number)+"-MATCH("+str(network)+"):(WILDCARD):"+line)
								else:
									print(str(number)+"-MATCH (WILDCARD):"+line)
							else:
								if option_p:
									print("MATCH("+str(network)+"):(WILDCARD):"+line)
								else:
									print("MATCH (WILDCARD):"+line)
							if number not in number_line_list_printed:
								number_line_list_printed.append(number)
										
						
		if network_net_list:
			if option_v:
				for network_net in network_net_list:
					print_verbose("NETWORK LIST:"+network_net.__str__(),option_v)
				network_net_list =  regex_network_net.finditer(line)
				
			for network_net in network_net_list:
				print_verbose("IP LIST:"+network_net.__str__(),option_v)
				try:
					net_cur_line=Network(network_net.group(0).replace(" ",""))
				except:
					raise grepIpError(code=2,value1=network_net.group(0).replace(" ",""))
				if option_e:
					if net_cur_line == network and number not in number_line_list_printed:
						if option_n:
							if option_p:
								print (str(number)+"-EXACT MATCH("+str(network)+"):"+line)
							else:
								print (str(number)+"-EXACT MATCH:"+line)
						else:
							if option_p:
								print ("EXACT MATCH("+str(network)+"):"+line)
							else:
								print ("EXACT MATCH:"+line)
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
				elif option_l:
					if net_cur_line in network and network >= net_cur_line and number not in number_line_list_printed:
						if option_n:
							if option_p:
								print(str(number)+"-MATCH("+str(network)+"):"+line)
							else:
								print(str(number)+"-MATCH:"+line)
						else:
							if option_p:
								print("MATCH("+str(network)+"):"+line)
							else:
								print("MATCH:"+line)
								
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
				else:
					if net_cur_line in network and network <=net_cur_line and number not in number_line_list_printed:
						if option_n:
							if option_p:
								print(str(number)+"-MATCH("+str(network)+"):"+line)
							else:
								print(str(number)+"-MATCH:"+line)
						else:
							if option_p:
								print("MATCH("+str(network)+"):"+line)
							else:
								print("MATCH:"+line)
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
							
		if ip_list:
			if option_v:
				for ip in ip_list:
					print_verbose("IP LIST"+ip.__str__(),option_v)
				ip_list =  regex_ip.finditer(line)
				
			for ip in ip_list:
				print_verbose("\n=====================",option_v)
				print_verbose("Valid IP address present",option_v)
				print_verbose("=====================",option_v)
				print_verbose(ip.__str__(),option_v)
				try:
					net_cur_line=Network(ip.group(0)+"/32")
				except:
					raise grepIpError(code=2,value1=ip.group(0)+"/32")
				if option_e:
					if net_cur_line == network and number not in number_line_list_printed:
						if option_n:
							if option_p:
								print (str(number)+"-EXACT MATCH("+str(network)+"):"+line)
							else:
								print (str(number)+"-EXACT MATCH:"+line)
						else:
							if option_n:
								print ("EXACT MATCH("+str(network)+"):"+line)
							else:
								print ("EXACT MATCH:"+line)
								
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
				elif option_l: 
					if net_cur_line in network and number not in number_line_list_printed:
						if option_n:
							if option_p:
								print (str(number)+"-MATCH("+str(network)+"):"+line)
							else:
								print (str(number)+"-MATCH:"+line)
						else:
							if option_p:
								print ("MATCH("+str(network)+"):"+line)
							else:
								print ("MATCH:"+line)
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
				else:
					if net_cur_line in network and number not in number_line_list_printed: 
						if option_n:
							if option_p:
								print(str(number)+"-MATCH("+str(network)+"):"+line)
							else:
								print(str(number)+"-MATCH:"+line)
						else:
							if option_p:
								print("MATCH("+str(network)+"):"+line)
							else:
								print("MATCH:"+line)
						if number not in number_line_list_printed:
							number_line_list_printed.append(number)
							
		if number not in number_line_list_printed:
			print_verbose("\nno valid IP present",option_v)

	print_verbose(u'Ligne affichée (numéro):\n'+str(number_line_list_printed),option_v)
		
def netmask_to_wildcard(netmask):
	# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
	return str(IP(int(IP('255.255.255.255'))-int(netmask)))
	
def wildcard_to_netmask(wildcard):
	# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
	return str(IP(int(IP('255.255.255.255'))-int(wildcard)))
		
def main(network,file):
	return
 
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	parser.add_argument("-e", "--exact",action="store_true",help="exact match",required=False)
	parser.add_argument("-n", "--numeric",action="store_true",help="print line number",required=False)
	parser.add_argument("-l", "--longer_prefixes",action="store_true",help="match longer prefixes",required=False)
	parser.add_argument("-f", "--file-ip",dest='file_ip',action="store_true",help="mode file",required=False)
	parser.add_argument("-p", "--print-prefix",dest='printing',action="store_true",default=False, help="print the network",required=False)
	
	all_lines=""
	
	if os.isatty(0):
		parser.add_argument(dest='network',nargs='*')
		parser.add_argument('file')
		mode="FILE"

	else:
		parser.add_argument(dest='network',nargs='*')
		mode="STDIN"
		
	args = parser.parse_args()
	
	if mode=="FILE":
		for net__ in args.network:
			print_verbose('Network:'+net__,args.Verbose)
		print_verbose('File:'+args.file,args.Verbose)
		param_file=args.file
		with open(param_file,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		for net__ in args.network:
			print_verbose('Network:'+net__,args.Verbose)
		param_file=None
		all_lines=sys.stdin.read()
	
	if args.file_ip:
		with open(args.network[0]) as file_network:
			liste_network=file_network.read().split()
			for net__ in liste_network:
				try:
					param_network=Network(net__)
				except:
					raise grepIpError(code=2,value1=args.network)
				
				match(param_network,all_lines,args.Verbose,args.exact,args.numeric,args.longer_prefixes,option_p=args.printing)
	else:
		for net__ in args.network:
			try:
				param_network=Network(net__)
			except:
				raise grepIpError(code=2,value1=args.network)
			
			match(param_network,all_lines,args.Verbose,args.exact,args.numeric,args.longer_prefixes,option_p=args.printing)
	
	#print_verbose(match_wildcard(Network("192.168.211.0"),Network("192.168.1.0"),Network("0.0.254.0")))
