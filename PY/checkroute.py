#!/usr/bin/env python3.8
# -*- coding: utf-8 -*- 

import string
import re
import os
import optparse
from ipcalc import * 
import pdb
import pickle
from ParsingShow import ParseIpRoute
import pdb
import jinja2
from netaddr import IPNetwork

class prefix(object):
	"definit une route, un prefix"
	def __init__(self,protocole="C",reseau="1.2.3.4/32",gateway="0.0.0.0",ligne="TOBEDEFINED",tab=[]):
		"Constructeur"
		self.protocole=protocole
		self.reseau=Network(reseau)
		self.nexthop=gateway
		#pdb.set_trace()
		if ligne!="TOBEDEFINED":
			self.init_str(ligne)
		elif tab:
			#pdb.set_trace()
			if len(tab)==3:
				try:
					self.protocole=tab[0]
				except IndexError:
					self.protocole="UNKNOWN"
				try:
					self.reseau=Network(tab[1])
				except IndexError:
					self.reseau="255.255.255.255/32"
				try:
					self.nexthop=tab[2]
				except IndexError:
					self.gateway="0.0.0.0"
			elif len(tab)==2 and tab[0]=='DEFAULT':
				self.protocole='UNKNOWN'
				self.reseau=Network('0.0.0.0/0')
				self.gateway=tab[1]
				
	
	def __list__(self):
		return [self.protocole,self.reseau,self.nexthop]
		
	def safelist(self):
		return [self.protocole,self.reseau.__str__(),str(self.nexthop)]
		
	def __str__(self):
		"Pour l'affichage"
		return self.protocole+" "+self.reseau.__str__()+" vers:"+str(self.nexthop)

	def __repr__(self):
		"Pour l'affichage"
		return self.protocole+" "+self.reseau.__str__()+" vers:"+str(self.nexthop)
		
	def str_short(self):
		"Pour l'affichage"
		return self.protocole+":"+self.reseau.__str__()+"=>"+str(self.nexthop)
		
	def init_str(self,ligne):
		"initialisation a partir d'une ligne de fichier"
		elements=ligne.split()
		self.protocole=elements[0]
		#print(elements[1])
		try:
			self.reseau=Network(elements[1])
		except ValueError:	
			print ("Erreur :"+elements[1]+" N'est pas une IP")
			print("Ligne:"+ligne)
		self.nexthop=elements[2]
	def test_eq_reseau(self,other):
		return self.reseau.__str__() == other.reseau.__str__() and str(self.reseau.subnet()) == str(other.reseau.subnet())
		
	def __eq__(self,other):
		return self.protocole==other.protocole and self.reseau.__str__() == other.reseau.__str__() and str(self.reseau.subnet()) == str(other.reseau.subnet()) and self.nexthop==other.nexthop
		
	def __mod__(self,other):
		resultat=False
		
		if self.reseau==other.reseau:
			if type(self.nexthop)==list and type(other.nexthop)==list:
				if len(self.nexthop)==1:
					resultat=(self.nexthop[0] in other.nexthop) and self.protocole==other.protocole and self.reseau.__str__() == other.reseau.__str__()
				elif len(other.nexthop)==1:
					resultat=(other.nexthop[0] in self.nexthop) and self.protocole==other.protocole and self.reseau.__str__() == other.reseau.__str__()
					
				elif len(other.nexthop)==2 and len(self.nexthop)==2:
					resultat=(other.nexthop[0]==self.nexthop[0] and other.nexthop[1]==self.nexthop[1]) or (other.nexthop[0]==self.nexthop[1] and other.nexthop[1]==self.nexthop[0])
				else:
					resultat=sort(self.nexthop.copy())==sort(other.nexthop.copy()) and self.protocole==other.protocole and self.reseau.__str__() == other.reseau.__str__()
					
		return resultat
		
	def __contains__(self,other):
		
		if isinstance(other,str):
			return IP(other) in self.reseau
		else:
			return self.reseau.__contains__(other.reseau) and self.nexthop==other.nexthop

	def __contains__(self,other):
		
		if isinstance(other,str):
			return IP(other) in self.reseau
		else:
			return self.reseau.__contains__(other.reseau) and self.nexthop==other.nexthop		
	
	def __ior__(self,other):
		
		if isinstance(other,str):
			return IP(other) in self.reseau
		else:
			return self.reseau.__contains__(other.reseau)	
	
	def get_reseau_str(self):
		return self.reseau.__str__()
		
			
				
