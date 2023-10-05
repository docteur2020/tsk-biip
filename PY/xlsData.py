#!/usr/bin/env python3.8
# coding: utf-8


import pdb
import argparse
import pickle
import xlrd
from pprint import pprint as ppr
from pprint import pformat as pprs
from unidecode import unidecode

def normalizeKey(String):
	toreplace={' ':'_','(':'_',')':'_'}
	resultatTmp=unidecode(String)
	strList=[]
	for c in resultatTmp:
		if c in toreplace:
			strList.append(toreplace[c]) 
		elif c.isalnum():
			strList.append(c)
	resultat=''.join( c for c in strList)
	return resultat

class xlsContainer(object):
	"TDB Container"
	
	def __init__(self,excel_file):

		self.headers={}
		try:
			xl_workbook = xlrd.open_workbook(excel_file,encoding_override='cp1252')
		except AssertionError as E:
			pdb.set_trace()
			print(E)
			
		sheet_names = xl_workbook.sheet_names()
		xl_sheets={}
		self.datas={}
		for sheet_name in sheet_names:
			xl_sheets[sheet_name] = xl_workbook.sheet_by_name(sheet_name)
			self.datas[sheet_name]=[]
			self.headers[sheet_name]=xl_sheets[sheet_name].row_values(0)
			for rownum in range(1,xl_sheets[sheet_name].nrows):
				self.datas[sheet_name].append({key:str(xl_sheets[sheet_name].row_values(rownum)[id__]) for id__,key in list(enumerate(self.headers[sheet_name])) })
			
	#def initObj(self,sheet_name):
	#		for key,item in self.datas[sheet_name]:
	#			super().__setattr__(normalizeKey(key),item)
	#
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		with open(filename,'rb') as file__:
			self=pickle.load(file__)
			
	def __str__(self):
		return pprs(self.datas)
		
	def __repr__(self):
		return pprs(self.datas)
			
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--excel",  action="store",help="fichier excel contenant les informations",required=True)
	parser.add_argument("-s", "--save",  action="store",help="fichier de sauvegarde dump",required=False)
	parser.add_argument("-d", "--dump",  action="store",help="load dump",required=False)
	args = parser.parse_args()
	
	objFromXls=xlsContainer(args.excel)
	
	print(objFromXls)
	
	#objFromXls.initObj('Sheet1')
	#
	#print(dir(objFromXls))
		