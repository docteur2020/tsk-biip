#!/usr/bin/env python3.8
# coding: utf-8

import pdb
#import socks
import ssl
import sys
import pwd
import os
from urllib.parse import urlparse, urlencode
from cpapi import  APIClientArgs , APIClient
from cpapi.mgmt_api import HTTPSConnection
import http.client as http_client
from pprint import pprint as ppr

sys.path.insert(0,'/home/d83071/py')
from getsec import *
import cache as cc

from Tunnelier import Tunnelier



PROXIES={'https':'socks5://127.0.0.1:7777','http':'socks5://127.0.0.1:7777'}
TSK="/home/d83071/CONNEXION/pass.db"
SOCKS={'ip':'127.0.0.1' , 'port':7777 , 'proto':'socks5'}
USERNAME='d83071'


	
class  APIClientTunnel(APIClient):
	
	def __init__(self,api_client_args=None,domain=""):
		super().__init__(api_client_args=api_client_args)
		self.initCred()
		#self.tunnel=Tunnelier()
		self.domain=domain
		
	def __enter__(self):
		newUrl=self.tunnel.addUrl('https://%s'%self.server)
		newUrlObj = urlparse(newUrl)
		self.realServer=self.server
		self.server=newUrlObj.netloc.split(':')[0]
		self.set_port(newUrlObj.port)
		self.tunnel.printMessageTunnelCur()
		super().__enter__()
		return self
		
		
	def __exit__(self, exc_type, exc_value, traceback):
		"""destructor"""
		super().__exit__(exc_type, exc_value, traceback)
		self.tunnel.stop()
		
	def initCred(self):
		self.username=pwd.getpwuid(os.getuid()).pw_name.lower()
		tsk=secSbe(TSK)
		self.password=tsk.tac

		
	def login(self):
		super().login(self.username,self.password,domain=self.domain)


		
if __name__ == '__main__':
	"Fonction principale"
	
	client_args = APIClientArgs(server="196.18.48.101")
	
	with APIClientTunnel(client_args) as client:
		client.login()
		# show hosts
		print("Processing. Please wait...")
		show_res = client.api_query("show-packages", "full")
		if show_res.success is False:
			print("Failed to get the list of all host objects:\n{}".format(show_res.error_message))
			exit(1)
			
		ppr(show_res)
		