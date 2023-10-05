#!/bin/python3.8
# coding: utf-8

import time
import pyparsing as pp
#from sshtunnel import SSHTunnelForwarder
#from sshtunnel import HandlerSSHTunnelForwarderError
import logging
import argparse
import time
import pdb
import logging
import logging.handlers



PAER="192.64.10.129"
LOCALHOST="127.0.0.1"
REMOTE_USER = 'x112097'
REMOTE_HOST =  PAER
REMOTE_PORT = 22
LOCAL_HOST =  LOCALHOST
FIRST_LOCAL_PORT = 7000
KEY='/home/x112097/.ssh/id_rsa'
HOSTFILE='/home/x112097/HOSTS/hosts'
LOGFILE='TMP/Tunnelier/log'

class MaxTunnelError(Exception):
	"Classe Exception pour grep-ip"
	
	def __init__(self,code=0,value="None"):
		self.message=u'Unknown Error'
		
		if code==1 :
			self.message=u'Max value threshold:'+value
			
		super(MaxTunnelError, self).__init__(self.message)
		

def parseUrl(url__):

	Result=None
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	name=pp.Word(pp.alphanums+'.')
	http=pp.CaselessLiteral('http').setParseAction(lambda s,l,t : t[0].lower())
	https=pp.CaselessLiteral('https').setParseAction(lambda s,l,t : t[0].lower())
	ftp=pp.CaselessLiteral('ftp').setParseAction(lambda s,l,t : t[0].lower())
	ftps=pp.CaselessLiteral('ftps').setParseAction(lambda s,l,t : t[0].lower())
	path=pp.Combine(pp.Literal('/')+pp.Word(pp.alphanums+'_-/'))
	port=pp.Combine(pp.Suppress(pp.Literal(':'))+pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <65536 and int(tokens[0]) >= 0 ))
	url_http=http.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='80').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_https=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='443').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_ftp=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='21').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_ftps=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='22').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	
	url=pp.MatchFirst([url_https,url_http,url_ftps,url_ftp])
	
	Result=url.parseString(url__).asDict()
	
	return Result
	
class Tunnelier(object):
	def __init__(self,user=REMOTE_USER,password="",rebond=PAER,port=REMOTE_PORT,local_port=FIRST_LOCAL_PORT,key=KEY):
		self.Url={}
		self.usedPort={}
		self.currentLocalPort=local_port
		self.maxPort=local_port+100
		self.tunnels={}
		self.rebond=rebond
		self.user=user
		self.password=password
		self.key=key
		self.logger = logging.getLogger("")
		self.logger.setLevel(logging.DEBUG)
		handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)
		
	def addUrl(self,url):
		urlParsed=parseUrl(url)
		while True:
			try:
				self.tunnels[url]=SSHTunnelForwarder(
									(self.rebond, 22),
									ssh_username=self.user,
									ssh_pkey=self.key,
									remote_bind_address=(urlParsed['ip'], int(urlParsed['port'])),
									local_bind_address=( LOCALHOST, self.currentLocalPort),
									mute_exceptions=False,logger=self.logger)
						
				self.tunnels[url].daemon_forward_servers=True
				self.tunnels[url].start()

				self.setMessageTunnelCur(url,urlParsed['protocol'])
				self.printMessageTunnelCur()
				#pdb.set_trace()
				if not urlParsed['path']:
					new_url=urlParsed['protocol']+'://'+LOCALHOST+':'+str(self.currentLocalPort)
				else:
					new_url=urlParsed['protocol']+'://'+LOCALHOST+':'+str(self.currentLocalPort)+urlParsed['path']
				
				self.incrPort()
				
				break
				
				
		
			
			except HandlerSSHTunnelForwarderError as e:
				print(str(self.currentLocalPort)+" used")
				self.tunnels[url].stop()
				self.incrPort()
				
		return new_url
			
	def incrPort(self):
		self.currentLocalPort+=1
		if self.currentLocalPort>self.maxPort:
			raise MaxTunnelError(code=1,value=str(self.maxPort))
			
		
	def stop(self):
		for tunnel__ in self.tunnels.values():
			self.CurrentMessage='Closing tunnel for '+str(tunnel__.tunnel_bindings)
			self.printMessageTunnelCur()
			tunnel__.stop()
			


			
	def setMessageTunnelCur(self,url,proto):
		self.CurrentMessage='Running tunnel for '+url+"=>"+proto+'://'+LOCALHOST+':'+str(self.currentLocalPort)
		
	def getMessageTunnelCur(self):
		return self.CurrentMessage
		
	def printMessageTunnelCur(self):
		print(self.CurrentMessage)
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--url",  action="append",help="url",required=True)
	args = parser.parse_args()
	
	T=Tunnelier()
	for url in args.url:
		T.addUrl(url)
		T.printMessageTunnelCur()
		
	try:
		while True:
			print('Tunnelier running...')
			time.sleep(5)


	except KeyboardInterrupt:
		print('Closing...')
		T.stop()
	
		

		