#!/usr/bin/env python3.8
# coding: utf-8


import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
from connexion import *
from ParsingShow  import getShortPort, getLongPort, ParseStatusCisco , ParseCdpNeighborDetailString
import re
import cache as cc
from shut import groupIfByHostname , readCsv

TAG_PREFIX_STATUS='STATUS_'
TAG_PREFIX_CDP='CDPDETAIL_'

def getInterfaceStatus(equipment__):

	ifStatus=None
	
	commande=f'show interface status'
	#                    connexion(equipement(equipment__)     ,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log"            ,commande_en_ligne=commande,timeout=20 ,verbose=False)
	con_get_ifStatus_cur=connexion(equipement(equipment__)     ,None,'SSH',"TMP/"+equipment__.lower()+"_shifStatus.log"       ,commande_en_ligne=commande,timeout=50,verbose=False)
	ifStatus=con_get_ifStatus_cur.launch_withParser(ParseStatusCisco)
	
	return ifStatus

def getCdpNeighborDetail(equipment__):

	ifStatus=None
	
	commande=f'show cdp neighbor detail'
	#                     connexion(equipement(equipment__)     ,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log"            ,commande_en_ligne=commande,timeout=20 ,verbose=False)
	con_get_cdpDetail_cur=connexion(equipement(equipment__)     ,None,'SSH',"TMP/"+equipment__.lower()+"_shcdpdetail.log"      ,commande_en_ligne=commande,timeout=50,verbose=False)
	ifStatus=con_get_cdpDetail_cur.launch_withParser(ParseCdpNeighborDetailString)
	
	return ifStatus
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-i","--interconnection",action="store",help="csv containing interconnexion",required=True)
	parser.add_argument("--cache",action="store_true",help="Use cache if it is possible")
	args = parser.parse_args()
	
	intercos=readCsv(args.interconnection)
	ifByHostGrouped=groupIfByHostname(intercos,notGrouped=True)	
	
	Status={}
	cacheStatus={}
	
	CdpDetail={}
	cacheCdpDetail={}
	
	for hostname in ifByHostGrouped:
		TAG_STATUS_HOST=f'{TAG_PREFIX_STATUS}{hostname}'
		TAG_CDP_HOST=f'{TAG_PREFIX_CDP}{hostname}'
		cacheStatus[hostname]=cc.Cache(TAG_STATUS_HOST)
		cacheCdpDetail[hostname]=cc.Cache(TAG_CDP_HOST)
		if args.cache:		

			if cacheStatus[hostname].isOK():
				print(f'Caching status is present for {hostname}')
				Status[hostname]=cacheStatus[hostname].getValue()
			else:
				print(f'Caching status  is not present for {hostname}')
				Status[hostname]=getInterfaceStatus(hostname)
				cacheStatus[hostname].save(Status[hostname])
				
			if cacheCdpDetail[hostname].isOK():
				print(f'Caching cdp is present for {hostname}')
				CdpDetail[hostname]=cacheCdpDetail[hostname].getValue()
			else:
				print(f'Caching cdp  is not present for {hostname}')
				CdpDetail[hostname]=getCdpNeighborDetail(hostname)
				cacheCdpDetail[hostname].save(CdpDetail[hostname])			
	 
		else:
			Status[hostname]=getInterfaceStatus(hostname)
			CdpDetail[hostname]=getCdpNeighborDetail(hostname)
			cacheStatus[hostname].save(Status[hostname])
			cacheCdpDetail[hostname].save(CdpDetail[hostname])
	
	interfaceStatusNotConformed={}
	
	print('Check interface Status')
	for hostname in ifByHostGrouped:
		for interface in ifByHostGrouped[hostname]:
			try:
				statusCur=Status[hostname][interface][1]
			except KeyError as E:
				pdb.set_trace()
				print(E)

			if statusCur !='connected':
				if hostname not in interfaceStatusNotConformed:
					interfaceStatusNotConformed[hostname]=[interface]
				else:
					interfaceStatusNotConformed[hostname].append(interface)	


	print('interface Status not connected')
	ppr(interfaceStatusNotConformed)
	
	
	intercoNotConformed=[]
	print('Check Interconnection with cdp')
	
	def checkInterfaceConformed(host__,if__):

		if host__ not in interfaceStatusNotConformed:
			return True
		try:
			if if__ in interfaceStatusNotConformed[host__]:
				return False
		except KeyError as E:
			pdb.set_trace()
			print(E)
	
		return True

	def getCdpNeighbor(host__,if__):
		try:
			Neigh=CdpDetail[host__][getLongPort(if__)]
			return Neigh
		except KeyError as E:
			print(E)
			return
			
		
	
	for interco in intercos:
		host=interco[0]
		ifCur=interco[1]
		neighbor=interco[2]
		ifCurNeighbor=interco[3]
		
		if (checkInterfaceConformed(host,ifCur)):
			cdpNeigh=getCdpNeighbor(host,ifCur)
			if cdpNeigh:
				cdpNeighborHost=cdpNeigh['Neighbor']
				cdpNeighborIf=cdpNeigh['Interface Neighbor']
				if cdpNeighborHost.upper() != neighbor or ifCurNeighbor !=getShortPort(cdpNeighborIf):
					intercoNotConformed.append(interco+['!=Real Cdp Neighbor']+[cdpNeighborHost.upper(),getShortPort(cdpNeighborIf)])
			else:
				print(f'cdp neighbor is empty for interface {host} {ifCur}')
		else:
			print(f'interface {host} {ifCur} is not connected')
			
			
	print('interco not conformed')
	ppr(intercoNotConformed,width=400)
