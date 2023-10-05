#!/bin/python3.8


import sys
import argparse
import pyparsing as pp
import pdb
import glob
import re
from time import gmtime, strftime , localtime
import os
from pprint import pprint as ppr
import difflib


DIR_DIFF_RESULT="/home/d83071/diff"

def getFileLst(path__):
	all_files=glob.glob(path__+'/*.[Ll][Oo][Gg]')
	all_files.extend(glob.glob(path__+'/*.[Tt][Xx][Tt]'))
	
	all_files_short=list(map(lambda y:  os.path.split(y)[1],all_files))
	
	return all_files_short
	
def getHostnameFromPathFile(file):
	dirname, fname = os.path.split(file)
	hostname=fname.split('_')[0]
	return hostname

def searchHostnameLst(hostname,files):
	for file in files:
		if hostname in file:
			return file
			
	
	
	
	
def initCouple(path1,path2):

	CoupleFiles=[]
	files1=getFileLst(path1)
	files2=getFileLst(path2)
	
	for file1 in files1:	
		
		if file1 in files2:
			CoupleFiles.append((path1+'/'+file1,path2+'/'+file1))
			continue
		hostnameCur=getHostnameFromPathFile(file1)
		fileOther=searchHostnameLst(hostnameCur,files2)
		if fileOther:
			CoupleFiles.append((path1+'/'+file1,path2+'/'+fileOther))
		else:
			print(f'{path1}/{file1} not find in {path2}')
			
	return CoupleFiles
	
def addDirectory(path__):
	if not os.path.exists(path__):
		print(f"directory added:{path__}")
		os.makedirs(path__)
	else:
		print(f"directory already exists:{path__}")

def FileAsStr(file):
	
	Str__=""
	
	with open(file) as file_r:
		Str__=file_r.read()
	
	return Str__
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("directory1", help="Directory to compare (1) ")
	parser.add_argument("directory2", help="Directory to compare (2) ")
	parser.add_argument("-t", "--tag",  action="store",help="tag to save result")

	args = parser.parse_args()
	
	filesToCompare=initCouple(args.directory1,args.directory2)
	
	if args.tag:
		suffixeHtml=strftime("_diff_%Y%m%d_%Hh%Mm%Ss.html", localtime())
		NewDir=DIR_DIFF_RESULT+'/'+args.tag
		addDirectory(NewDir)
				
		for file1,file2 in filesToCompare:
			Str1=open(file1)
			Str2=open(file2)
			basename=os.path.basename(file1)
			basename_w_ext=os.path.splitext(basename)[0]
			FullFileresult=NewDir+'/'+basename_w_ext+suffixeHtml

			print(f'Comparison between {file1} and {file2}')
			diffResultStr=difflib.HtmlDiff().make_file(Str1,Str2)

			with open(FullFileresult,'w+') as file_html_w:
				file_html_w.write(diffResultStr)
		
	

			
