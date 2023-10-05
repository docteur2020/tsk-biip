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
from time import  strftime , localtime
import yaml
from pprint import pprint as ppr

sys.path.insert(0,'/home/d83071/py')

PATH_YAML="/home/d83071/yaml/ROUTE/"
PATH_YAML_RESULT="/home/d83071/yaml/ROUTE/MULTIPATHBGP/"
from ParsingShow import ParseIpRouteNexusSpec

def loadYaml(file):
	with open(file, 'r') as yml__:
		yaml_obj = yaml.load(yml__,Loader=yaml.SafeLoader)

	return yaml_obj
	
def getHostnameFromPathFile(file):
	dirname, fname = os.path.split(file)
	hostname=fname.split('_')[0].split('.')[0].upper()
	
	return hostname
	
def saveResult(result,saveName,path=PATH_YAML):
	suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
	filename=path+'/'+saveName+suffix
	with open(filename,'w') as yml_w:
		 yaml.dump(result,yml_w ,default_flow_style=False)
		 
def countRT(RTCur):
	RTCount={}
	
	for hostname in RTCur:
		RTCount[hostname]={}
		for vrf in RTCur[hostname]:
			nb_route=len(RTCur[hostname][vrf])
			RTCount[hostname][vrf]=nb_route
		
	ppr(RTCount)
	
	return RTCount

def extractNH_RT(RTCur):
	RT_NH={}
	
	for hostname in RTCur:
		RT_NH[hostname]={}
		for vrf in RTCur[hostname]:
			RT_NH[hostname][vrf]={}
			for prefix in RTCur[hostname][vrf]:
				NHs=[ nh[0] for nh in  prefix[2] ]
				for NH in NHs:
					if NH not in RT_NH[hostname][vrf]:
						RT_NH[hostname][vrf][NH]=1
					else:
						RT_NH[hostname][vrf][NH]+=1
		
	ppr(RT_NH)
	
	return RT_NH
		 
def filterRTMultipath(RTCur,mode='mbgp'):

	RTfiltered={}
	
	for hostname in RTCur:
		for vrf in RTCur[hostname]:
			for route in RTCur[hostname][vrf]:
				nb_path=int(route[1][0])
				if nb_path <= 1:
					continue
				nexthops=route[2]
				if len(nexthops) <= 1:
					pdb.set_trace()
					print('warning nb path do not match nb nexthop')
					
					
				protocoles=[]
				types=[]
				for nh in nexthops:
					protocoleCur=nh[1]
					if nh[2]:
						typeCur='i'
					else:
						typeCur='e'
					if 	protocoleCur not in protocoles:
						protocoles.append(protocoleCur)
					if 	typeCur not in types:
						types.append(typeCur)
					'stop'
						
				if protocoles!=['B']:
					continue
					
				
				if mode=='mbgp':
					if hostname not in RTfiltered:
						RTfiltered[hostname]={}
					if vrf not in RTfiltered[hostname]:
						RTfiltered[hostname][vrf]=[]
						
					RTfiltered[hostname][vrf].append(route)
					continue
				if mode=='mebgp':
					if types==['e']:
						if hostname not in RTfiltered:
							RTfiltered[hostname]={}
						if vrf not in RTfiltered[hostname]:
							RTfiltered[hostname][vrf]=[]
							
						RTfiltered[hostname][vrf].append(route)					
				
				if mode=='mibgp':
					if types==['i']:
						if hostname not in RTfiltered:
							RTfiltered[hostname]={}
						if vrf not in RTfiltered[hostname]:
							RTfiltered[hostname][vrf]=[]
							
						RTfiltered[hostname][vrf].append(route)				
				
				if mode=='meibgp':
					if 'i' in types and 'e' in types:
						if hostname not in RTfiltered:
							RTfiltered[hostname]={}
						if vrf not in RTfiltered[hostname]:
							RTfiltered[hostname][vrf]=[]
							
						RTfiltered[hostname][vrf].append(route)						
				
	return 	RTfiltered	
				
				
if __name__ == '__main__':
	"Extract BGP Multipath"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-d","--directory",action="store",help="directory containing show ip route",required=False)
	group1.add_argument("-y","--yaml-file",action="store",dest='yamlfile',help="yaml file containing route in yaml format",required=False)
	parser.add_argument("-s","--save" ,action="store", help="file (tag) for saving result",required=False)
	
	parser.add_argument("-e","--extract" ,action="store_true",help="extract bgp multipath BGP",required=False)
	parser.add_argument("-c","--count" ,action="store_true",help="count route",required=False)
	parser.add_argument("-n","--nh-only" ,dest='nhonly',action="store_true",help="extract only next hop",required=False)
	
	group2.add_argument("--multipath-bgp" ,dest='mbgp',action="store_true",help="filter multipath BGP",required=False)
	group2.add_argument("--multipath-ebgp" ,dest='mebgp',action="store_true",help="filter multipath eBGP",required=False)
	group2.add_argument("--multipath-ibgp" ,dest='mibgp',action="store_true",help="filter multipath iBGP",required=False)
	group2.add_argument("--multipath-eibgp" ,dest='meibgp',action="store_true",help="filter multipath eiBGP",required=False)
	
	args = parser.parse_args()
	
	RT={}

	if args.directory:
		for file in glob.glob(args.directory+'/*.log'):
			hostCur=getHostnameFromPathFile(file)
			print(f'Processing {hostCur}:{file}...')
			RTCur=ParseIpRouteNexusSpec(file)
			RT[hostCur]=RTCur
			
	if args.yamlfile:
		print(f'Loadin yaml file {args.yamlfile}...')
		RT=loadYaml(args.yamlfile)
		print(f'yaml file {args.yamlfile} loaded')
		
	if args.save and not args.yamlfile:
		saveResult(RT,args.save)
	
	if args.count:
		countRT(RT)

	if args.nhonly:
		extractNH_RT(RT)
		
	filtering=False
	
	if args.mbgp:
		mode='mbgp'
		filtering=True

	if args.mebgp:
		mode='mebgp'
		filtering=True

	if args.mibgp:
		mode='mibgp'
		filtering=True

	if args.meibgp:
		mode='meibgp'
		filtering=True		

	if filtering:
		RTFiltered=filterRTMultipath(RT,mode=mode)
		
		ppr(RTFiltered)
		
		if args.save:
			saveResult(RTFiltered,args.save+'_'+mode.upper(),path=PATH_YAML_RESULT)


		
		
	
		