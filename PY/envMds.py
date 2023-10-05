#!/bin/python3.8
# coding: utf-8

import sys
import argparse
import pdb
import yaml
import os
from time import gmtime, strftime , localtime ,ctime
from cpapi import  APIClientArgs , APIResponse
from pprint import pprint as ppr
import glob
import ntpath
from itertools import product

import checkpoint.CheckpointSBE as ckp

yaml.Dumper.ignore_aliases = lambda *args : True

MDS_YAML='/home/x112097/yaml/checkpoint/mds.yml'
ALIAS_YAML='/home/x112097/yaml/checkpoint/fw_alias.yml'
DIR_YAML_SAVE='/home/x112097/yaml/checkpoint/bck'
KEY_UID=["action","content","destination","uid","objects","install-on","service","source","time","vpn","type"]

def saveData(data,yaml_tag,sub_dir=''):
	suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
	if sub_dir:
		filename=DIR_YAML_SAVE+'/'+sub_dir+'/'+yaml_tag+suffix
	else:
		filename=DIR_YAML_SAVE+'/'+yaml_tag+suffix
	with open(filename,'w') as yml_w:
		print(f"Saving file:{filename}")
		yaml.dump(data,yml_w ,default_flow_style=False)

def loadData(yaml_file):
	data__=None
	with open(yaml_file) as io_yml:
		data__=yaml.load(io_yml,Loader=yaml.SafeLoader)
	return data__
	
def getTimeFile(file__):
	return f"last modified {ntpath.basename(file__)}:{ctime(os.path.getmtime(file__))}"

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet
		
def getLastObjectsDb(mds__,domain__):
	
	tag__=f'{mds__}_{domain__}'
	path__=DIR_YAML_SAVE+'/'+'objects_db/'
	lastDump=max(glob.glob(path__+'/*'),key=os.path.getctime)
	#print("dump:",lastDump)
	return {'date': getTimeFile(lastDump),'data':lastDump}
	
def initObjectUidDict(responseApi):
	result={}
	
	if 'objects-dictionary' not in responseApi.data:
		return result
	
	for objectUid in responseApi.data['objects-dictionary']:
		objectUidCur=objectUid.copy()
		del objectUidCur['uid']
		del objectUidCur['domain']
		result[ objectUid['uid']]=objectUidCur
	
	return result
	
def replaceUidinDictList(dictOrList,objectUid,):
	if isinstance(dictOrList,dict):
		
		for key in dictOrList:
			if  key in KEY_UID:
				if isinstance(dictOrList[key],str):
					entry=dictOrList[key]
					if dictOrList[key] in objectUid:
						dictOrList[key]=objectUid[entry]
				elif isinstance(dictOrList[key],list):
					dataListCur=dictOrList[key].copy()
					for entry in dictOrList[key]:
						index_cur=dictOrList[key].index(entry)
						try:
							dataListCur[index_cur]=objectUid[entry]
						except KeyError:
							pass
						except TypeError as E:
							dictOrList[key]=replaceUidinDictList(dictOrList[key],objectUid)
							continue
					dictOrList[key]=dataListCur
			elif isinstance(dictOrList[key],dict):
				dictOrList[key]=replaceUidinDictList(dictOrList[key],objectUid)
			
			elif isinstance(dictOrList[key],list):
				dictOrList[key]=replaceUidinDictList(dictOrList[key],objectUid)
				
	elif isinstance(dictOrList,list):
		indice=0
		for entry in dictOrList:
			if isinstance(entry,list):
				dictOrList[indice]=replaceUidinDictList(entry,objectUid)
			if isinstance(entry,dict):
				dictOrList[indice]=replaceUidinDictList(entry,objectUid)
			indice+=1
					
	return dictOrList
	
def translateUidRule(responseApi):

	newDataRule=[]
	refUid=initObjectUidDict(responseApi)
	
	if 'rulebase' in responseApi.data:
	
		for entry in responseApi.data['rulebase']:
			RuleCur=entry.copy()
			translateResult=replaceUidinDictList(RuleCur,refUid)
			newDataRule.append(translateResult)
	else:
		pdb.set_trace()
		print('stop')
	
	return newDataRule
	
