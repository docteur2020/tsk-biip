#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import pdb
import argparse
import yaml
import hashlib
import os
from pprint import pprint as ppr
import base64
import glob

DEFAULT_RESULT='result'

def splitInStr(Str,length):
	try:
		chunks, chunk_size = len(Str), int(len(Str)/length)
	except TypeError as E:
		pdb.set_trace()
		print(E)
	return [Str[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]

def reverseListStr(ListStr):
	return [Str[::-1] for Str in ListStr]

def get_md5(filename):
	with open(filename,'rb') as file_rb:
		return hashlib.md5(file_rb.read()).hexdigest()


class MFile(object):
	def __init__(self,filename,number=1000):
		self.fullpath_filename=filename
		self.name=os.path.basename(filename)
		self.path=os.path.dirname(filename)
		self.number=number
		self.hash=get_md5(self.fullpath_filename)
		self.encodeSpecTxt()
	
	def __str__(self):
		return self.__dict__
	
	def encodeSpecTxt(self):
		with open(self.fullpath_filename, "rb") as file_rb:
			encodedFile = base64.b64encode(file_rb.read())
			str_encodedFile=encodedFile.decode()
			self.encodedStrsReversed=reverseListStr(splitInStr(str_encodedFile,self.number))
			
	def save(self,fileYaml):
		with open(fileYaml, 'w') as file_w:
			yaml.dump(self.__dict__, file_w)
	   
	@staticmethod
	def generate(fileYaml,resultDir):
		with open(fileYaml,'r') as file_r:
			data = yaml.load(file_r, Loader=yaml.FullLoader)
			str_encodedStr="".join(reverseListStr(data['encodedStrsReversed']))
			fileData=base64.b64decode(str_encodedStr)
			resultFilename=resultDir+'/'+data['name']
			with open(resultFilename,'wb') as file_wb:
				file_wb.write(fileData)
				
				
			newMD5SUM=get_md5(resultFilename)
			oldMD5SUM=data['hash']
			print(f'Original MD5SUM:{oldMD5SUM}')
			print(f'	 New MD5SUM:{newMD5SUM}')
			

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-f", "--file",action="store",help="File")
	group.add_argument("-d", "--dump",action="store",help="Yaml dump that contained the file data")
	group.add_argument("--dir-files", dest="dirFiles",action="store",help="directory containing file")
	group.add_argument("--dir-dump", dest="dirDumps",action="store",help="directory containing dumps")
	parser.add_argument("-n", "--number",action="store",default=1000,type=int,help="number of split file",required=False)
	parser.add_argument("-s", "--save",action="store",help="save to yaml",required=False)
	parser.add_argument("-r", "--result",action="store",help="directory to save result file",default=DEFAULT_RESULT)
	args = parser.parse_args()
	
	if args.file:
		mFileObj=MFile(args.file,args.number)
		ppr(mFileObj.__str__())
		if args.save:
			mFileObj.save(args.save)
			
	if args.dump:
		MFile.generate(args.dump,args.result)
		
	if args.dirFiles:
		mFileObj={}
		files=glob.glob(args.dirFiles+'/*')
		for id__,file__ in enumerate(files):
			print(file__)
			print(id__)
			if args.save:
				mFileObj[id__]=MFile(file__,args.number)
				mFileObj[id__].save(args.save+str(id__)+'.yml')
			
	if args.dirDumps:
		dumps=glob.glob(args.dirDumps+'/*')
		for id__,dump__ in enumerate(dumps):
			print(dump__)
			print(id__)
			if args.result:
				MFile.generate(dump__,args.result)