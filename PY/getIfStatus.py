#!/usr/bin/env python3.8
# coding: utf-8


import pdb
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
from connexion import *
from ParsingShow  import ParseStatusCisco , ParseDescriptionCiscoOrNexus, getShortPort ,  getLongPort
import re
import cache as cc
from cdpEnv import *
import more_itertools as mit

TAG_PREFIX_STATUS='STATUS_'
TAG_PREFIX_DESC='DESC_'



def getInterfaceStatus(equipment__):

	ifStatus=None
	
	commande=f'show interface status'
	con_get_ifStatus_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shifStatus.log","TMP",commande,timeout=300,verbose=False)
	ifStatus=con_get_ifStatus_cur.launch_withParser(ParseStatusCisco)
	
	return ifStatus

def getInterfaceDesc(equipment__):

	ifDesc=None
	
	commande=f'show interface description'
	con_get_ifDesc_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shifDesc.log","TMP",commande,timeout=300,verbose=False)
	ifDesc=con_get_ifDesc_cur.launch_withParser(ParseDescriptionCiscoOrNexus)
	
	return ifDesc
	
def extractConnected(ifStatus):
	return { interface:attribute for interface,attribute in ifStatus.items() if attribute[1]=='connected' and '.' not in interface and 'Eth' in interface}

def extractDesc(ifDesc,portsConnected,portsCdpMatch,regex):
	otherPorts=[]
	for port__ in portsConnected:
		if port__ not in portsCdpMatch:
			try:
				descCur=ifDesc[port__].strip()
			except KeyError as E:
				pdb.set_trace()
				print(E)
				raise E
			if re.search(regex,descCur,re.IGNORECASE):
				otherPorts.append(port__)

	return otherPorts
	
def groupList(integerStrList)	:

	integerStrListSorted=sorted(integerStrList)
	try:
		integerList=list(map(int,integerStrListSorted))
	except ValueError as E:
		pdb.set_trace()
		print(E)
	
	groupInt=[list(map(str,group)) for group in mit.consecutive_groups(integerList)]
	
	return groupInt
	
	
def groupInterface(interfaces):
	
	ifByModule={}
	for interface in interfaces:
		interfaceLst=interface.split('/')
		portNumber=interfaceLst[-1]
		prefix="".join(interfaceLst[:-1])
		if prefix in ifByModule:
			ifByModule[prefix].append(portNumber)
		else:
			ifByModule[prefix]=[portNumber]
	
	ifByModuleGrp={ interface:groupList(port) for interface,port in ifByModule.items()}
	
	interfaceGrp=[]
	for interface,ports in ifByModuleGrp.items():
		for portGrp in ports:
			if len(portGrp)>1:
				interfaceCur=interface+'/'+portGrp[0]+'-'+portGrp[-1]
			else:
				interfaceCur=interface+'/'+portGrp[0]
			interfaceGrp.append(interfaceCur)
		
	
	return interfaceGrp
	
def explodeInterface(ports):
	result=[]
	if re.search('-',ports):
		portsListFormat=ports.split('/')
		extremity=portsListFormat[-1].split('-')
		minPort=extremity[0]
		maxPort=extremity[-1]
		return ["/".join(portsListFormat[:-1])+'/'+str(index) for index in range(int(minPort),int(maxPort)+1)]
	else:
		return ports


	
