#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals

import sys
import os
import re
import pdb
import io
import argparse


class config_cisco(object):
	"Configuration Cisco"
	def __init__(self,fichier,data=""):
		self.fichier_config=fichier
		self.equipements_cfg=[]
		self.dict_equipements_cfg={}
		self.mode=None
		self.exp_reg_bloc=None
		self.data=data
		if fichier != None:
			with open(fichier,'r') as file:
				all_lines=file.read()
			self.exp_reg_bloc=re.compile('(^!$|^\w)',re.MULTILINE)
			self.exp_reg_exclam=re.compile('^!$',re.MULTILINE)
			reg_end=re.compile('^end\r\n|^end\s*\n|\r\n\r\n\r\n\r\S.*#',re.MULTILINE)
			self.mode="FILE"
		elif not data:
			all_lines=sys.stdin.read() 
			self.exp_reg_bloc=re.compile('(^!\r\n|^\w)',re.MULTILINE)
			self.exp_reg_exclam=re.compile('^!\r\n',re.MULTILINE)
			reg_end=re.compile('^end\r\n|^end\s*\n|\r\n\r\n\r\n\r\S.*#',re.MULTILINE)
			self.mode="STDIN"
		elif data:
			all_lines=data
			self.exp_reg_bloc=re.compile('(^!\r\n|^\w)',re.MULTILINE)
			self.exp_reg_exclam=re.compile('^!\r\n',re.MULTILINE)
			reg_end=re.compile('^end\r\n|^end\s*\n|\r\n\r\n\r\n\r\S.*#',re.MULTILINE)
			self.mode="STDIN"	
		self.equipements_cfg=reg_end.split(all_lines)
		
		indice=2		
		for equipement_cfg in self.equipements_cfg:
			hostame_cur=self.get_name(equipement_cfg)
			#print('START===========')
			#print(hostame_cur)
			if hostame_cur in self.dict_equipements_cfg.keys():
				hostame_cur=hostame_cur+"_"+str(indice)
				indice=indice+1
			self.dict_equipements_cfg[hostame_cur]=equipement_cfg
			#print(equipement_cfg)
			#print('END===========')
			
		if 'INCONNU' in self.dict_equipements_cfg:
			del self.dict_equipements_cfg['INCONNU']
			
	def explode_blocs(self,config_str):
	
		resulat=[]
		blocs_cur=""
		resultat=self.exp_reg_bloc.split(config_str)			
		
		return resultat
		
	def explode_blocs2(self,config_str):
	
		resultat=[]
		bloc_cur=""
		line_prec=""

		exp_reg_espace=re.compile('^\s',re.MULTILINE)
		for line in config_str.splitlines():
			if exp_reg_espace.match(line):
				bloc_cur=bloc_cur+"\n"+line
			elif self.exp_reg_exclam.match(line):
				resultat.append(bloc_cur+"\n"+line+"\n")
				bloc_cur=""
				
			elif not exp_reg_espace.match(line):
				resultat.append(bloc_cur)
				bloc_cur=line
				
			line_prec=line
			

		return resultat
		
	def explode_blocs_critere(self,config_str,reg_critere):
	
		resultat=[]
		bloc_cur=""
		line_prec=""

		exp_reg_espace=re.compile('^\s',re.MULTILINE)
		for line in config_str.splitlines():
			if reg_critere.match(line):
				resultat.append(bloc_cur)
				bloc_cur=line+"\n"
			else:
				bloc_cur=bloc_cur+line+"\n"
		resultat.append(bloc_cur)
		
		return resultat
		
	def match(self,reg):
		exp_reg=re.compile(str(reg),re.MULTILINE)
		exp_reg_router=re.compile('router ')
		exp_reg_paragraphe_router=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ !|^ address-family ipv4 vrf',re.MULTILINE)
		exp_reg_paragraphe_router_generique=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ address-family ipv4 vrf',re.MULTILINE)
		# print(exp_reg)
		indice=0
		for hostname_cur in self.dict_equipements_cfg.keys():
			print("---------------------------------")
			print("Equipement:"+hostname_cur)
			print("---------------------------------")
			for bloc in self.explode_blocs2(self.dict_equipements_cfg[hostname_cur]):
				#print(bloc)
				#print("INDICE:"+indice.__str__())
				indice=indice+1
				# if indice==791:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
				# if indice==792:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
					#pdb.set_trace()
					
				if exp_reg.search(bloc):
					# print("COUCOU MATCH")
					# print(bloc)
					# print(exp_reg.search(bloc))
					indice_bloc=0
					if exp_reg_router.search(bloc):
						print("!")
						for bloc_router in self.explode_blocs_critere(bloc,exp_reg_paragraphe_router):
							indice_bloc=indice_bloc+1
							# print(bloc_router)
							# print(exp_reg.search(bloc_router))
							# print("INDICE_BGP:"+indice_bloc.__str__())
							if exp_reg_router.search(bloc_router):
								bloc_router_first=bloc_router
								print(bloc_router_first)
							elif exp_reg.search(bloc_router):
								print(bloc_router)
							elif not exp_reg_paragraphe_router_generique.search(bloc_router) and not bloc_router == " !\n" :
								print(bloc_router)

					else:
						print(bloc)
						#print("INDICE:"+indice.__str__())
					
			print("\nEND:"+hostname_cur+'\n')

	def extract(self,reg):
		result=io.StringIO()
		exp_reg=re.compile(str(reg),re.MULTILINE)
		exp_reg_router=re.compile('router ')
		exp_reg_paragraphe_router=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ !|^ address-family ipv4 vrf',re.MULTILINE)
		exp_reg_paragraphe_router_generique=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ address-family ipv4 vrf',re.MULTILINE)
		# print(exp_reg)
		indice=0
		for hostname_cur in self.dict_equipements_cfg.keys():
			#print("---------------------------------")
			#print("Equipement:"+hostname_cur)
			#print("---------------------------------")
			for bloc in self.explode_blocs2(self.dict_equipements_cfg[hostname_cur]):
				#print(bloc)
				#print("INDICE:"+indice.__str__())
				indice=indice+1
				# if indice==791:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
				# if indice==792:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
					#pdb.set_trace()
					
				if exp_reg.search(bloc):
					# print("COUCOU MATCH")
					# print(bloc)
					# print(exp_reg.search(bloc))
					indice_bloc=0
					if exp_reg_router.search(bloc):
						#print("!")
						for bloc_router in self.explode_blocs_critere(bloc,exp_reg_paragraphe_router):
							indice_bloc=indice_bloc+1
							# print(bloc_router)
							# print(exp_reg.search(bloc_router))
							# print("INDICE_BGP:"+indice_bloc.__str__())
							if exp_reg_router.search(bloc_router):
								bloc_router_first=bloc_router
								result.write(bloc_router_first+'\n')
							elif exp_reg.search(bloc_router):
								result.write(bloc_router+'\n')
							elif not exp_reg_paragraphe_router_generique.search(bloc_router) and not bloc_router == " !\n" :
								result.write(bloc_router+'\n')

					else:
						result.write(bloc+'\n')
						#print("INDICE:"+indice.__str__())
					
			#print("\nEND:"+hostname_cur+'\n')	

		extractedStr=result.getvalue()
		
		return extractedStr

	def extract2(self,reg):
		result=io.StringIO()
		exp_reg=re.compile(str(reg),re.MULTILINE)
		exp_reg_router=re.compile('router ')
		exp_reg_paragraphe_router=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ !|^ address-family ipv4 vrf',re.MULTILINE)
		exp_reg_paragraphe_router_generique=re.compile('^ vrf|^ neighbor-group|^ template peer-policy|^ template peer-session|^ address-family ipv4 vrf',re.MULTILINE)
		# print(exp_reg)
		indice=0
		for hostname_cur in self.dict_equipements_cfg.keys():
			#print("---------------------------------")
			#print("Equipement:"+hostname_cur)
			#print("---------------------------------")
			for bloc in self.explode_blocs2(self.dict_equipements_cfg[hostname_cur]):
				#print(bloc)
				#print("INDICE:"+indice.__str__())
				indice=indice+1
				# if indice==791:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
				# if indice==792:
					# print ("################")
					# print(bloc)
					# print ("################")
					# print(exp_reg_router.search(bloc))
					# print ("################")
					#pdb.set_trace()
					
				if exp_reg.search(bloc):
					# print("COUCOU MATCH")
					# print(bloc)
					# print(exp_reg.search(bloc))
					indice_bloc=0
					if exp_reg_router.search(bloc):
						#print("!")
						for bloc_router in self.explode_blocs_critere(bloc,exp_reg_paragraphe_router):
							indice_bloc=indice_bloc+1
							# print(bloc_router)
							# print(exp_reg.search(bloc_router))
							# print("INDICE_BGP:"+indice_bloc.__str__())
							if exp_reg_router.search(bloc_router):
								bloc_router_first=bloc_router
								result.write(bloc_router_first+'\n')
							elif exp_reg.search(bloc_router):
								result.write(bloc_router+'\n')
							elif not exp_reg_paragraphe_router_generique.search(bloc_router) and not bloc_router == " !\n" :
								result.write(bloc_router+'\n')

					else:
						result.write(bloc+'\n')
						#print("INDICE:"+indice.__str__())
					
			#print("\nEND:"+hostname_cur+'\n')	

		extractedStr=result.getvalue()
		
		return extractedStr
		
	def get_name(self,config_string):
		resultat="INCONNU"
		if self.mode=="FILE":
			for line in config_string.split('\n'):
				if re.search('^hostname|^switchname',line):
					resultat=line.split()[1]
		elif self.mode=="STDIN":
			for line in config_string.split('\n'):
				if re.search('^hostname|^switchname',line):
					resultat=line.split()[1]
		return resultat
		


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	
	if os.isatty(0):
		mode="FILE"
		
		parser.add_argument('match')
		parser.add_argument('file')
		
		
		args = parser.parse_args()
		
		parametre_file=args.file
		parametre_reg=args.match
	else:
		mode="STDIN"
		parser.add_argument('match')
		
		args = parser.parse_args()
		
		parametre_file=None
		parametre_reg=args.match
		
	#print(parametre_reg)
	config_obj=config_cisco(parametre_file)
	config_obj.match(parametre_reg)