class liste_prefix(object):
	def __init__(self,file__):
		self.liste_prefix_src_dst=[]
		self.liste_proto_nh_src=[]
		self.dict_proto_nh_src={}
		with open(file__,'r') as file_src_dst:
			for ligne in file_src_dst:
				ligne_col=[ x for x in  re.split(';',ligne.replace("\n","").replace("\r",""))  if x ]
				self.liste_prefix_src_dst.append(ligne_col)
				self.liste_proto_nh_src.append((ligne_col[0],[ligne_col[1]]))
				self.dict_proto_nh_src[str((ligne_col[0],[ligne_col[1]]))]=(ligne_col[2],[ligne_col[3]])
		#pdb.set_trace()
		'stop'
	def __contains__(self,duple_proto_prefix):
		return duple_proto_prefix in self.liste_proto_nh_src

	def replace(self,prefix_old_obj):
		
		
		if (prefix_old_obj.protocole,prefix_old_obj.nexthop) in self:
			try:
				new_proto_nh=self.dict_proto_nh_src[str((prefix_old_obj.protocole,prefix_old_obj.nexthop))]
				resultat=prefix(new_proto_nh[0],prefix_old_obj.reseau,new_proto_nh[1])
			except KeyError as keyerror:
				print(keyerror)
				resultat=prefix_old_obj
		else:
			resultat=prefix_old_obj
		
		return resultat
		
			 
		 
			