def getInfoPorts(equipement,port,cdps,status,description):

	if '-' in port:
		ports=explodeInterface(port)
		cdpNeigh={}
		descPort={}
		
		for port__ in ports:
			try:
				cdpNeighCur=cdps[equipement].entries_dict[getLongPort(port__)].hostname
			except KeyError:
				cdpNeighCur=None
				
			try:
				descPortCur=description[port__].strip()
			except KeyError:
				descPortCur=None
			except IndexError:
				descPort=None
			cdpNeigh[port__]=cdpNeighCur
			descPort[port__]=descPortCur
			
	else:
		try:
			cdpNeigh=cdps[equipement].entries_dict[getLongPort(port)].hostname
		except KeyError:
			cdpNeigh=None
			
		try:
			descPort=description[port].strip()
		except KeyError:
			descPort=None
		except IndexError:
			descPort=None		
		
	
	return {'cdpNeigh': cdpNeigh, 'description':descPort}
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument("-e","--equipment",action="store",help="hostname",required=True)
	group.add_argument("--shutdown",action="store_true",help="get shut down config")
	group.add_argument("--activate",action="store_true",help="get no shut down config")
	parser.add_argument("--cache",action="store_true",help="use cache to get interface status",required=False)
	parser.add_argument("--cdp-dump",dest='cdpDump',action="store",help="Dump CDP env",required=False)
	parser.add_argument("--reg-exclude",dest='regExclude',action="append",help="regex match neighbor cdp/desc to exclude,possible format desc::regex ",required=False)
	parser.add_argument("--reverse",action="store_true",help="inverse group excluded")
	args = parser.parse_args()
	
	if args.cache:
		
		TAG_STATUS_HOST=f'{TAG_PREFIX_STATUS}{args.equipment.upper()}'
		TAG_DESC_HOST=f'{TAG_PREFIX_DESC}{args.equipment.upper()}'
		cacheStatus=cc.Cache(TAG_STATUS_HOST)
		cacheDesc=cc.Cache(TAG_DESC_HOST)
		if cacheStatus.isOK():
			print(f'Caching status is present for {args.equipment.upper()}')
			Status=cacheStatus.getValue()
		else:
			print(f'Caching status  is not present for {args.equipment.upper()}')
			Status=getInterfaceStatus(args.equipment)
			cacheStatus.save(Status)
			
		if cacheDesc.isOK():
			print(f'Caching description is present for {args.equipment.upper()}')
			Desc=cacheDesc.getValue()
		else:
			print(f'Caching description is not present for {args.equipment.upper()}')
			Desc=getInterfaceDesc(args.equipment)
			cacheDesc.save(Desc)		
		 
		 
		 
	else:
		Status=getInterfaceStatus(args.equipment)
		Desc=getInterfaceDesc(args.equipment)
		
	pdb.set_trace()
	onlyConnected=extractConnected(Status)
	#ppr(onlyConnected)
	
	if args.cdpDump:
		cdpData=DC_cdp(dump=args.cdpDump)
			
		if args.regExclude:
			otherInterfaces={}
			cdpEntryFiltered={}
			otherInterfaceMatchDesc={}
			allOtherInterface=[]
			alreadyUsed=[]
			
			if args.reverse:
				args.regExclude.reverse()
			try:
				for filterRegDesc in args.regExclude:
					if re.search('::',filterRegDesc):
						filterRegDescList=filterRegDesc.split('::')
						descrReg=filterRegDescList[0]
						filterReg=filterRegDescList[1]
					else:
						descrReg=filterRegDesc
						filterReg=filterRegDesc		
						
					cdpEntryFiltered[descrReg]=cdpData[args.equipment].filterRegex(filterReg)
					otherInterfaces[descrReg]=[ getShortPort(cdpCur.interface) for cdpCur in cdpEntryFiltered[descrReg] if getShortPort(cdpCur.interface) not in alreadyUsed]
					otherInterfaceMatchDesc[descrReg]=[ ifs__ for ifs__ in extractDesc(Desc,list(onlyConnected.keys()),otherInterfaces[descrReg],filterReg) if ifs__ not in alreadyUsed]
					otherInterfaces[descrReg]+=otherInterfaceMatchDesc[descrReg]
					
					for interface in otherInterfaces[descrReg]:
						allOtherInterface.append(interface)
						alreadyUsed.append(interface)
						
						
			except KeyError as E:
				print(f'Cdp Dump do not contains data for {args.equipment}')
				print(E)
				
			#ppr(cdpEntryFiltered)				
			#ppr(otherInterfaces)
		
		
	
			ports=list(filter(lambda y: y not in allOtherInterface , onlyConnected))
		else:
			ports=groupInterface(onlyConnected)			
	else:
		ports=groupInterface(onlyConnected)
	
	ppr(ports)
	
	if args.shutdown or args.activate:
		print('\n\n\nCONFIG\n\n')
		if args.regExclude:
			for desc in otherInterfaces:
				print('!'+desc)
				for port in groupInterface(otherInterfaces[desc]):
					print('interface '+port)

					infoCur=getInfoPorts(args.equipment,port,cdpData,Status,Desc)
					print('!'+pprs(infoCur).replace('\n','\n!'))
					if args.shutdown :
						print('  shut')
					if args.activate:
						print(' no shut')					
					print('!\n')	
				print('!')
				print('!')
				print('!')

			print('!Remaining Ports:')
			for port in ports:	
				print('interface '+port)
				infoCur=getInfoPorts(args.equipment,port,cdpData,Status,Desc)
				print('!'+pprs(infoCur).replace('\n','\n!'))
				if args.shutdown :
					print('  shut')
				if args.activate:
					print(' no shut')		
				print('!\n')	
		else:
			for port in ports:
	
				print('interface '+port)
				if args.cdpDump:
					infoCur=getInfoPorts(args.equipment,port,cdpData,Status,Desc)
					print('!'+pprs(infoCur).replace('\n','\n!'))
					if args.shutdown :
						print('  shut')
					if args.activate:
						print(' no shut')		
				print('!\n')
	