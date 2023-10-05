#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals


import re
import xlrd
import argparse
import pdb
import io
import os
import sys

def initListTupleFromCsv(excel_file):
	resultat=[]
	contenu_dict={}
	wb=xlrd.open_workbook(excel_file)
	lignes=[]
	sh = wb.sheet_by_name(u'Feuil1')
	for rownum in range(0,sh.nrows):
		lignes.append(sh.row_values(rownum))
		

	for ligne in lignes[1:]:
		dict_cur={}
		column_id=0
		for value in ligne:
			#column_id=ligne.index(value)
			header=lignes[0][column_id]
			if isinstance(value,float):
				dict_cur[header]=str(int(value))
			else:
				dict_cur[header]=value
			column_id+=1
		resultat.append(dict_cur)
	
	resulat_list_tup=[]
	
	
	for dict__ in resultat:
		list_cur=[]
		for key__ in dict__.keys():
			list_cur.append(("<"+key__+">",dict__[key__]))
		resulat_list_tup.append(list_cur)
			
	return resulat_list_tup
	
		

class configTemplate(object):
	"Classe template de configuration"
	def __init__(self,str):
		self.template=str
		
	def replace(self,liste_parametre):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=self.template
		for (param,valeur) in liste_parametre:
			#print("PARAM:{0} VALEUR:{1}".format(param,valeur))
			try:
				resultat=resultat.replace(param,valeur)
				
			except:
				#pass
				pdb.set_trace()
			
		return resultat
		
	
class SedFile(object):
	"Classe template de configuration"
	def __init__(self,file):
		self.file_str=file
		self.liste_str1_str2=[]
		
		with open(self.file_str,'r') as file_str_:
			self.liste_str1_str2=file_str_.read().splitlines()
			
		
	def replace(self,long_str):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=long_str
		for str1_str2 in self.liste_str1_str2:
			tab_str=str1_str2.split(';')
			if len(tab_str) >= 2:
				str1=tab_str[0].strip()
				str2=tab_str[1].strip()
				try:
					resultat=resultat.replace(str1,str2)
				except:
					pdb.set_trace()
		
		return resultat

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-x", "--xls",action="store_true",help="mode fichier Excel",required=False)

	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file_str1_str2_or_xls')
		parser.add_argument('file_src')
		mode="FILE"


	else:
		parser.add_argument('file_str1_str2_or_xls')
		mode="STDIN"
		
	args = parser.parse_args()
	
	print(mode)
	
	if mode=="FILE":
		with open(args.file_src,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		param_file=None
		all_lines=sys.stdin.read()
		
	if args.xls:
		resultat=io.StringIO()
		param_array=initListTupleFromCsv(args.file_str1_str2_or_xls)
		#print(param_array)
		for param__ in param_array:
			resultat.write(configTemplate(all_lines).replace(param__))
		print(resultat.getvalue())
		resultat.close
	
	else:
		sed_obj=SedFile(args.file_str1_str2_or_xls)
		print(sed_obj.replace(all_lines))