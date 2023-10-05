#!/usr/bin/env python3.8
# coding: utf-8


from ParsingShow import ParseCdpNeighborDetail,ParseCdpNeighborDetailString,writeCsv,getEquipementFromFilename,getLongPort
import csv
import checkroute
import sys
import os
import argparse
import glob
import pdb
import pickle
import re
from io import StringIO
from pprint import pprint as ppr
from pprint import pformat as pprs

class interconnexion(object):
	def __init__(self,host_src,port_src,host_dest,port_dest):
		self.host_source=host_src
		self.host_destination=host_dest
		self.port_source=port_src
		self.port_destination=port_dest
		
	def __eq__(self,other_interco):
		return (self.host_source==other_interco.host_source and self.host_destination==other_interco.host_destination and self.port_source==other_interco.port_source and self.port_source==other_interco.port_source ) or (self.host_source==other_interco.host_destination and self.host_destination==other_interco.host_source and self.port_source==other_interco.port_destination and self.port_destination==other_interco.port_source ) 
		
	def __str__(self):
		return self.host_source+";"+self.port_source+";"+self.host_destination+";"+self.port_destination

	def __repr__(self):
		return self.host_source+";"+self.port_source+";"+self.host_destination+";"+self.port_destination
		
	def toList(self):
		return [self.host_source,self.port_source,self.host_destination,self.port_destination]	

