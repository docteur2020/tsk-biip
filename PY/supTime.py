#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals


import re
import argparse
import pdb
import io
import os
import sys
import pyparsing as pp
import glob



def supTimeLog( strInput ):

	Output=io.StringIO()

	noTimestamp="==suppressed=="

			
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	duree=(jma*2)|(jma*3)
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	time=duree|heure

	time.setParseAction(lambda y: noTimestamp)

	for line in strInput.split('\n'):
		new_line=time.transformString(line)
		
		Output.write(new_line+'\n')
		
	outputStr=Output.getvalue()
	Output.close()

	return outputStr
			
if __name__ == '__main__':
	"Useful to sup time in log"
	
	parser = argparse.ArgumentParser()

	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file_or_dir',help='file or directory')
		
		mode="FILE"

	else:
		mode="STDIN"
		
	args = parser.parse_args()
		
	if mode=="FILE":
		
		if os.path.isfile(args.file_or_dir):
			with open(args.file_or_dir,'r') as file:
				all_lines=file.read()		   
		elif os.path.isdir(args.file_or_dir):
			mode="DIR"
			all_files=glob.glob(args.file_or_dir+'/*.log')
			all_files.extend(glob.glob(args.file_or_dir+'/*.txt'))
			dir_result=args.file_or_dir+'/NOTIME'
			
			if not os.path.exists(dir_result):
				print(f"directory added:{dir_result}")
				os.makedirs(dir_result)
			else:
				print(f"directory already exists:{dir_result}")
				
			for file in all_files:
				with open(file,'r') as file_r:
					all_lines=file_r.read()
				dirname, fname = os.path.split(file)
				new_file=dirname+'/NOTIME/'+fname
				print(f'Generating new file:{new_file}')
				output=supTimeLog(all_lines)
				with open(new_file,'w+') as file_w:
					file_w.write(output)
			
		else:
			print('verify path file or directory')
			


	elif mode=="STDIN":
		all_lines=sys.stdin.read()
	

	if mode !="DIR":	
		output=supTimeLog(all_lines)
		print(output)