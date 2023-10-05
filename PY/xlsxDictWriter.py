#!/usr/bin/env python3.7
# coding: utf-8

import csv
import pdb
import argparse
import os
import pprint
import glob
from pathlib import Path
from tabulate import tabulate
from collections import OrderedDict
import xlsxwriter

def setwidth(f):
	def wrapper_setwidth(*args,**kwargs):
		liste_cur=args[1]
		xls=args[0]
		namefile=args[3]
		indice=0
		for element in liste_cur:
			if len(element)>(xls.maxcolumn[namefile][indice]):
				xls.maxcolumn[namefile][indice]=len(element)
			xls.worksheets[namefile].set_column(indice, indice, xls.maxcolumn[namefile][indice]+4)
			indice+=1
		f(*args,**kwargs)
	return wrapper_setwidth
	
class xlsMatrix(object):
	def __init__(self,filename,InfoDict):
		self.filename=filename
		self.info=InfoDict
		self.workbook  = xlsxwriter.Workbook(filename)
		self.worksheets={}
		self.indices={}
		for key__ in InfoDict.keys():
			self.worksheets[key__] = self.workbook.add_worksheet(key__)
			self.indices[key__]=0

		self.initStyle()
		self.initMaxColumn()
		self.writeAll()
		self.workbook.close()
		
	
	def initMaxColumn(self):
		self.maxcolumn={}
		for wk in self.info:
			self.maxcolumn[wk]=[]
			for element in self.info[wk][0]:
				self.maxcolumn[wk].append(len(element))
	
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
	
	def writeAll(self):
	
		header=True
		for wk in self.info.keys():
			header=True
			for ligne in self.info[wk]:
				if header:
					self.writeList(ligne,self.header_format_2,wk)
					header=False
				else:
					self.writeList(ligne,self.default_format,wk)
					

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-x", "--xls",  action="store",help="Matrice Excel",required=True)
	args = parser.parse_args()
	
	dict_cur={'test1':[['toto','titi','tutu'],['rien','quedalle','nothing'],['coucou','bonjour','hi'],['bob','bill','bouel'],['pierre','paul','jack']],'test2':[['paul','pierre','bilou'],['jack','jacko','jack ouille'],['noir','beau','black'],['rouge','red','carmin'],['bleu','vert','jaune']],'test3':[['vrai','encore','encore'],['faux','wrong','archi faux'],['pas faux','something','more'],['pas vrai','presque vrai','ah bon'],['pas sure','oui','non']]}
	
	if args.xls:
		xlsMatrix(args.xls,dict_cur)