class interconnexions(object):
	def __init__(self):
		self.liste_interconnexion=[]
		
	def add_element(self,interco__):
		if interco__ not in self:
			self.liste_interconnexion.append(interco__)
			
	def __contains__(self,interco__):
		result=False
		for interco__cur in self.liste_interconnexion:
			if interco__cur == interco__:
				result=True
				
		return result
		
	def __str__(self):
		resultat=StringIO()
		for interco__ in self.liste_interconnexion:
			resultat.write(str(interco__)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	def toList(self):
		return [interco.toList() for interco in self.liste_interconnexion]		

class cdpEntry(object):

	def __init__(self,hostname,interface_local,interface_neighbor):
		self.hostname=hostname
		self.interface=interface_local
		self.interface_neighbor=interface_neighbor
		
	def __str__(self):
		#pdb.set_trace()
		return "Interface:"+self.interface+" Hostame:"+self.hostname+"("+self.interface_neighbor+")"
		
	def __repr__(self):
		#pdb.set_trace()
		return "Interface:"+self.interface+" Hostame:"+self.hostname+"("+self.interface_neighbor+")"
		
class cdpEntries(object):

	def __init__(self,output="OUTPUT/tigr4-odin-svc-a1-cdp.log",dump="DUMP/CDP/tigr4-odin-svc-a1.dump",Str="",Dict={}):
		self.entries=[]
		self.entries_dict={}
		if Str:
			CDPAll=ParseCdpNeighborDetailString(output)
			
			for interface in CDPAll.keys():
				self.entries.append(cdpEntry(CDPAll[interface]['Neighbor'],interface,CDPAll[interface]['Interface Neighbor']))
		elif Dict:
			CDPAll=Dict

			for interface in CDPAll.keys():
				self.entries.append(cdpEntry(CDPAll[interface]['Neighbor'],interface,CDPAll[interface]['Interface Neighbor']))			
			
		elif output:
			CDPAll=ParseCdpNeighborDetail(output)
			
			for interface in CDPAll.keys():
				self.entries.append(cdpEntry(CDPAll[interface]['Neighbor'],interface,CDPAll[interface]['Interface Neighbor']))
		if dump:
			pass
		
		for entry in self.entries:
			self.entries_dict[entry.interface]=entry
		
	def __str__(self):
		resultat=StringIO()
		for entry in self.entries:
			resultat.write(str(entry)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def __repr__(self):
		resultat=StringIO()
		for entry in self.entries:
			resultat.write(str(entry)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def filterRegex(self,regex):
		resultat=[]
		for entry in self.entries:
			if re.search(regex,entry.hostname):
				resultat.append(entry)
				
		return resultat
		
class DC_cdp(object):
	def __init__(self,repertoire="",dump="",dictHost={},dictResult={}):
		self.cdpEntries_DC={}
		
		if dictResult:
			for equipement__ in dictResult:
				self.cdpEntries_DC[equipement__]=cdpEntries(Dict=dictResult[equipement__])
			self.interco=self.init_interconnexion()			
		if dictHost:
			for equipement__ in dictHost:
				self.cdpEntries_DC[equipement__]=cdpEntries(Str=dictHost[equipement__])
			self.interco=self.init_interconnexion()
		if repertoire:
			Liste_file_show_cdp=glob.glob(repertoire+'/*.log')
			for file_show_cdp in Liste_file_show_cdp:
				file_show_cdp__=file_show_cdp.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_cdp__).upper()
				self.cdpEntries_DC[equipement__]=cdpEntries(output=file_show_cdp)
				#pdb.set_trace()*******
			self.interco=self.init_interconnexion()
		if dump:
			self.load(dump)
			
		#pdb.set_trace()
			
	def __str__(self):
	
		resultat=StringIO()
		for hostname in self.cdpEntries_DC.keys():
			resultat.write("Equipement:"+hostname+"\n")
			resultat.write(str(self.cdpEntries_DC[hostname]))
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
	

	def __getitem__(self, key):
		return self.cdpEntries_DC[key]
		
	def init_interconnexion(self):
		resultat=interconnexions()
		for hostname in self.cdpEntries_DC.keys():
			for entry__ in self.cdpEntries_DC[hostname].entries:
				resultat.add_element(interconnexion(hostname,entry__.interface,entry__.hostname,entry__.interface_neighbor))
			
		return resultat
		
	def print_interconnexion(self):
		print(self.interco)
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
		
		try:
			self.cdpEntries_DC=dc.cdpEntries_DC
			self.interco=dc.interco

		except:
			print('ERROR')
			
	def getNeighbor(self,equipement,interface):
		resultat=None
		
		try:
			#pdb.set_trace()
			resultat=self.cdpEntries_DC[equipement.upper()].entries_dict[getLongPort(interface)]
		
		except KeyError:
			pass
			
		return resultat
		
	def getNeighbors(self,equipement):
		resultat=None
		
		try:
			#pdb.set_trace()
			resultat=self.cdpEntries_DC[equipement.upper()].entries_dict
		
		except KeyError:
			pass
			
		return resultat
	
	def getAllhosts(self,regex=None):
	
		ListHosts=[]
		
		for host in self.cdpEntries_DC:
			if host not in ListHosts:
				ListHosts.append(host)
			for entry in self.cdpEntries_DC[host].entries:
				neighbor=entry.hostname
				if neighbor not in ListHosts:
					ListHosts.append(neighbor)
					
		if not regex:
			return ListHosts
		else:
			test_regex=lambda y: True if re.search(regex,y,re.IGNORECASE)  else False
			result=list(filter(test_regex,ListHosts))
			
			return result
	

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-r", "--repertoire",action="store",help="Répertoire contenant les output show cdp neighbor detail")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump type cdp")
	parser.add_argument("-e", "--exportcsv",action="store",help=u"Résultat sous forme fichier csv",required=False)
	parser.add_argument("-s", "--save",action="store",help=u"Résultat dans fichier dump",required=False)
	parser.add_argument("-l", "--list-hosts",dest='filter_hosts',action="store",help=u"Regex to filter hosts",required=False)
	args = parser.parse_args()
	
	if args.repertoire:
		A=DC_cdp(repertoire=args.repertoire)
	elif args.dumpfile:
		A=DC_cdp(dump=args.dumpfile)
		
	print(str(A))
	
	if args.save:
		A.save(args.save)
		
	A.print_interconnexion()
	
	if args.filter_hosts:

		hosts=A.getAllhosts(args.filter_hosts)
		ppr(hosts)
	