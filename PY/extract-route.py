#!/usr/bin/env python3.8
# coding: utf-8


import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from ParsingShow import ParseIpRoute,writeCsv
import csv
import checkroute
import sys
import os
import argparse
from getNetEntry import getNetMatchSilent,dmoCache,get_last_dump
from getNetmapInfo import NETMAPContainer
from ipEnv import ifEntries , interface
import glob
import pdb
from netaddr import IPNetwork , IPAddress
from xlsxDictWriter import xlsMatrix
from pprint import pprint as ppr
from checkStaticRoute import MultipleRTContainer


import pdb



PREFIX_DUMP_DIR="/home/d83071/DUMP/PREFIX"
IP_DUMP_DIR="/home/d83071/IP/DUMP/"
PATH_NET_DUMP="/home/X112097/CSV/NETMAP/DUMP/"

def get_last_dump_ip(rep__):
	return max(glob.glob(rep__+'/*'),key=os.path.getctime)

def addInfoNetmap(liste_prefixes,netmapContainer):
	resultat=None
	if isinstance(liste_prefixes,list):
		resultat=[]
		for prefix in liste_prefixes:
			info_cur=netmapContainer.getBestMatchInfoNet(prefix[2].__str__(),mode='best')
			resultat.append(prefix+[info_cur])
			print(str(info_cur))
	elif isinstance(liste_prefixes,dict):
		resultat={}
		for vrf__ in liste_prefixes:
			resultat[vrf__]=[]
			for prefix in liste_prefixes[vrf__]:
				info_cur=netmapContainer.getBestMatchInfoNet(prefix[1].__str__(),mode='best')
				resultat[vrf__].append(prefix+[str(info_cur)])
				print(str(info_cur))
	return resultat

def addInfoConnected(liste_prefixes):
	resultat=[]
	
	defaultDump=get_last_dump_ip(IP_DUMP_DIR)
	DC_IP=ifEntries(dump=defaultDump)
	
	
	total=len(liste_prefixes)
	nb=1
	for prefix in liste_prefixes:
		info_cur=DC_IP.getConnected(prefix[2].__str__())
		print("Traitement:"+str(nb)+"/"+str(total))
		nb+=1
		resultat.append(prefix+[info_cur])
	
	return resultat
	
def addInfoNH(liste_prefixes):
	resultat=[]
	
	defaultDump=get_last_dump_ip(IP_DUMP_DIR)
	DC_IP=ifEntries(dump=defaultDump)
	
	
	total=len(liste_prefixes)
	nb=1
	for prefix in liste_prefixes:
		info_cur=DC_IP.searchIP(prefix[3][0].__str__())
		print("Traitement:"+str(nb)+"/"+str(total))
		nb+=1
		resultat.append(prefix+[info_cur])
	
	return resultat

