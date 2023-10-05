#!/usr/bin/env python3.8
# -*- coding: utf-8 -*- 

from ParsingShow import DC,writeCsv
import csv
import pdb
import re
from cdpEnv import DC_cdp,cdpEntries,cdpEntry,interconnexions,interconnexion
from pprint import pprint as ppr

import argparse


def exclude_cdpneigbor(liste_port,cdp__,dc__):
	resultat__=[]
	for entry in liste_port:
		#pdb.set_trace()
		if re.match ('Po|port-channel',entry[1]):
			interfaces=dc__.getInterfaceFromPo(entry[0],entry[1])
			for int__ in interfaces:
				if not cdp__.getNeighbor(entry[0],int__):
					resultat__.append(entry)
		else:
			if not cdp__.getNeighbor(entry[0],entry[1]):
				resultat__.append(entry)
	return resultat__

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump",required=True)
	parser.add_argument("-v", "--vlan",action="store",help="Liste des vlans pour lesquels il faut extraire les ports",required=False)
	parser.add_argument("-m", "--mac",action="store",help="Mac(s) pour lesquels il faut extraire les ports,separees par des virgules",required=False)
	parser.add_argument("-i", "--ip",action="store",help="IP(s) pour lesquels il faut extraire les ports,separees par des virgules",required=False)
	parser.add_argument("--description",action="store",help="Regex pour filter les ports selon la description",required=False)
	parser.add_argument("-p", "--print",action="store",help="Liste les equipements du dump",required=False)
	parser.add_argument("-c", "--cmp_mac",action="store_true",help="Avec option -i recherche la mac",required=False)
	parser.add_argument("-e", "--exportcsv",action="store",help="Envoie d",required=False)
	parser.add_argument("-x", "--xclude",action="store",help="Exclue les ports avec un Neighbor CDP, parametre dump type CDP,option c et v obligtoires",required=False)
	parser.add_argument("-l","--liste",action="store",help="Liste de mac",required=False)
	parser.add_argument("--liste-mac-vlan",dest='liste_mac_vlan',action="store",help="Liste de vlan + mac",required=False)
	parser.add_argument("--pretty-print",dest='pretty',action="store_true",help="Pretty print",required=False)
	parser.add_argument("--only-with-mac",dest='onlywithmac',action="store_true",help="extract only port with mac",required=False)
	args = parser.parse_args()
	
	dc=DC()
	dc.load(args.dumpfile)
	
	if args.vlan:
		if not args.xclude:
			result=dc.extract_port_vlans(args.vlan,noEmptyEntry=args.onlywithmac)
		else:
			result=exclude_cdpneigbor(dc.extract_port_vlans(args.vlan,noEmptyEntry=args.onlywithmac),DC_cdp(dump=args.xclude),dc)
	elif args.mac:
		if not args.xclude:
			result=dc.extract_macs(args.mac)
		else:
			result=exclude_cdpneigbor(dc.extract_macs(args.mac),DC_cdp(dump=args.xclude),dc)
	elif args.ip:
		result=dc.extract_ip(args.ip)
	elif args.description:
		result=dc.extract_description(args.description)
	elif args.liste:
		with open(args.liste) as fichier:
			liste_mac__=fichier.readlines()
			liste_mac=[ mac.strip() for mac in liste_mac__ ]
			result=[]
			for mac in liste_mac:
				if not args.xclude:
					result_cur=dc.extract_macs(mac)
					for entry in result_cur:
						if not re.search('ODIN-C',entry[3],re.IGNORECASE):
							print([mac]+entry)
							if args.cmp_mac:
								infoComp=dc.getInfoMac(mac)
								result.append([mac]+entry+infoComp[1:])
							else:
								result.append([mac]+entry)
				else:
					result_cur=exclude_cdpneigbor(dc.extract_macs(mac),DC_cdp(dump=args.xclude),dc)
					for entry in result_cur:			
						if not re.search('ODIN-C',entry[3],re.IGNORECASE):
							print([mac]+entry)
							if args.cmp_mac:
								infoComp=dc.getInfoMac(mac)
								result.append([mac]+entry+infoComp[1:])
							else:
								result.append([mac]+entry)
	elif args.liste_mac_vlan:
		with open(args.liste_mac_vlan) as fichier:
			liste_mac__=fichier.readlines()
			list_vlan_mac=[]
			for info__ in liste_mac__:
				info_lst=info__.split()
				vlan=info_lst[0]
				mac=info_lst[1]
				list_vlan_mac.append((vlan,mac))
			result=[]
			for info__ in list_vlan_mac:
				vlan=info__[0]
				mac=info__[1]
				if not args.xclude:
					result_cur=dc.extract_macs(mac,vlan=vlan,noEmptyEntry=args.onlywithmac)
					for entry in result_cur:
						if not re.search('ODIN-C',entry[3],re.IGNORECASE):
							if args.cmp_mac:
								infoComp=dc.getInfoMac(mac,vlan=vlan)
								result.append([vlan,mac,entry,infoComp[1:]])
							else:
								result.append([vlan,mac,entry])


				else:
					#test=dc.extract_macs(mac,vlan=vlan)
					#print('test:',mac,vlan,test)
					result_cur=exclude_cdpneigbor(dc.extract_macs(mac,vlan=vlan,noEmptyEntry=args.onlywithmac),DC_cdp(dump=args.xclude),dc)
					info_cur=[]
					print(result_cur)
					for entry in result_cur:			
						if not re.search('ODIN-C',entry[3],re.IGNORECASE):
							if args.cmp_mac:
								infoComp=dc.getInfoMac(mac,vlan=vlan)
								result.append([vlan,mac,entry]+infoComp[1:])
							else:
								result.append([vlan,mac,entry])
					if not result_cur:
						if args.cmp_mac:
							result.append([vlan,mac,None,None])
						else:
							result.append([vlan,mac,None])
	
	if not args.pretty:
		print(result)
	else:
		ppr(result,width=100)
	if args.cmp_mac and args.ip:
		result_cmp_mac=None
		try:
			if not args.xclude:
				result_cmp_mac=dc.extract_macs(result[0][0])
			else:
				result_cmp_mac=exclude_cdpneigbor(dc.extract_macs(result[0][0]),DC_cdp(dump=args.xclude),dc)
			print(result_cmp_mac)
			fichier_mac=(args.ip+"__"+result[0][0]).replace('.','_')+".csv"
			print("Resultat Complementaires mac dans RESULT/"+fichier_mac)
			writeCsv(result_cmp_mac,"RESULT/"+fichier_mac)
		except IndexError as error_index:
			print(str(result))
			print(error_index)
			
	
	if args.exportcsv:
		writeCsv(result,args.exportcsv)
	
	