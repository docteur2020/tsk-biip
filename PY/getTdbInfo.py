#!/usr/bin/env python3.8
# coding: utf-8

import csv
import pdb
import argparse
import pickle
import os
import pprint
import glob
from pathlib import Path
from cdpEnv import interconnexion
from tabulate import tabulate
from collections import OrderedDict
import xlsxwriter
import pyparsing as pp
import xlrd
import yaml
from pprint import pprint as ppr
import re


PATH_TDB_EXCEL="/home/d83071/EXCEL/TDB"
PATH_TDB_DUMP="/home/d83071/EXCEL/TDB/DUMP"
TDB_HEADER_FILE_YAML="/home/d83071/yaml/tdb_header.yml"
TDB_HEADER_CUSTOM_FILE_YAML="/home/d83071/yaml/tdb_header_custom.yml"


def splitFileByLine(filename):

	lines=[]
	with open(filename) as file:
		lines_tmp=file.read().split('\n')
		lines=[ line.split()[0].strip() for line in lines_tmp if line]
		
	return lines

def loadYaml(file):
	with open(file, 'r') as yml__:
		yaml_obj = yaml.load(yml__,Loader=yaml.SafeLoader)

	return yaml_obj

def get_last_dump(directory):
	lastDump=max(glob.glob(directory+'/*'),key=os.path.getctime)
	print(f'Last Dump:{lastDump}')
	return lastDump
	
def print_tabulate_dict(dict__):
	print(tabulate([[ val for val in dict__.values()]] ,headers=dict__.keys(),tablefmt='psql'))
	
def getbasefilename(file_with_path):
	return Path(file_with_path).stem
	
def ParseMac(macStr):
	resultat=None
	Octet=pp.Word(pp.nums+'abcdef'+'ABCDEF',exact=2).setParseAction(lambda t : t[0].upper())
	Separator=pp.Word(':-. ',exact=1).setParseAction(pp.replaceWith(':'))
	MacWoSep=pp.Combine(6*Octet).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][4]+t[0][5]+":"+t[0][6]+t[0][7]+":"+t[0][8]+t[0][9]+":"+t[0][10]+t[0][11])
	MacCisco=pp.Combine((2*Octet+Separator)*2+(2*Octet)).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][5]+t[0][6]+":"+t[0][7]+t[0][8]+":"+t[0][10]+t[0][11]+":"+t[0][12]+t[0][13])
	MacUnix=pp.Combine((Octet+Separator)*5+Octet)
	MacSpec1=pp.Suppress(pp.Literal('SEP'))+MacWoSep
	MacSpec2=pp.Suppress(pp.Literal('0x'))+MacWoSep
	Mac=pp.MatchFirst([MacWoSep,MacCisco,MacUnix,MacSpec1,MacSpec2])
	try:
		resultat=Mac.parseString(macStr,parseAll=True).asList()[0]
	except  pp.ParseException as ppError:
		print(f"Vérifiez le format de l'adresse Mac:{macStr}")
		raise(ppError)
			 
	return resultat
	
def ParseIP(IPStr,mode="list"):

	
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	
	if mode=="list":
		resultat=[]
		parseResultIP=ipAddress.scanString(IPStr)
		resultat=[ip[0].asList()[0] for ip in parseResultIP ]
	else:
		resultat=None
		try:
			resultat=ipAddress.parseString(IPStr,parseAll=True).asList()[0]
		except pp.ParseException as ppError:
			print(f"Vérifiez le format de l'adresse IP:{IPStr}")
			raise(ppError)
		
	return resultat
	

