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
import xlrd
import pyparsing as pp
from netaddr import IPAddress , IPNetwork

def initNetMatching(file,xlsxMode=False):

	netMatch={}	
	if xlsxMode:
		xls_file=file
		wb=xlrd.open_workbook(xls_file)
		lignes=[]
		sheetNames=wb.sheet_names()
		sh = wb.sheet_by_name(sheetNames[0])
		for rownum in range(0,sh.nrows):
			entry=sh.row_values(rownum)
			netMatch[entry[0]]=entry[1]
		
	else:
		with open(file,'r') as file_str:
			netsMatchingLine=file_str.read().splitlines()
			for line in netsMatchingLine:
				listList=line.split()
				netOld=listList[0]
				netNew=listList[1]
				netMatch[netOld]=netNew
				
	return netMatch

def getnewIP(old_ip,new_net):
	
	old_ipObj=IPNetwork(old_ip)
	
	if old_ipObj.prefixlen==32:
		return new_net
	
	new_net_obj=IPNetwork(new_net)	
	
	offset=old_ipObj.value-old_ipObj.network.value
	new_ip_obj=IPNetwork('0.0.0.0/'+str(old_ipObj.prefixlen))
	new_ip_obj.value=new_net_obj.value+offset
	
	return str(new_ip_obj)

def replaceNet( strInput,netsMatching):
	Output=io.StringIO()
	def replace_ip(t):
	
		for netOld,netNew in netsMatching.items():
			netOldCurObj=IPNetwork(netOld)
			netNewCur=netNew
			maskOldCur=netOldCurObj.netmask.__str__()
			ip_cur_obj=IPAddress(t[0])
			if ip_cur_obj in netOldCurObj:
				new_ip__=getnewIP(t[0]+'/'+maskOldCur,netNewCur)
				new_ip=new_ip__.split('/')[0]
				return new_ip
		else:
			return t
			

	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=(pp.Combine(octet + ('.'+octet)*3))
	ipAddress.setParseAction(replace_ip)

	for line in strInput.split('\n'):
		if re.search('ip route',line,re.IGNORECASE):
			pass
		else:
			new_line=ipAddress.transformString(line)
		
		Output.write(new_line+'\n')
		
	outputStr=Output.getvalue()
	Output.close()

	return outputStr
			
if __name__ == '__main__':
	"Useful to Migrate IP Network"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-x", "--xlsx",action="store_true",help="mode fichier Excel",required=False)

	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file_str1_str2_or_xls')
		parser.add_argument('file_src')
		mode="FILE"


	else:
		parser.add_argument('file_str1_str2_or_xls')
		mode="STDIN"
		
	args = parser.parse_args()
		
	if mode=="FILE":
		with open(args.file_src,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		all_lines=sys.stdin.read()
	

	netsMatching=initNetMatching(args.file_str1_str2_or_xls,args.xlsx)

			
	output=replaceNet(all_lines,netsMatching)
	print(output)