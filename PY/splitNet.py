#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
from ipcalc import Network , IP
import argparse
import pdb


class IpError(Exception):
	"Classe Exception pour le format IP"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitée'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un réseau IPV4 valide'
		super(IpError, self).__init__(self.message[code])
 


def print_verbose(line,option_v=False,level=1):

	if option_v:
		if option_v >= level:
			print(line)
	#print("OPTION_V",str(option_v))


def split_network(net__,bits,option_v=False):	
	subnet=net__.subnet()
	if subnet > bits:
		return [net__]
		
	else:
		print_verbose("Network à splitter",option_v=option_v)
		nb_network=int((pow(2,32-subnet))/(pow(2,32-bits)))
		print_verbose("nombre de Net:"+str(nb_network),option_v=option_v)
		resultat=[]
		first_net=Network(str(net__.network())+'/'+str(bits))
		print_verbose("First Net:"+str(first_net),option_v=option_v)
		for i in range(nb_network):
			net_cur=first_net+i*(pow(2,32-bits))
			resultat.append(net_cur)
			print_verbose("Reseau "+str(i+1)+":"+str(net_cur),option_v=option_v)
			
		return resultat
	
		
 
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	parser.add_argument("-m","--max",action="store",type=int,default=17,help="max wildcard")
	group.add_argument("-f","--file",action="store",help="Fichier contenant les réseaux")
	group.add_argument("-n","--network",action="store",help="Network à splitter si nécessaire")

	args = parser.parse_args()
	
	if args.network:
		print_verbose("mode Network",option_v=args.Verbose)
		

		try:
			param_network=Network(args.network)
			
		except:
			raise IpError(code=2,value1=args.network)
			
		net_split=split_network(param_network,args.max,option_v=args.Verbose)
			
		for net__ in net_split:
			print(str(net__))
			
	if args.file:
		print_verbose("mode Fichier",option_v=args.Verbose)
					
		with open(args.file) as file_network:
			liste_network=file_network.read().split()
			for net__ in liste_network:
				try:
					param_network=Network(net__)
				except:
					raise IpError(code=2,value1=args.network)
				
				net_split=split_network(param_network,args.max,option_v=args.Verbose)
				for net___ in net_split:
					print(str(net___))