class table_routage(object):
	def __init__(self,nom_fichier=None,liste_prefix=[]):
		"Constructeur"
		
		self.toto="TOTO"
		self.tab_prefix_dict={}
		self.tab_prefix=[]
		self.tab_prefix_dict_only={}
			
	
		
		if nom_fichier:
			try:
				fichier=open(nom_fichier,"r")
				for ligne in fichier:
					prefix_cur=prefix(ligne=ligne)
					self.tab_prefix.append(prefix_cur)
					self.tab_prefix_dict[prefix_cur.str_short()]=prefix_cur
					prefix_cur_str_net=prefix_cur.reseau.__str__()
					if prefix_cur_str_net not in self.tab_prefix_dict_only:
						self.tab_prefix_dict_only[prefix_cur_str_net]=[prefix_cur]
					else:
						self.tab_prefix_dict_only[prefix_cur_str_net].append(prefix_cur)
					#pdb.set_trace()
			except IOError:
				print("Fichier inaccessible")
				exit()
			else:
				fichier.close()
		elif liste_prefix:
			for entry in liste_prefix:
				#pdb.set_trace()
				if isinstance(entry,list):
					prefix_cur=prefix(tab=entry)
				elif isinstance(entry,prefix):
					prefix_cur=entry
				self.tab_prefix.append(prefix_cur)
				self.tab_prefix_dict[prefix_cur.str_short()]=prefix_cur
				
				prefix_cur_str_net=prefix_cur.reseau.__str__()
				if prefix_cur_str_net not in self.tab_prefix_dict_only:
					self.tab_prefix_dict_only[prefix_cur_str_net]=[prefix_cur]
				else:
					self.tab_prefix_dict_only[prefix_cur_str_net].append(prefix_cur)


				
				
		else:
			self.tab_prefix_dict={}
			self.tab_prefix=[]
				
		
	def __str__(self):
		"Pour l'affichage"
		result=""
		for route in self.tab_prefix:
			result+=route.__str__()+"\n"
		return result
	
	def __contains__(self,prefix__obj):
		resultat=False
		#pdb.set_trace()
		#print(self.toto)
		#print(str(self.tab_prefix))
		try:
			A=self.tab_prefix_dict[prefix__obj.str_short()]
			resultat=True
		except KeyError:
			resultat=False
			pass
		
		return resultat

	def test_presence_prefix_only(self,prefix__obj):
		
		resultat=False
		try:
			A=self.tab_prefix_dict_only[prefix__obj.reseau.__str__()]
			resultat=True
		except KeyError:
			resultat=False
			pass
		return resultat
			
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def get_allroute(self,prefix_recherche):
		resultat=[]

		for route__ in self.tab_prefix:
			route__prefix=route__
			if prefix_recherche in route__prefix:
				resultat.append(route__prefix)

				
		return resultat
		
	def get_min_route(self,liste_prefix):
		resultat=prefix(tab=['U','0.0.0.0/0','0.0.0.0'])
		max=0
		for prefix__ in liste_prefix:
			if prefix__.reseau.subnet() >= max:
				max=prefix__.reseau.subnet()
				resultat=prefix__
				
		return resultat
		
	def get_route(self,prefix_recherche):
		return self.get_min_route(self.get_allroute(prefix_recherche))
			
			
	def check_presence(self,other):
		"Verifie la presence dans la table plus globale(la table reelle)"
		Message={}
		test_=False
		for reseau in self.tab_prefix:
			Message[reseau.get_reseau_str()]="/!\/!\/!\ALERTE/!\/!\/!\ ROUTE KO:"
			for other_reseau in other.tab_prefix:
				if other_reseau==reseau:
					Message[reseau.get_reseau_str()]="ROUTE PRESENTE:"+other_reseau.__str__()
					test_=True
					break
			if not test_ :
				for other_reseau in other.tab_prefix:
					if reseau in other_reseau:
						Message[reseau.get_reseau_str()]="!!WARNING!! ROUTE PRESENTE:"+other_reseau.__str__()+" ROUTAGE NON ADEQUAT:"+reseau.__str__()
						test_=True
						break
						#print(Message[reseau.get_reseau_str()])
			else:
				Message[reseau.get_reseau_str()]+=reseau.__str__()
				
		return Message
		
	def check_presence_from_dump(self,other,optionNoAlert=False,optionOptimisation=False,ReplaceObj=None,optionPrefixOnly=False):
		"Verifie la presence dans la table plus globale(la table reelle)"
		Message={}
		test_route_exacte=False
		test_route_plus_globale=False
		
		for reseau__ in self.tab_prefix:
			if ReplaceObj:
				reseau=ReplaceObj.replace(reseau__)
			else:
				reseau=reseau__
			Message[reseau.get_reseau_str()]="/!\/!\/!\ALERTE/!\/!\/!\ ROUTE KO:"+reseau__.__str__()
			test_route_exacte=False
			test_route_plus_globale=False
			
			
			if optionPrefixOnly:
				if other.test_presence_prefix_only(reseau) :
					Message[reseau.get_reseau_str()]="ROUTE PRESENTE (NEXT-HOP NON VERIFIE):"+reseau.__str__()
					test_route_exacte=True
				
					
					
				if not optionOptimisation and not test_route_exacte:
					for other_reseau__ in other.tab_prefix:
						if reseau in other_reseau__:
							test_route_plus_globale=True
							break
					if test_route_plus_globale:
						#pdb.set_trace()
						best_route=other.get_route(reseau)
						
							
						Message[reseau.get_reseau_str()]="!!WARNING!! ROUTE PRESENTE:"+best_route.__str__()+" ROUTAGE NON ADEQUAT:"+reseau.__str__()

			else:
				if reseau in other:
					Message[reseau.get_reseau_str()]="ROUTE PRESENTE:"+reseau.__str__()
					test_route_exacte=True
				
					
				elif optionNoAlert:
					for other_reseau__ in other.tab_prefix:
						other_reseau=prefix(other_reseau__)
						if other_reseau%reseau:
							Message[reseau.get_reseau_str()]="!!WARNING!! ROUTE PRESENTE:"+other_reseau.__str__()+" NEXTHOP SUREMENT OK, IOS XR??:"
							test_route_exacte=True
							break
						elif not optionOptimisation:	
							#pdb.set_trace()
							if reseau in other_reseau:
								test_route_plus_globale=True
					
				if not optionOptimisation and not test_route_exacte:
					for other_reseau__ in other.tab_prefix:
						if reseau in other_reseau__:
							test_route_plus_globale=True
							break
					if test_route_plus_globale:
						#pdb.set_trace()
						best_route=other.get_route(reseau)
						
							
						if optionPrefixOnly:
							pass
						elif best_route.nexthop==reseau.nexthop:
							Message[reseau.get_reseau_str()]="!!WARNING!! ROUTE PRESENTE:"+best_route.__str__()+" ROUTAGE NON ADEQUAT:"+reseau.__str__()
						elif best_route.protocole=='U':
							Message[reseau.get_reseau_str()]+=reseau.__str__()
						else:
							Message[reseau.get_reseau_str()]="!!ALERTE!! ROUTE PRESENTE:"+best_route.__str__()+" NEXTHOP A CHANGE:"+reseau.__str__()
					#else:
					#	Message[reseau.get_reseau_str()]+=reseau.__str__()
					
				#else:
				#	Message[reseau.get_reseau_str()]+=reseau.__str__()				
			

		return Message
					
	def affichage_check_rt(self,messages):
		"Affiche un dictionnaire type message renvoye par check presence"
		for reseau in self.tab_prefix:
			try:
				print(messages[reseau.get_reseau_str()])
			except KeyError as keyerror:
				print(keyerror)
				#pdb.set_trace()
				
		
	def filteredByPrefix(self,Net):
		resultat=[]
		
		NetObj=Network(Net)
		for entry in self.tab_prefix:
			try:
				if isinstance(entry,prefix):
					if NetObj in entry.reseau and NetObj>=entry.reseau:
						resultat.append(entry)
				elif isinstance(entry,list):
					pdb.set_trace()
			except IndexError as e:
				print(e)
				pdb.set_trace()
				
			except TypeError as e:
				print(e)
				pdb.set_trace()
				
			except NameError as e:
				print(e)
				pdb.set_trace()
			except AttributeError as e:
				print(e)
				pdb.set_trace()
		return resultat
		
	def filteredByIP(self,Net):
		resultat=self.get_route(Net)
		
		if resultat.protocole=='U':
			return None
		
		return resultat
		
	def extract_gateway(self,nexthop,mode=""):
		resultat=[]
		
		if not mode:
			for entry in self.tab_prefix:
				try:
					if isinstance(entry,prefix):
						if isinstance(entry.nexthop,list):
							if nexthop in entry.nexthop:
								resultat.append(entry)
						elif isinstance(entry.nexthop,str):
							if entry.nexthop==nexthop:
								resultat.append(entry)
					elif isinstance(entry,list):
						if isinstance(entry[-1],list):
							if nexthop in entry[-1]:
								resultat.append(entry)
						elif isinstance(entry[-1],str):
							if entry[-1]==nexthop:
								resultat.append(entry)
						else:
							pdb.set_trace()
				except IndexError as e:
					print(e)
					#pdb.set_trace()
					
				except TypeError as e:
					print(e)
					#pdb.set_trace()
					
				except NameError as e:
					print(e)
					#pdb.set_trace()
				except AttributeError as e:
					print(e)
					#pdb.set_trace()
					
		elif mode=='inverse':
			for entry in self.tab_prefix:
				try:
					if isinstance(entry,prefix):
						if isinstance(entry.nexthop,list):
							if nexthop not in entry.nexthop:
								resultat.append(entry)
						elif isinstance(entry.nexthop,str):
							if entry.nexthop!=nexthop:
								resultat.append(entry)
					elif isinstance(entry,list):
						if isinstance(entry[-1],list):
							if nexthop not in entry[-1]:
								resultat.append(entry)
						elif isinstance(entry[-1],str):
							if entry[-1]!=nexthop:
								resultat.append(entry)
						else:
							pdb.set_trace()
				except IndexError as e:
					print(e)
					#pdb.set_trace()
					
				except TypeError as e:
					print(e)
					#pdb.set_trace()
					
				except NameError as e:
					print(e)
					#pdb.set_trace()
				except AttributeError as e:
					print(e)
					#pdb.set_trace()
		else:
			print("Mode unknown")
		#pdb.set_trace()
				
		return resultat


	def extract_protocol(self,protocol,mode=""):
		resultat=[]
		
		if not mode:
			for entry in self.tab_prefix:
				try:
					if protocol == entry.protocole:
						resultat.append(entry)
	
					
				except IndexError as e:
					print(e)
					#pdb.set_trace()
					
				except TypeError as e:
					print(e)
					#pdb.set_trace()
					
				except NameError as e:
					print(e)
					#pdb.set_trace()
				except AttributeError as e:
					print(e)
					#pdb.set_trace()
					
		elif mode=='inverse':
			for entry in self.tab_prefix:
				try:
					if protocol != entry.protocole:
						resultat.append(entry)

				except IndexError as e:
					print(e)
					#pdb.set_trace()
					
				except TypeError as e:
					print(e)
					#pdb.set_trace()
					
				except NameError as e:
					print(e)
					#pdb.set_trace()
				except AttributeError as e:
					print(e)
					#pdb.set_trace()
		else:
			print("Mode unknown")
		#pdb.set_trace()
				
		return resultat
		
	def add_entries(self,entries):
		self.tab_prefix.extend(entries)
		