class intercoTDB(interconnexion):
	def __init__(self,host_src,port_src,host_dest,port_dest,type,PathdbTDB=PATH_TDB_DUMP):
		super().__init__(host_src,port_src,host_dest,port_dest)
		self.type=type
		
		self.host_source=host_src
		self.host_destination=host_dest
		self.port_source=port_src
		self.port_destination=port_dest
		
		self.new_header=['Réf Câble','MA','Nom','SN','Model','DC','Salle','Baie','Position','Port','Type']
		self.header_tr={'MA':'Asset ID','Nom':'Usual name','SN':'Serial number','Model':'Model','Salle':'Room','Baie':'Cabinet','Position':'Rack position'}
		self.dbTDB=get_last_dump(PathdbTDB)
		self.info_src=self.getTDBInfo(self.host_source,self.port_source,self.type)
		self.info_dst=self.getTDBInfo(self.host_destination,self.port_destination,self.type)
		
		#print_tabulate_dict(self.info_src)
		#print_tabulate_dict(self.info_dst)
		
		
	def toList(self):
		return [self.host_source,self.port_source,self.host_destination,self.port_destination,self.type ]
		
	def toListComplete(self):
		return [element for element in self.info_src.values() ] + [element for element in self.info_dst.values() ] 

	def __str__(self):
		resultat=StringIO()
		for ligne in super().__str__().splitlines():
			resultat.write(ligne+";"+self.type)
		
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	def getTDBInfo(self,host__,port__,type__):
		resultat=OrderedDict()
		curTDBdb=tdbContainer(dump=self.dbTDB)
		curInfo=curTDBdb.getInfoEquipment(host__)
		
		
		for element in self.new_header:
			if element in self.header_tr.keys():
				try:
					resultat[element]=curInfo[self.header_tr[element]]
				except KeyError as e:
					pdb.set_trace()
					print(e)
					resultat[element]="INCOMPLETE"
					
			else:
				resultat[element]="TBD"
		
		resultat['Port']=port__
		resultat['Type']=type__
		
		return resultat
		
	
class intercoTDBContainer(object):
	def __init__(self,fichier_csv):
		self.headers=['hostSrc','portSrc','hostDst','portDst','type']
		reader=csv.DictReader(open(fichier_csv, "r",encoding="iso-8859-1"),fieldnames=self.headers,delimiter=';')
		self.intercos=[]
		
		for row in reader:
			self.intercos.append(intercoTDB(row['hostSrc'],row['portSrc'],row['hostDst'],row['portDst'],row['type'] ))
	
	def __repr__(self):
		return tabulate(self.toList(),headers=self.headers,tablefmt='psql')
	
	def __str__(self):
		return tabulate(self.toList(),headers=self.headers,tablefmt='psql')	
		
	def toList(self):
		return [ interco.toList() for interco in self.intercos ]
	
	def printer(self):
		print(str(self))
	