def extractFilterMatchFromRule(rules):
	result=rules.copy()
	result['rules']={}
	
	
	if not rules['rules']:
		return rule
		
	
	for parag in rules['rules']:
		for entry in parag:
			for sub_rule in entry['rulebase']:
				rule_id=sub_rule['rule-number']
				match_=sub_rule['filter-match-details']
				uid=sub_rule['uid']
			if rule_id not in result:
				result['rules'][rule_id]=[{'uid':uid,'match':match_}]
			else:
				result['rules'][rule_id].append({'uid':uid,'match':match_})
				
				
	return result
	
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	saving=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument('--list-all',dest='list_all',action="store_true",help='display all known mds')
	parser.add_argument('--list-alias',dest='list_alias',action="store_true",help='display all alias')
	parser.add_argument('-m','--mds',action="store",help='MDS Name')
	parser.add_argument('-d','--domain',action="store",help='domain')
	parser.add_argument('-a','--alias',action="store",help='directly set mds/domain/access-layer')
	parser.add_argument('--access-layer',dest='access_layer',action="store",help='access layer name')
	parser.add_argument('--list-domain',dest='list_domain',action="store_true",help='display all domain')
	parser.add_argument('--list-package',dest='list_package',action="store_true",help='display package')
	parser.add_argument('--show-access-layers',dest='show_access_layers',action="store_true",help='display access-layers')
	parser.add_argument('--show-access-rules',dest='show_access_rules',action="store_true",help='display access-rules')
	parser.add_argument('--show-access-rule',dest='show_access_rule',action="store_true",help='display access-rule for a rule number')
	parser.add_argument('--show-objects',dest='show_objects',action="store_true",help='display objects')
	parser.add_argument('--set-objects-uid',dest='set_db_objects',action="store_true",help='construct a object/uid db')
	parser.add_argument('--search-object',dest='search_object',action="store_true",help='search a specific object in db')
	parser.add_argument('--translate-uid',dest='translate_uid',action="store_true",help='replace uid by object')
	parser.add_argument('--brief-filter',dest='brief_filter',action="store_true",help='extrat match filter in rules/only with --show-access-rules and filtering')
	parser.add_argument('--src',action="store",help='filter on source IP')
	parser.add_argument('--dst',action="store",help='filter on destination IP')
	parser.add_argument('--file-src',dest='file_src',action="store",help='filter on multiple source IP ')
	parser.add_argument('--file-dst',dest='file_dst',action="store",help='filter on multiple destination IP')
	parser.add_argument('--uid',action="store",help='filter on uid')
	parser.add_argument('--number',action="append",help='rule number')
	parser.add_argument('--name',action="store",help='filter on name')
	saving.add_argument('--save',action="store_true",help='Save result')
	saving.add_argument('--cache',action="store_true",help='Use cache')
	args = parser.parse_args()

	MDS_INFO={}
	
	ALIAS_INFO={}
	
	with open(MDS_YAML,'r') as mds_yml_stream:
		MDS_INFO=yaml.load(mds_yml_stream,Loader=yaml.SafeLoader)
	
	with open(ALIAS_YAML,'r') as alias_yml_stream:
		ALIAS_INFO=yaml.load(alias_yml_stream,Loader=yaml.SafeLoader)
		
	if args.list_all:
		print("\n".join(list(MDS_INFO.keys())))
		
	if args.list_alias:
		ppr(ALIAS_INFO,width=5)
		
	if args.alias:
		if args.alias not in ALIAS_INFO:
			print(f'{args.alias} not found in alias yaml:{ALIAS_YAML}',file=sys.stderr)
			sys.exit(1)
		args.mds=ALIAS_INFO[args.alias]['mds']
		args.domain=ALIAS_INFO[args.alias]['domain']
		args.access_layer=ALIAS_INFO[args.alias]['accessLayerRule']
		
	if args.file_src or args.file_dst:
		modeFile=True
		if args.file_src and args.file_dst:
			modeFilter="SrcDst"
		elif args.file_src:
			modeFilter="Src"
		elif args.file_dst:
			modeFilter="Dst"

		
	else:
		modeFile=False
		modeFilter=None
		
	if args.list_domain:
		if args.mds:
			if args.mds in MDS_INFO.keys():
				print("\n".join(MDS_INFO[args.mds]['domains']))
			else:
				print(f'MDS unknown:{args.mds}')
		else:
			for mds__ in MDS_INFO:
				print('==')
				print(f'MDS {mds__}:')
				for domain__ in MDS_INFO[mds__]['domains']:
					print(f' - {domain__}')
				print('==\n')
				
	if args.list_package:
		if not args.mds or not args.domain:
			parser.error("--mds and --domain is mandatory with --list-package")
			
				
	if args.show_access_layers:
		if not args.mds or not args.domain:
			parser.error("--mds and --domain are mandatory with --show-access-layers")
			
	if args.show_access_rules:
		if not args.mds or not args.domain or not args.access_layer:
			parser.error("--mds, --domain and --access-layer are mandatory with --show-access-rule")

	if args.show_access_rule:
		if not args.mds or not args.domain or not args.access_layer or not args.number:
			parser.error("--mds, --domain, --number and --access-layer are mandatory with --show-access-rule")				
			
	if args.show_objects:
		if not args.mds or not args.domain:
			parser.error("--mds and --domain are mandatory with --show-objects")
			
	if args.set_db_objects:
		if not args.mds or not args.domain:
			parser.error("--mds and --domain are mandatory with --show-objects")
			
	if args.search_object:
		if not args.mds or not args.domain:
			parser.error("--mds and --domain are mandatory with --search-object")
		if not args.uid and not args.name:
			parser.error("--uid or --name are mandatory with --search-object")
	
	if args.list_package or args.show_access_layers:
		if args.mds not in MDS_INFO.keys():
			print(f'MDS unknown:{args.mds}',file=sys.stderr)
			sys.exit(1)
			
		if args.domain not in MDS_INFO[args.mds]['domains']:
			print(f'domain unknown:{args.domain}',file=sys.stderr)
			sys.exit(1)
			
	if args.mds:
		client_args = APIClientArgs(server=MDS_INFO[args.mds]['ip'])
		

	if args.list_package:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			print("Processing. Please wait...")
			list_package = client.api_query("show-packages", "standard")
			if not list_package.success:
				print("Failed to get the list of packages:\n{}".format(list_package.error_message))
				sys.exit(1)
				
			ppr(list_package)
			
	if args.show_access_layers:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			print("Processing. Please wait...")
			importantAttributes=['name','type','uid']
			list_access_layers = client.api_query("show-access-layers", "full")
			if not list_access_layers.success:
				print("Failed to get the list of all access layer:\n{}".format(list_access_layers.error_message))
				sys.exit(1)
			list_access_layers_filtered=[]
			for acl in list_access_layers.data['access-layers']:
				list_access_layers_filtered.append( { k:i for k,i in acl.items() if k in importantAttributes } )
			ppr(list_access_layers_filtered )

	if args.show_access_rule:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			rules={}
			print("Processing. Please wait...")
			
			for num in args.number:
				payload={'layer':args.access_layer,'rule-number':num}
				rule = client.api_call("show-access-rule",  payload)
				rules[num]=rule.data
				
				if not rule.success:
					print(f"Failed to get Rule-numer {num}:\n {rule.error_message}")
					sys.exit(1)
			
			#if args.translate_uid:
			#	translate_rules=[]
			#	for rule in rules:
			#		translate_rules.append(translateUidRule(rule))
			#	ppr(translate_rules)
			#else:
			#	ppr(rules)
			ppr(rules)
			
			if args.save:
				saveData(rules,f'{args.mds}_{args.domain}_RULES',sub_dir='rules')
			
	if args.show_access_rules:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			print("Processing. Please wait...")
			
			payload={'name':args.access_layer,"details-level" : "full"}
			
			if not modeFile:
				if args.src and args.dst:
					filter__=f"src:{args.src} AND dst:{args.dst} AND action:Accept"
				elif args.src:
					filter__=f"src:{args.src} AND action:Accept"
				elif args.dst:
					filter__=f"dst:{args.dst} AND action:Accept"
				else:
					filter__=None
					
				
				if filter__:
					payload['filter']=filter__
					#payload['search-mode']='packet'
	
					
				list_rules = client.api_query("show-access-rulebase",  payload=payload)
				
				if not list_rules.success:
					print("Failed to get Rules:\n{}".format(list_rules.error_message))
					sys.exit(1)
	
				if args.translate_uid:
					translate_rules=translateUidRule(list_rules)
					ppr(translate_rules)
					if args.save:
						saveData(translate_rules,f'{args.mds}_{args.domain}_RULES',sub_dir='rules')
				else:
					ppr(list_rules)
					if args.save:
						saveData(list_rules,f'{args.mds}_{args.domain}_RULES',sub_dir='rules')
			else:
				if args.file_src:
					ListNetSrc=getListNetFromFile(args.file_src)
				if args.file_dst:
					ListNetDst=getListNetFromFile(args.file_dst)
					
				FilterList=[]
				Result=[]
				if modeFilter=="SrcDst":
					filter_template=f"src:<SRC> AND dst:<DST> AND action:Accept"
					AllSrcDst=list(product(ListNetSrc,ListNetDst))
					for src__,dst__ in AllSrcDst:
						entry=filter_template.replace('<SRC>',src__).replace('<DST>',dst__)
						FilterList.append({'src':src__,'dst':dst__,'filter':entry})
				elif modeFilter=="Src":
					filter_template=f"src:<SRC> AND action:Accept"		
					AllSrc=ListNetSrc
					for src__ in AllSrc:
						entry=filter_template.replace('<SRC>',src__)
						FilterList.append({'src':src__,'filter':entry})
				elif modeFilter=="Dst":
					filter_template=f"dst:<DST> AND action:Accept"	
					AllDst=ListNetDst
					for dst__ in AllDst:
						entry=filter_template.replace('<DST>',dst__)
						FilterList.append({'dst':dst__,'filter':entry})
						
					
				

				for filter__ in FilterList:
					payload['filter']=filter__['filter']
					list_rules = client.api_query("show-access-rulebase",  payload=payload)
					Result.append({**filter__,'rules':list_rules})
				
					if not list_rules.success:
						print(f"Failed to get Rules:\n-{list_rules.error_message}\n-filter:{filter__}")
						sys.exit(1)
	
				if args.translate_uid:
					TranslateResult=[]
					for rules in Result:
						entry_cur={}
						for key in rules:
							if key=='rules':
								entry_cur['rules']=translateUidRule(rules['rules'])
							else:
								entry_cur[key]=rules[key]
									
						if args.brief_filter:
							TranslateResult.append(entry_cur)
						else:
							TranslateResult.append(entry_cur)
						
					if args.brief_filter:
						TranslateResultBrief=[]
						for rule in TranslateResult:
							TranslateResultBrief.append(extractFilterMatchFromRule(rule))
						ppr(TranslateResultBrief)
					else:
						ppr(TranslateResult)
					
					if args.save:
						saveData(TranslateResult,f'{args.mds}_{args.domain}_RULES',sub_dir='rules')
					
				else:
					if args.save:
						saveData(Result,f'{args.mds}_{args.domain}_RULES',sub_dir='rules')
					
					if args.brief_filter:
						TranslateResultBrief=[]
						for rule in Result:
							TranslateResultBrief.append(extractFilterMatchFromRule(rule))
						ppr(TranslateResultBrief)
					else:
						ppr(Result)

	if args.show_objects:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			print("Processing. Please wait...")
			importantAttributes=['name','type','uid']
			list_objects = client.api_query("show-objects", payload={"details-level" : "full","offset" : 0,"limit" : 500} )
			if not list_objects.success:
				print("Failed to  Rules:\n{}".format(list_objects.error_message))
				sys.exit(1)
			
			ppr(list_objects)
			
			if args.save:
				saveData(list_objects.data,f'{args.mds}_{args.domain}_OBJECTS')

	
	if args.set_db_objects:
		with ckp.APIClientTunnel(client_args,domain=args.domain) as client:
			client.login()
			dict_object={'uid':{},'name':{}}
			result_tag=f'{args.mds}_{args.domain}'
			print("Processing. Please wait...")
			importantAttributes=['name','type','uid']
			list_objects = client.api_query("show-objects", payload={"details-level" : "full","offset" : 0,"limit" : 500} )
			if not list_objects.success:
				print("Failed to  Rules:\n{}".format(list_objects.error_message))
				sys.exit(1)
			for object__ in list_objects.data:
				cur_obj_data_uid=object__.copy()
				cur_obj_data_name=object__.copy()
				del cur_obj_data_uid['uid']
				del cur_obj_data_name['name']
				dict_object['uid'][object__['uid']]=cur_obj_data_uid
				dict_object['name'][object__['name']]=cur_obj_data_name
			ppr(dict_object)

			saveData(dict_object,result_tag,sub_dir='objects_db')
	
	
	if args.search_object:
		curObject_info=getLastObjectsDb(args.mds,args.domain)
		print(curObject_info['date'])
		curObjectdb=loadData(curObject_info['data'])
		if args.uid:
			if args.uid not in curObjectdb['uid']:
				print(f'{args.uid} not found in db object of mds {args.mds}/{args.domain}',file=sys.stderr)
				sys.exit(1)
			ppr(curObjectdb['uid'][args.uid])
		if args.name:
			if args.name not in curObjectdb['name']:
				print(f'{args.name} not found in db object of mds {args.mds}/{args.domain}',file=sys.stderr)
				sys.exit(1)
			ppr(curObjectdb['name'][args.name])