class table_routage_allVRF(object):
	def __init__(self,nom_fichier=None,dict_RT={},dict_RT_obj={},dump=None):
	
		self.dict_RT_AllVRF={}
		self.dict_RT={}
		#pdb.set_trace()
		if dict_RT:
			self.dict_RT_AllVRF=self.setRT_From_dict(dict_RT)
			for vrf__ in dict_RT.keys():
				liste_prefix_cur=[]
				for prefix__ in dict_RT[vrf__]:
					liste_cur=prefix__.__list__()
					liste_cur[1]=str(liste_cur[1])
					liste_prefix_cur.append(liste_cur)
				self.dict_RT[vrf__]=liste_prefix_cur	
			
		if dict_RT_obj:
			self.dict_RT_AllVRF=dict_RT_obj
		
		if nom_fichier:
			#print(nom_fichier)
			dict_cur=ParseIpRoute(nom_fichier)
			self.dict_RT=dict_cur
			self.dict_RT_AllVRF=self.setRT_From_dict(dict_cur)
			
		if dump:
			#pdb.set_trace()
			self.load(dump)
			
			
	def __str__(self):
		result=""
		for VRF__ in self.dict_RT_AllVRF.keys():
			result+="VRF:"+VRF__+"\n"
			result+=self.dict_RT_AllVRF[VRF__].__str__()
		
		return result
	
	def __repr__(self):
		result=""
		for VRF__ in self.dict_RT_AllVRF.keys():
			result+="VRF:"+VRF__+"\n"
			result+=self.dict_RT_AllVRF[VRF__].__str__()
		
		return result
		
	def __getitem__(self,item):
		return self.dict_RT[item]
		
	def keys(self):
		return self.dict_RT.keys()

	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		
		RT=None
		
		#pdb.set_trace()
		
		with open(filename,'rb') as file__:
			RT=pickle.load(file__)
			
		try:
			self.dict_RT=RT.dict_RT
			self.dict_RT_AllVRF=RT.dict_RT_AllVRF
		except:
			print('ERROR')
			
	def setRT_From_dict(self,RT_dict):
		
		resultat={}
		for VRF__ in RT_dict.keys():
			resultat[VRF__]=table_routage(liste_prefix=RT_dict[VRF__])
		
		return resultat
		
	def extract_gateway(self,nexthop,mode=""):
		resultat={}
		
		#pdb.set_trace()
		for VRF__ in self.dict_RT_AllVRF.keys():
			resultat[VRF__]=self.dict_RT_AllVRF[VRF__].extract_gateway(nexthop,mode=mode)
			
		return resultat
		
	def extract_protocol(self,protocol,mode=""):

		resultat={}
		resultat__=table_routage_allVRF()
		
		#pdb.set_trace()
		for VRF__ in self.dict_RT_AllVRF.keys():
			resultat[VRF__]=self.dict_RT_AllVRF[VRF__].extract_protocol(protocol,mode=mode)
			resultat__.add_entries(resultat[VRF__],VRF__)
		return resultat__
		
	def add_entries(self,entries,VRF):
		try:
			self.dict_RT_AllVRF[VRF].add_entries(entries)

		except KeyError:
			self.dict_RT_AllVRF[VRF]=table_routage(liste_prefix=entries)
		
	def extract_gateways(self,liste_nexthop):
		resultat__=table_routage_allVRF()
		
		if isinstance(liste_nexthop,str):
		
			with open(liste_nexthop,'r') as file_nexthop:
				liste_NH=file_nexthop.read().splitlines()
		elif isinstance(liste_nexthop,list):
			liste_NH=liste_nexthop
		print(str(liste_NH))
		
		
		for VRF__ in self.dict_RT_AllVRF.keys():
			for nexthop in liste_NH:
				resultat__.add_entries(self.dict_RT_AllVRF[VRF__].extract_gateway(nexthop),VRF__)
			
		
		return resultat__
		
	def extract_vrf(self,vrf):
		resultat__=None
		try:
			resultat__=table_routage_allVRF(dict_RT_obj={vrf:self.dict_RT_AllVRF[vrf]})
			resultat__.dict_RT={vrf:self.dict_RT[vrf]}
		
		except KeyError:
			print("VRF NON PRESENTE")
		
		return resultat__
		
	def filteredByPrefix(self,ListeVrf,Net):
		
		resultat__=table_routage_allVRF()
		
		for VRF__ in ListeVrf:
			resultat__.add_entries(self.dict_RT_AllVRF[VRF__].filteredByPrefix(Net),VRF__)
		
		return resultat__
		
	def filteredByIP(self,ListeVrf,Net):
		
		resultat__=table_routage_allVRF()
		
		for VRF__ in ListeVrf:
			res_cur=self.dict_RT_AllVRF[VRF__].filteredByIP(Net)
			if res_cur:
				resultat__.add_entries([res_cur],VRF__)
		
		return resultat__
		
	def get_liste(self):
		resultat=[]
		
		#pdb.set_trace()
		for VRF__ in self.dict_RT_AllVRF.keys():
			for entry in self.dict_RT_AllVRF[VRF__].tab_prefix:
				try:
					resultat.append([VRF__,*entry.__list__()])
				except AttributeError:
					pdb.set_trace()
					
				except TypeError as typerror:
					print(typerror)
					pdb.set_trace()
			
		return resultat
		
	def getNH(self):
		resultat={}
		
		for VRF__ in self.dict_RT_AllVRF.keys():
			for entry in self.dict_RT_AllVRF[VRF__].tab_prefix:
				if isinstance(entry.nexthop,list):
					for nh in entry.nexthop:
						if VRF__ not in resultat:
							resultat[VRF__]={nh:{entry.protocole:1}}
						else:
							if nh in resultat[VRF__]:
								if entry.protocole in resultat[VRF__][nh]:
									old_total=resultat[VRF__][nh][entry.protocole]
									resultat[VRF__][nh][entry.protocole]=old_total+1
								else:
									resultat[VRF__][nh][entry.protocole]=1
							else:
								resultat[VRF__][nh]={entry.protocole:1}
				else:
					if VRF__ not in resultat:
						resultat[VRF__]={entry.nexthop:{entry.protocole:1}}
					else:
						if entry.nexthop in resultat[VRF__]:
							if entry.protocole in resultat[VRF__][entry.nexthop]:
								old_total=resultat[VRF__][entry.nexthop][entry.protocole]
								resultat[VRF__][entry.nexthop][entry.protocole]=old_total+1
							else:
								resultat[VRF__][entry.nexthop][entry.protocole]=1
						else:
							resultat[VRF__][entry.nexthop]={entry.protocole:1}	

			
							
			
		return resultat
		
	def get_dict(self):
		resultat={}
		
		#pdb.set_trace()
		for VRF__ in self.dict_RT_AllVRF.keys():
			resultat[VRF__]=[]
			for entry in self.dict_RT_AllVRF[VRF__].tab_prefix:
				try:
					resultat[VRF__].append([*entry.safelist()])
				except AttributeError:
					pdb.set_trace()
					
				except TypeError as typerror:
					print(typerror)
					pdb.set_trace()
			
		return resultat
		
	def getAllVRF(self):
		return list(self.dict_RT_AllVRF.keys())
		
	def format(self,yamlfile):
		loader = jinja2.FileSystemLoader(os.path.dirname(yamlfile))
		env = jinja2.Environment( loader=loader)
		templates=env.get_template(os.path.basename(yamlfile))
		resultat=templates.render({"allroute":self.dict_RT})
		
		return resultat
			