class tdbContainer(object):
	"TDB Container"
	
	def __init__(self,excel_file="",dump=""):
			
		if excel_file:
		
			try:
				xl_workbook = xlrd.open_workbook(excel_file,encoding_override='cp1252')
			except AssertionError as E:
				pdb.set_trace()
				print(E)
			sheet_names = xl_workbook.sheet_names()
			
			sheet_name=sheet_names[0]
			xl_sheet = xl_workbook.sheet_by_name(sheet_name)
			#reader=csv.DictReader(open(csv_file, "r",encoding="iso-8859-1"),delimiter=';')
			self.allHeader={ indice:value for indice,value in  enumerate(xl_sheet.row_values(0)) }
			self.header=loadYaml(TDB_HEADER_CUSTOM_FILE_YAML)
			self.allDataByHosts={}
			self.allDataBySN={}
			self.allDataByIPMain={}

			self.allData=[]
			
			for rownum in range(1,xl_sheet.nrows):
				try:
					self.allData.append({self.allHeader[id__]:str(int(xl_sheet.row_values(rownum)[id__])) for id__ in self.allHeader.keys()})
				except ValueError as E:
					self.allData.append({self.allHeader[id__]:str(xl_sheet.row_values(rownum)[id__]) for id__ in self.allHeader.keys()})
				
			nb_entry=len(self.allData)
			indice=1
			for row in self.allData:
				self.allDataByHosts[row['Nom de l\'équipement']]={ key:value for key , value in row.items() if key in self.header }
				self.allDataBySN[row['Numéro de série']]={ key:value for key , value in row.items() if key in self.header }
				
				if row['Adresse IP']:
					ip_curs=ParseIP(row['Adresse IP'])
					for ip_cur in ip_curs:
						if ip_cur not in self.allDataByIPMain:
							self.allDataByIPMain[ip_cur]=[]
						self.allDataByIPMain[ip_cur].append({ key:value for key , value in dict(row).items() if key in self.header })
						#print(f'ip_cur:{ip_cur}')

				indice+=1
		if dump:
			self.load(dump)
		
		
	def getInfoEquipment(self,hostname,mode='normal'):
		
		
		if mode=='normal':
			resultat={}
			try:
				resultat=self.allDataByHosts[hostname]
				#pprint.pprint(resultat)
			except KeyError as e:
				print('%s inconnue dans le fichier TDB' % hostname)
				
			return resultat
		if mode=='regex':
			resultat=[]
			regex__=hostname
			for host__ in self.allDataByHosts:
				if re.search(regex__,host__, re.IGNORECASE):
					resultat.append(self.allDataByHosts[host__])
					
			return resultat

	def getInfoModel(self,model):
		

		resultat=[]
		regex__=model
		for host__ in self.allDataByHosts:
			if re.search(regex__,self.allDataByHosts[host__]['Modèle'], re.IGNORECASE):
				resultat.append(self.allDataByHosts[host__])
				
		return resultat
		
	def getInfoSN(self,SN):
		resultat={}
		try:
			print(f'SN:{SN}')					
			resultat=self.allDataBySN[SN]
			#pprint.pprint(resultat)
		except KeyError as e:
			print('SN %s inconnue dans le fichier TDB' % SN)
			
		return resultat

		
	def getInfoIP(self,IPStr):
		resultat={}
		IP=ParseIP(IPStr,mode="normal")
		try:
			resultat['ipMain']=self.allDataByIPMain[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
		try:
			resultat['ipRemoteConsole']=self.allDataByIPRemote[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
		try:
			resultat['IP']=self.allDataByIP[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
			
		return resultat
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		base=None
		
		with open(filename,'rb') as file__:
			base=pickle.load(file__)
		
		try:
			self.allDataByHosts=base.allDataByHosts
			self.allDataBySN=base.allDataBySN
			self.allDataByIPMain=base.allDataByIPMain
		except KeyError as E:
			print('ERROR')
			raise E
			
def setwidth(f):
	def wrapper_setwidth(*args,**kwargs):
		liste_cur=args[1]
		xls=args[0]
		namefile=args[3]
		indice=0
		for element in liste_cur:
			if len(element)>(xls.maxcolumn[indice]):
				xls.maxcolumn[indice]=len(element)
				xls.worksheets[namefile].set_column(indice, indice, xls.maxcolumn[indice]+2)
			indice+=1
		f(*args,**kwargs)
	return wrapper_setwidth
			
class xlsTDBMatrix(object):
	def __init__(self,filename,intTDBObjCnr__):
		self.filename=filename
		self.intTDBObjCnr=intTDBObjCnr__
		self.workbook  = xlsxwriter.Workbook(filename)
		self.worksheets={}
		self.indices={}
		for name_file in intTDBObjCnr__.keys():
			self.worksheets[name_file] = self.workbook.add_worksheet(name_file)
			self.indices[name_file]=0
		self.header=['Réf Câble','MA','Nom','SN','Model','DC','Salle','Baie','Position','Port','Type']
		self.initMaxColumn()
		self.initStyle()
		self.initHeader()
		self.writeInterco()
		
		self.workbook.close()
		
	def initHeader(self):
	
		for name_file in self.worksheets.keys():
			self.worksheets[name_file].merge_range('A1:K1', "Source", self.header_format)
			self.worksheets[name_file].merge_range('L1:V1', "Destination", self.header_format)
			self.indices[name_file]+=1
			self.writeList(self.header*2,self.header_format_2,name_file)

	def initMaxColumn(self):
		self.maxcolumn=[]
		for element in self.header*2:
			self.maxcolumn.append(len(element))
	
	@setwidth	
	def writeList(self,liste,style,namefile,offset=0):
		current_offset=offset
		for element in liste:
			self.worksheets[namefile].write(self.indices[namefile],current_offset,element,style)
			current_offset+=1
		self.indices[namefile]+=1
		
	def initStyle(self):
		self.header_format=self.workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#A9A9A9'})
			
		self.header_format_2=self.workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#DCDCDC'})
			
		self.default_format=self.workbook.add_format({
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#B0E0E6'})
	
	def writeInterco(self):
		for name_file in self.intTDBObjCnr.keys():
			for interco__ in self.intTDBObjCnr[name_file].intercos:
				self.writeList(interco__.toListComplete(),self.default_format,name_file)

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-e", "--equipement",  action="store",help="hostname de l'équipement TDB",required=False)
	group1.add_argument("--file-host", dest='filehost', action="store",help="hostname de l'équipement TDB",required=False)
	parser.add_argument("--filter-field", dest='filterfield', action="store",help="Filtre les champs: CHAMP1:CHAMP2:...",required=False)
	group1.add_argument("--sn",  action="store",help="Serial Number de l'équipement TDB",required=False)
	group1.add_argument("--file-sn", dest='filesn', action="store",help="Fichier contenant les Serial Number de l'équipement TDB",required=False)
	group1.add_argument("--mac",  action="store",help="mac de l'équipement TDB",required=False)
	group1.add_argument("--model",  action="store",help="filtre sur le model",required=False)
	group1.add_argument("--ip-address", action="store",dest='IPaddress',help="IP de l'équipement TDB",required=False)
	parser.add_argument("--excel",  action="store",help="fichier excel contenant les informations TDB",required=False)
	parser.add_argument("-d", "--dump_dir",  action="store",default=PATH_TDB_DUMP,help="Répertoire contenant les dump",required=False)
	parser.add_argument("--regex",  action="store_true",default=PATH_TDB_DUMP,help="Search Equipment with regex",required=False)
	parser.add_argument("-s", "--save",  action="store",help="fichier de sauvegarde dump",required=False)
	parser.add_argument("-x", "--xls",  action="store",help="Matrice Excel",required=False)
	group1.add_argument("-m", "--matrice", nargs='*', action="store",help="matrice de câblage simplifié en csv",required=False)
	args = parser.parse_args()
	
	mode="normal"
	if args.regex:
		mode="regex"
		
	
	if args.equipement:
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoEquipment(args.equipement.upper(),mode=mode))
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseTDB.getInfoEquipment(args.equipement.upper(),mode=mode))
			else:
				print("Ajouter un dump")
	elif args.filehost:
		allHosts=splitFileByLine(args.filehost)
		resultat={}
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			for host__ in allHosts:
				resultat[host__.upper()]=BaseTDB.getInfoEquipment(host__.upper(),mode=mode)
			if args.save:
				BaseTDB.save(args.save)
			
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				for host__ in allHosts:
					resultat[host__.upper()]=BaseTDB.getInfoEquipment(host__.upper(),mode=mode)
			if args.save:
				BaseTDB.save(args.save)
			else:
				print("Ajouter un dump")
		
		if args.filterfield:
			fields=args.filterfield.split(':')
			resultat_filtered={}
			#pdb.set_trace()
			for hostname in resultat:
				resultat_filtered[hostname]=[]
				for element in resultat[hostname]:
					resultat_filtered[hostname].append({ key:value for key , value in element.items() if key in fields })
			resultat=resultat_filtered
		for equipment in resultat:
			print(equipment)
			ppr(resultat[equipment],width=100)

	elif args.sn:
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoSN(args.sn))
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseTDB.getInfoSN(args.sn))
			else:
				print("Ajouter un dump")
				
	elif args.filesn:
		allSn=splitFileByLine(args.filesn)
		resultat={}
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoSN(args.sn))
			for sn__ in allSn:
				resultat[sn__.upper()]=BaseTDB.getInfoSN(sn__)
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseTDB.getInfoSN(args.sn))
				for sn__ in allSn:
					resultat[sn__.upper()]=BaseTDB.getInfoSN(sn__)
			if args.save:
				BaseTDB.save(args.save)
                
		for SN in resultat:
			print(SN)
			ppr(resultat[SN],width=100)

		for SN in resultat:
			nameCur=resultat[SN]["Nom de l'équipement"]
			print(f'{SN}:{nameCur}')

				
	elif args.mac:
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoMac(args.mac))
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseTDB.getInfoMac(args.mac))
			else:
				print("Ajouter un dump")
	elif args.IPaddress:
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoIP(args.IPaddress))
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pdb.set_trace()
				pprint.pprint(BaseTDB.getInfoIP(args.IPaddress))
			else:
				print("Ajouter un dump")
	elif args.model:
		if args.excel:
			BaseTDB=tdbContainer(excel_file=args.excel)
			pprint.pprint(BaseTDB.getInfoModel(args.model))
			if args.save:
				BaseTDB.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseTDB=tdbContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseTDB.getInfoModel(args.model))
			else:
				print("Ajouter un dump")					
	elif args.matrice:
		Matrix={}
		for matrice_element in args.matrice:
			name__=getbasefilename(matrice_element)
			Matrix[name__]=intercoTDBContainer(matrice_element)
			print(name__+":")
			Matrix[name__].printer()
		
		if args.xls:
			xlsTDBMatrix(args.xls,Matrix)
		