def addInfoToListNH(dict_NH):
	resultat={}
	
	defaultDump=get_last_dump_ip(IP_DUMP_DIR)
	DC_IP=ifEntries(dump=defaultDump)
	
	
	for vrf__ in dict_NH:
		resultat[vrf__]={}
		for nh in dict_NH[vrf__]:
			info_nh=DC_IP.searchIP(nh)
			resultat[vrf__][nh]={'reverse':info_nh,'count':dict_NH[vrf__][nh]}

	
	return resultat

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=False)
	group3=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-o", "--output",action="store",help="Contient le fichier output")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump")
	group1.add_argument("-y", "--yaml",action="store",help="Yaml qui contient plusieurs table de routage")
	group2.add_argument("-n", "--nexthop",action="append",default=[],help="Filtrage sur le Next-hop")
	group2.add_argument("-l", "--liste-nexthop",dest='liste_nexthop',action="store",help="Filtrage sur une liste de Next-hop contenu dans un fichier")
	parser.add_argument("-v", "--vrf",action="store",help="Filtrage sur la vrf contenu dans un fichier")
	group2.add_argument("--prefix-filter", dest='prefix_filter',action="store",help="Filtrage sur le net type longer prefix,format: VRF1:VRF2:...:VRFN:PREFIX")
	group2.add_argument("--route-ip", dest='route_ip',action="store",help="Route pour une IP VRF1:VRF2:...:VRFN:IP")
	parser.add_argument("-p", "--protocol",action="store",help="Filtrage sur le protocol",required=False)
	parser.add_argument("-P", "--Print",action="store_true",help=u'affiche le résultat ou le dump',required=False)
	parser.add_argument("--list-all-nexthop",action="store_true",dest='list_all_nexthop',help=u'get all nexthop',required=False)
	parser.add_argument("--list-all-vrf",action="store_true",dest='list_all_vrf',help=u'get all vrf',required=False)
	parser.add_argument("-f", "--format",action="store",help=u'formatage de l\'output par un jinja',required=False)
	parser.add_argument("-s", "--savefile",action="store",help="Save to dump File")
	parser.add_argument("-e", "--exportcsv",action="store",help="Résultat sous forme fichier csv",required=False)
	parser.add_argument("--xlsx",action="store",help="Résultat sous forme fichier excel",required=False)
	parser.add_argument("--inverse",action="store_true",help="inverse le résultat",default=False,required=False)
	group3.add_argument("-i", "--infonetmap",action="store_true",help="Ajoute les informations netmap sur le prefix uniquement avec option e",required=False)
	group3.add_argument("-c", "--connected",action="store_true",help="Ajoute les informations sur l'interface d'origine uniquement avec option e",required=False)
	group3.add_argument("-t","--trip",action="store_true",help="Translation next-hop type tr-ip",required=False)
	
	
	args = parser.parse_args()
	
	if args.prefix_filter or args.route_ip:
		try:
			infoPrefix=[]
			if args.prefix_filter:
				infoPrefix=args.prefix_filter.split(':')
			if args.route_ip:
				infoPrefix=args.route_ip.split(':')
			ListeVrf=infoPrefix[:-1]
			Net=infoPrefix[-1]
			if args.prefix_filter:
				netfilter=IPNetwork(Net)
			if args.route_ip:
				ipfilter=IPAddress(Net)

		except ValueError:
			parser.error("--prefix-filter is a IP Network")
		except IndexError:
			parser.error("--prefix-filter format:VRF1:VRF2:...:VRFN:PREFIX")

	if args.vrf and args.liste_nexthop:
		parser.error("--liste-nexthop not compatible with --vrf (feature coming soon)")
		
	if args.inverse and not args.nexthop:
		parser.error("--inverse works only with --nexthop")
	
	if args.nexthop is None and args.Print is None and args.savefile is None and args.liste_nexthop is None and args.exportcsv is None and not args.Print and not args.vrf:
		parser.error("at least one of -n and -P required without -s")
		
	if args.infonetmap and not (args.exportcsv or args.xlsx):
		parser.error("-i require -e or --xlsx")
		
	if len(args.nexthop)==1:
		args.nexthop=args.nexthop[0]
		
	elif len(args.nexthop)>1:
		args.liste_nexthop=args.nexthop
		args.nexthop=None
		
	mode=""
	if args.inverse:
		mode="inverse"
		
	if args.output or args.dumpfile:
		if args.output:
			RT__=checkroute.table_routage_allVRF(nom_fichier=args.output)
		elif args.dumpfile:
			RT__=checkroute.table_routage_allVRF(dump=args.dumpfile)
		

			
		if args.nexthop:
			if args.vrf:
				RT__Vrf=RT__.extract_vrf(args.vrf)
				RT__Filtered=checkroute.table_routage_allVRF(dict_RT=RT__Vrf.extract_gateway(args.nexthop,mode=mode))
			else:
				RT__Filtered=checkroute.table_routage_allVRF(dict_RT=RT__.extract_gateway(args.nexthop,mode=mode))
		
			if args.savefile :
				RT__Filtered.save(args.savefile)
			
			if args.exportcsv:
				
				if args.infonetmap:
					writeCsv(addInfoNetmap(RT__.get_liste(),NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))),args.exportcsv)
					
				elif args.connected:
					writeCsv(addInfoConnected(RT__Filtered.get_liste()),args.exportcsv)
					
				elif args.trip:
					writeCsv(addInfoNH(RT__Filtered.get_liste()),args.exportcsv)
				else:
					writeCsv(RT__Filtered.get_liste(),args.exportcsv)
				
		elif args.liste_nexthop:
			RT__Filtered=RT__.extract_gateways(args.liste_nexthop)
			
			if args.exportcsv:
				writeCsv(RT__Filtered.get_liste(),args.exportcsv)
				
		elif args.protocol:
			RT__Filtered=RT__.extract_protocol(args.protocol)
			
			if args.exportcsv:
				writeCsv(RT__Filtered.get_liste(),args.exportcsv)
				
		elif args.vrf:
			RT__Filtered=RT__.extract_vrf(args.vrf)
			
			if args.exportcsv:
				writeCsv(RT__Filtered.get_liste(),args.exportcsv)
				
				if args.infonetmap:
					writeCsv(addInfoNetmap(RT__.get_liste(),NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))),args.exportcsv)
					
				elif args.connected:
					writeCsv(addInfoConnected(RT__.get_liste()),args.exportcsv)
					
				elif args.trip:
					writeCsv(addInfoNH(RT__.get_liste()),args.exportcsv)
					
			if args.savefile :
				RT__Filtered.save(args.savefile)
			
		elif args.prefix_filter:
			if not ListeVrf:
				ListeVrf=RT__.getAllVRF()
				
			RT__Filtered=RT__.filteredByPrefix(ListeVrf,Net)
			
			if args.xlsx:
				if args.infonetmap:
					resultat=addInfoNetmap(RT__Filtered.get_dict(),NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP)))
					for vrf in resultat:
						resultat[vrf].insert(0,['PROTOCOL','PREFIX','NH','INFONETMAP'])
					xlsMatrix(args.xlsx,resultat)
				else:
					resultat=RT__Filtered.get_dict()
					for vrf in resultat:
						resultat[vrf].insert(0,['PROTOCOL','PREFIX','NH'])
					xlsMatrix(args.xlsx,resultat)
			
		elif args.route_ip:
			if not ListeVrf:
				ListeVrf=RT__.getAllVRF()
				
			RT__Filtered=RT__.filteredByIP(ListeVrf,Net)
				
		elif args.exportcsv:
				writeCsv(RT__.get_liste(),args.exportcsv)
				
				if args.infonetmap:
					writeCsv(addInfoNetmap(RT__.get_liste(),NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))),args.exportcsv)
					
				elif args.connected:
					writeCsv(addInfoConnected(RT__.get_liste()),args.exportcsv)
					
				elif args.trip:
					writeCsv(addInfoNH(RT__.get_liste()),args.exportcsv)
					


				
	
	if args.savefile and args.nexthop is None and args.protocol is None and args.vrf is None:
		RT__.save(args.savefile)
		
		if args.exportcsv:
				writeCsv(RT__.get_liste(),args.exportcsv)
				
				if args.infonetmap:
					writeCsv(addInfoNetmap(RT__.get_liste(),NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))),args.exportcsv)

					
				elif args.connected:
					writeCsv(addInfoConnected(RT__.get_liste()),args.exportcsv)
					
				elif args.trip:
					writeCsv(addInfoNH(RT__.get_liste()),args.exportcsv)
					
	elif args.savefile:
		try:
			RT__Filtered.save(args.savefile)
		except NameError:
			RT__.save(args.savefile)
			
	if args.list_all_nexthop:
		listNH={}
		try:
			listNH=RT__Filtered.getNH()
		except NameError:
			listNH=RT__.getNH()
			
		if args.trip:
			ppr(addInfoToListNH(listNH))
		else:
			ppr(listNH)
	
	if args.list_all_vrf:
		listVRF=[]
		try:
			listVRF=RT__Filtered.getAllVRF()
		except NameError:
			listVRF=RT__.getAllVRF()
			
		ppr(listVRF)
		
	if args.Print:
		if args.nexthop or args.protocol or args.vrf or args.prefix_filter or args.liste_nexthop or args.route_ip:
			if args.format:
				print(RT__Filtered.format(args.format))
			else:
				print(RT__Filtered)
			
		else:
			if args.format:
				print(RT__.format(args.format))
			else:
				print(RT__)
			
				
	if args.yaml:
		MRTObj=MultipleRTContainer(args.yaml)

			
		if args.prefix_filter:
			RT_Filtered_dict=MRTObj.filteredByPrefix(ListeVrf,Net)
			ppr(RT_Filtered_dict)
			
		if args.route_ip:
			RT_Filtered_dict=MRTObj.filteredByIP(ListeVrf,Net)
			ppr(RT_Filtered_dict)
		
	