if __name__ == '__main__':
	
	parser = optparse.OptionParser()
	parser.add_option('-i','--input-file',help='fichier contenant les routes cibles format dump',dest='CIBLE_FILE', default='ROUTE/dub-b1.cfg',action='store')
	parser.add_option('-e','--existant',help='fichier contenant les routes actuelles format dump',dest='COURANT_FILE', default='ROUTE-RDS-CMC/dub-b1.format.log',action='store')
	parser.add_option('--vi','--vrf-input',help='fichier contenant les routes actuelles',dest='CIBLE_VRF', default='ALL',action='store')
	parser.add_option('--ve','--vrf-existant',help='fichier contenant les routes actuelles',dest='COURANT_VRF', default='ALL',action='store')
	parser.add_option('-p','--prefix-only',help='vérifie seulement la présence du prefix (pas du next-hop)',dest='PREFIX_ONLY',action='store_true',default=False)
	parser.add_option('--na','--no-alert',help='si un NH présent => warning et pas alerte pour IOS XR (backup route)',dest='NO_ALERT',action='store',default=False)
	parser.add_option('-o','--optimisation',help='Mode optimisé ne check que la route précise',dest='OPTIMISATION',action='store_true',default=False)
	parser.add_option('-r','--replace',help='Remplacement du next hop, fichier format ligne:PROTOCOLE NEXTHOP',dest='REPLACE_FILE',action='store',default=None)
	
	(opts, args) = parser.parse_args()
	
	
	if opts.REPLACE_FILE:
		liste_prefix_replace=liste_prefix(opts.REPLACE_FILE)
	
	if not (opts.CIBLE_VRF=="ALL" or opts.COURANT_VRF=="ALL") :
		CIBLE=table_routage_allVRF(dump=opts.CIBLE_FILE).dict_RT_AllVRF[opts.CIBLE_VRF]
		COURANT=table_routage_allVRF(dump=opts.COURANT_FILE).dict_RT_AllVRF[opts.COURANT_VRF]
		
		if opts.REPLACE_FILE:
			CIBLE.affichage_check_rt(CIBLE.check_presence_from_dump(COURANT,optionNoAlert=opts.NO_ALERT,optionOptimisation=opts.OPTIMISATION,ReplaceObj=liste_prefix_replace))
		else:
			CIBLE.affichage_check_rt(CIBLE.check_presence_from_dump(COURANT,optionNoAlert=opts.NO_ALERT,optionOptimisation=opts.OPTIMISATION,optionPrefixOnly=opts.PREFIX_ONLY))
	else:
		for VRF__ in table_routage_allVRF(dump=opts.CIBLE_FILE).getAllVRF():
			print("Vérification de la table:"+VRF__)
			try:
				CIBLE=table_routage_allVRF(dump=opts.CIBLE_FILE).dict_RT_AllVRF[VRF__]
				COURANT=table_routage_allVRF(dump=opts.COURANT_FILE).dict_RT_AllVRF[VRF__]
				if opts.REPLACE_FILE:
					CIBLE.affichage_check_rt(CIBLE.check_presence_from_dump(COURANT,optionNoAlert=opts.NO_ALERT,optionOptimisation=opts.OPTIMISATION,ReplaceObj=liste_prefix_replace))
				else:
					CIBLE.affichage_check_rt(CIBLE.check_presence_from_dump(COURANT,optionNoAlert=opts.NO_ALERT,optionOptimisation=opts.OPTIMISATION,optionPrefixOnly=opts.PREFIX_ONLY))
			except KeyError:
				print("VRF absente:"+VRF__)
				print("Routes non trouvées:\n")
				print(str(table_routage_allVRF(dump=opts.CIBLE_FILE).dict_RT_AllVRF[VRF__]))
