#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals


import re
import argparse
import pdb
import yaml
from pprint import pprint as ppr
import bgpNeighbor
from xlsxToDict import xlsContainer
from connexion import runActionCache , runListData , getHostsFromEnv , equipement

class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)
Loader__.add_constructor('!include', Loader__.include)

def intersect(lst1, lst2):
	lst3 = [value for value in lst1 if value in lst2]
	return lst3
	
def diffBgpTable(table1,table2):
	missingIn2=[value for value in table1 if value not in  table2]
	missingIn1=[value for value in table2 if value not in  table1]
	
	return {'missing in table 1': missingIn1 , 'missing in table 2': missingIn2 }
	
class diffBgpNeighbor(object):
	def __init__(self,xlsxFile,renew=False):
		datasDict=xlsContainer(xlsxFile).datas
		key=list(datasDict.keys())[0]
		self.datas=datasDict[key]
		self.bgpNeigbors=[]
		self.renew=renew
		for entry in self.datas:
			bgpNeighbor1=bgpNeighbor.bgpNeighbor(entry['host1'],entry['neigh1'],entry['vrf1'],renew=self.renew)
			bgpNeighbor2=bgpNeighbor.bgpNeighbor(entry['host2'],entry['neigh2'],entry['vrf2'],renew=self.renew)
			self.bgpNeigbors.append({'neigh1':bgpNeighbor1 ,'neigh2':bgpNeighbor2 })
			
	def diffRcvAdvPrefix(self):
		
		diffResult=[]
		
		for bgpPeering in self.bgpNeigbors:
			
			prefixes1=bgpPeering['neigh1'].getAllPrefixList(filterNH=[bgpPeering['neigh1'].ip])
			prefixes2=bgpPeering['neigh2'].getAllPrefixList(filterNH=[bgpPeering['neigh2'].ip])
			
			namePeer1=str(bgpPeering['neigh1'])
			namePeer2=str(bgpPeering['neigh2'])
			
			print(f'Difference between {namePeer1} advertised-routes and {namePeer2} received-routes')
			result1=diffBgpTable(prefixes1['advertised-routes'],prefixes2['routes'])
			ppr(result1)

			print(f'Difference between {namePeer2} advertised-routes and {namePeer1} received-routes')
			result2=diffBgpTable(prefixes2['advertised-routes'],prefixes1['routes'])
			ppr(result2)			
			
if __name__ == '__main__':
	"Extract BGP Neighbor informations"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-x","--xlsx",action="store",help="BGP Neighbor xlsxFile",required=True)
	parser.add_argument("-r","--renew",action="store_true",default=False ,help="resync fabric data ",required=False)
	args = parser.parse_args()
	
	bgpNeighDatas=diffBgpNeighbor(args.xlsx,renew=args.renew)
	bgpNeighDatas.diffRcvAdvPrefix()


		
		
	
		