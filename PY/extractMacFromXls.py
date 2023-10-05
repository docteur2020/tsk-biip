#!/usr/bin/env python3.7
# coding: utf-8

import re
import csv
import xlrd
import argparse
import pdb
import pyparsing as pp
import io
import pickle



class hostnames(object):
	def __init__(self,xls="",dump=""):
	
		self.ips={}
		self.names={}
		if xls:
			with open(xls, 'r') as csvfile:
				wb=xlrd.open_workbook(xls)
				sh = wb.sheet_by_name(u'splunk_results_1')
				for rownum in range(1,sh.nrows):
					hostname=sh.row_values(rownum)[1]
					try:
						macs_cur=self.get_liste_mac(sh.row_values(rownum)[17])
					except TypeError as e:
						print(e)
					if macs_cur:
						self.ips.update(macs_cur.asList()[0])
						for mac__ in macs_cur.asList()[0]:
							self.names[mac__]=hostname
					#pdb.set_trace()
		elif dump:
			self.load(dump)
			
		
	def __str__(self):
		resultat=io.StringIO()
		
		for mac__ in self.ips.keys():
			resultat.write(mac__+":Hostname=>"+self.names[mac__]+" IP(s)=>"+str(self.ips[mac__])+"\n")
		
		return resultat.getvalue()
		
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		hostnames__=None
		
		with open(filename,'rb') as file__:
			hostnames__=pickle.load(file__)
			
		try:
			self.ips=hostnames__.ips
			self.names=hostnames__.names
			
		except:
			print('ERROR LOAD DUMP')
	
	@staticmethod	
	def mac_to_cisco(mac_srv):
		
		resultat=mac_srv
		if mac_srv != 'NULL':
			if re.search("-",mac_srv):
				mac_cisco=mac_srv.split('-')
				try:
					resultat=(mac_cisco[0]+mac_cisco[1]+"."+mac_cisco[2]+mac_cisco[3]+"."+mac_cisco[4]+mac_cisco[5]).lower()
				except IndexError:
					pdb.set_trace()
			elif re.search(":",mac_srv):
				mac_cisco=mac_srv.split(':')
				try:
					resultat=(mac_cisco[0]+mac_cisco[1]+"."+mac_cisco[2]+mac_cisco[3]+"."+mac_cisco[4]+mac_cisco[5]).lower()
				except IndexError:
					pdb.set_trace()
			else:
				resultat='NULL'
		
				
		else:
			resultat='NULL'


		return resultat
		
	def get_info_mac(self,mac__):
		resultat=None
		try:
			resultat={"IP":self.ips[mac__],"Hostname":self.names[mac__]}
		except KeyError:
			pass
			
		return  resultat
		
	def get_info_macs(self,file_mac):
		with open(file_mac,'r') as fich__:
			for mac in fich__:
				mac__=mac.strip()
				print(mac__+";"+str(self.get_info_mac(mac__)))
				
	def macs_to_dict(self,string,location,token):
		Resultat={}

		try:
			ListeEntry=token[0]
			for entry in ListeEntry:
				try:
					ListeIP_cur=entry[0].asList()
					Liste_Mac=entry[1].asList()
				except AttributeError:
					ListeIP_cur=entry[0]
					Liste_Mac=entry[1]
				for mac__ in Liste_Mac:
					temp_resultat=Resultat
					if mac__ in Resultat.keys():
						try:
							Resultat[mac__]=self.merge_list(temp_resultat[mac__],ListeIP_cur)
						except TypeError:
							pdb.set_trace()
					else:
						Resultat[mac__]=ListeIP_cur
				
		except KeyError as e:
			print(e)

			
		except IndexError as e2:
			print(e2)
			
		finally:
			print("TOKEN:"+str(token.asList()))
	
			
	
		return Resultat	

	def merge_list(self,list1,list2):
		resultat=set().union(list1,list2)
		
		return list(resultat)
				
	def get_liste_mac(self,macs_str):
		macs_result_dict={}
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		ipAddresses=pp.Group(ipAddress+pp.Optional(pp.OneOrMore(pp.Suppress(pp.Literal('-')|pp.Literal('|'))+	ipAddress)))
		hexint = pp.Word(pp.hexnums,exact=2)
		macAddress = (pp.Combine(hexint + (':'+hexint)*5)).setParseAction(lambda tokens: self.mac_to_cisco(tokens[0]))
		macsAddresses = pp.Group(macAddress+pp.Optional(pp.OneOrMore(pp.Suppress(pp.Literal('-'))+	macAddress)))
		Null=pp.Suppress(pp.MatchFirst([pp.Literal('---NULL---'),pp.Literal('---NULL--'),pp.Literal('---NULL-'),pp.Literal('--NULL---'),pp.Literal('--NULL--'),pp.Literal('--NULL-'),pp.Literal('-NULL-'),pp.Literal('--NULL'),pp.Literal('NULL---'),pp.Literal('NULL--'),pp.Literal('NULL-')]))
		Separator=pp.MatchFirst([Null,pp.Literal('---'),pp.Literal('--'),pp.Literal('-'),pp.Literal('|'),pp.Literal('*'),pp.Word('NULL-|')]).suppress()
		ListeIP1=Separator+ipAddress.suppress()+pp.Optional(pp.Suppress(pp.OneOrMore(pp.Literal('/')+ipAddress)))+Separator
		ListeIP2=Separator+pp.OneOrMore(ipAddress)+Separator
		ListeIP3=Separator+ipAddress.suppress()+pp.Optional(pp.Suppress(pp.OneOrMore(pp.Literal(',')+ipAddress)))+Separator
		Entry_NoEmpty=pp.Optional(Separator)+pp.Group(ipAddresses+Separator+macsAddresses)+pp.Optional(Separator)
		Entry_Empty=Null|pp.Suppress(pp.MatchFirst([ListeIP1,ListeIP2,ListeIP3]))
		Entry_MacFirst=pp.Group((pp.OneOrMore(Separator)+macAddress+pp.Literal('-')+ipAddress).setParseAction(lambda token: [[token[2]],[token[0]]]))
		ipv6=(pp.CaselessLiteral('fe80:')|pp.Literal('2002:'))+pp.OneOrMore(pp.CharsNotIn(' '))
		EntryWithipv6=pp.Suppress(ipv6)+pp.Group(Entry_NoEmpty)
		Entry=pp.MatchFirst([Entry_NoEmpty,Entry_MacFirst,Entry_Empty,EntryWithipv6])

		Entries=(pp.Group(Entry+pp.Optional(Separator+pp.OneOrMore(Entry)))+pp.Optional(Separator+ipAddress.suppress())).setParseAction(self.macs_to_dict)
		
		print("MACS_STR:"+macs_str)
		try:
			macs_result_dict=Entries.parseString(macs_str)
		except pp.ParseException as e:
			#print(e)
			print('Entry not parsed:'+macs_str)
			pass
		except RecursionError as recur_err:
			print('Recursion Error:'+macs_str)
			#pdb.set_trace()
			
		except TypeError as type_err:
			print('type error:'+macs_str)
			print(type_err)
			#pdb.set_trace()
		finally:
			print(macs_result_dict)
		
			
		return macs_result_dict
		

				
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-x", "--xls",action="store",help="Contient le fichier resultat en xls")
	parser.add_argument("-l", "--liste_mac",action="store",help="Contient la liste des macs a traiter",required=False)
	group1.add_argument("-d", "--dump",action="store",help="Chargement du dump")
	parser.add_argument("-s", "--save",action="store",help="Sauvegarde dans le fichier dump",required=False)
	args = parser.parse_args()
	
	if args.xls:
		HOSTS__=hostnames(xls=args.xls)
		print("OK")

		if args.liste_mac:
			print("MAC trouve")
			HOSTS__.get_info_macs(args.liste_mac)
			
		if args.save:
			print("Sauvegarde dans fichier DUMP:"+args.save)
			HOSTS__.save(args.save)
			
	elif args.dump:
		HOSTS__=hostnames(dump=args.dump)
		print("Affichage")
		print(HOSTS__)
		if args.liste_mac:
			print("MAC trouve")
			HOSTS__.get_info_macs(args.liste_mac)
