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



def getnewIP(old_ip,new_net):
	
	old_ipObj=IPNetwork(old_ip)
	
	if old_ipObj.prefixlen==32:
		return new_net
	
	new_net_obj=IPNetwork(new_net)	
	
	offset=old_ipObj.value-old_ipObj.network.value
	new_ip_obj=IPNetwork('0.0.0.0/'+str(old_ipObj.prefixlen))
	new_ip_obj.value=new_net_obj.value+offset
	
	return str(new_ip_obj)

def replaceIP( strInput,increment):
	
	def replace_ip(t):
		return str(IPAddress(t[0])+int(increment))
			

	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=(pp.Combine(octet + ('.'+octet)*3))
	ipAddress.setParseAction(replace_ip)

	new_line=ipAddress.transformString(strInput)
		

	return new_line
			
if __name__ == '__main__':
	"Useful to Migrate IP Network"
	
	parser = argparse.ArgumentParser()
	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file_src')
		parser.add_argument('increment',type=int)
		mode="FILE"


	else:
		parser.add_argument('increment',type=int)
		mode="STDIN"
		
	args = parser.parse_args()
		
	if mode=="FILE":
		with open(args.file_src,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		all_lines=sys.stdin.read()
	

	output=replaceIP(all_lines,args.increment)
	print(output)