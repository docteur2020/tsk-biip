#!/usr/bin/env python3.7
# coding: utf-8

import sys
import ipaddr
import string, re, csv
__version__ = '0.2'
__all__ = ['netmapFile', 'netmapEntry']

import argparse
import glob
import os
import logging

NETMAP_DIR="/home/x112097/NETMAP"

class sbeValueError(ValueError):
	pass

class netmapFile(object):
    u"""
     netmapFile: Permet de chercher dans un fichier de type netmap une correspondance.
     format du fichier :
     subnet_id;base_network_address;network_bits;provider;customer;responsible;building_floor;comments;subnet_name
    
    __init__(self,filename): 
       filename: nom du fichier netmap au format ci-dessus
       Tente d'ouvir le fichier. En cas d'échec, envoie une exception de type sbeValueError. 
    """
    __module__ = __name__

    def __init__(self, source , logger):
        try:
            f = open(source)
        except:
            self.logger.error("/!\\ PB pour ouvrir le fichier netmap '%s' /!\\" % source)
            sys.exit(1)
        self.logger=logger
        self.__f = f
        self.__hashOfNet = {}
        self.result = {}
        self.result['short'] = {}
        self.result['med'] = {}
        self.result['long'] = {}

    def parse(self):
        hashOfNet = self.__hashOfNet
        s = csv.reader(self.__f, delimiter=';', quotechar='"')
        for aLine in s:
            if len(aLine) < 9:
                self.logger.error("Skip Line : '%s'... Pas assez de champs..." % aLine)
                continue
            netid = aLine[0]
            base = aLine[1]
            bits = aLine[2]
            provider = aLine[3]
            customer = aLine[4]
            responsible = aLine[5]
            building = aLine[6]
            comments = aLine[7]
            subnetName = aLine[8]
            try:
                netObj = ipaddr.IPv4Network('%s/%s' % (base, bits))
            except:
                self.logger.error("Probleme dans le fichier netmap avec l'entree: '%s/%s'. Je continue..." % (base, bits) )
                continue
            else:
                if netObj in hashOfNet:
                    arrayCopy = hashOfNet[netObj][:]
                    duplicateString = arrayCopy[3] + '%s,' % netid
                    value = arrayCopy[4]
                    netid = arrayCopy[0]
                    network = arrayCopy[1]
                    try:
                        hashOfNet[netObj] = [
                         netid, network, True, duplicateString, value]
                    except:
                        print(aLine)
                        raise
                    else:
                        continue
                value = '%s;%s;%s;%s;%s;%s' % (provider, customer, responsible, subnetName, building, comments)
                hashOfNet[netObj] = [netid, '%s' % netObj, False, '', value]

        self.__netmapHash = self.__constructNetmap(hashOfNet)

    def __getNetkeys(self, netObj):
        prefixLen = netObj._prefixlen
        if prefixLen >= 24:
            netKey = str(ipaddr.IPv4Network('%s/24' % netObj.network).network)
            tree = 'long'
        else:
            if prefixLen <= 15:
                netKey = str(ipaddr.IPv4Network('%s/0' % netObj.network).network)
                tree = 'short'
            else:
                netKey = str(ipaddr.IPv4Network('%s/16' % netObj.network).network)
                tree = 'med'
        return (tree, netKey)

    def __constructNetmap(self, source):
        """ Source: hash ayant pour cle des objets reseaux
            la fonction retourne un hash utilisable avec getNetmap()
        """
        result = self.result
        for netObj in source:
            tree, netKey = self.__getNetkeys(netObj)
            try:
                result[tree][netKey].append(netmapEntry(netObj, source[netObj]))
            except:
                result[tree][netKey] = [
                 netmapEntry(netObj, source[netObj])]

        for tree in ['short', 'med', 'long']:
            treeHash = result[tree]
            for baseNet in treeHash:
                currentArray = treeHash[baseNet]
                treeHash[baseNet] = sorted(currentArray, reverse=True)

        return result

    def getAllNetmaps(self, address):
        try:
            netObj = ipaddr.IPv4Network(address)
        except:
            raise sbeValueError("/!\\ '%s' n'est pas une adresse réseau IPv4 /!\\" % s)
        else:
            source = self.__netmapHash
            prefixLen = netObj._prefixlen
            result = None
            allNetmaps = []
            tree, netKey = self.__getNetkeys(netObj)
            if tree == 'long':
                allNetmaps.extend(self.__getAllMatches(source['long'], netKey, netObj))
                tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/16' % netObj.network))
                allNetmaps.extend(self.__getAllMatches(source['med'], netKey, netObj))
                tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/8' % netObj.network))
                allNetmaps.extend(self.__getAllMatches(source['short'], netKey, netObj))
            else:
                if tree == 'med':
                    allNetmaps.extend(self.__getAllMatches(source['med'], netKey, netObj))
                    tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/8' % netObj.network))
                    allNetmaps.extend(self.__getAllMatches(source['short'], netKey, netObj))
                else:
                    if tree == 'short':
                        allNetmaps.extend(self.__getAllMatches(source['short'], netKey, netObj))
                    raise sbeValueError("/!\\getNetmap : valeur autre que 'long', 'short' ,'med'")

        return allNetmaps

    def getNetmapEnclosed(self, address):
        try:
            netObj = ipaddr.IPv4Network(address)
        except:
            raise sbeValueError("/!\\ '%s' n'est pas une adresse réseau IPv4 /!\\" % s)
        else:
            source = self.__netmapHash
            prefixLen = netObj._prefixlen
            result = None
            allNetmaps = []
            tree, netKey = self.__getNetkeys(netObj)
            if tree == 'short':
                allNetmaps.extend(self.__getAllEnclosed(source['long'], netObj))
                allNetmaps.extend(self.__getAllEnclosed(source['med'], netObj))
                allNetmaps.extend(self.__getAllEnclosed(source['short'], netObj))
            else:
                if tree == 'med':
                    allNetmaps.extend(self.__getAllEnclosed(source['med'], netObj))
                    allNetmaps.extend(self.__getAllEnclosed(source['long'], netObj))
                else:
                    if tree == 'long':
                        allNetmaps.extend(self.__getAllEnclosed(source['long'], netObj))
                    raise sbeValueError("/!\\getNetmap : valeur autre que 'long', 'short' ,'med'")

        return allNetmaps

    def getNetmap(self, address):
        try:
            netObj = ipaddr.IPv4Network(address)
        except:
            raise sbeValueError("/!\\ '%s' n'est pas une adresse réseau IPv4 /!\\" % s)
        else:
            source = self.__netmapHash
            prefixLen = netObj._prefixlen
            result = None
            tree, netKey = self.__getNetkeys(netObj)
            if tree == 'long':
                matchType, value = self.__getMatch(source['long'], netKey, netObj)
                if matchType == None:
                    tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/16' % netObj.network))
                    matchType, value = self.__getMatch(source['med'], netKey, netObj)
                    if matchType == None:
                        tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/8' % netObj.network))
                        matchType, value = self.__getMatch(source['short'], netKey, netObj)
                        return (
                         matchType, value)
                    else:
                        return (
                         matchType, value)
                else:
                    return (
                     matchType, value)
            else:
                if tree == 'med':
                    matchType, value = self.__getMatch(source['med'], netKey, netObj)
                    if matchType == None:
                        tree, netKey = self.__getNetkeys(ipaddr.IPv4Network('%s/8' % netObj.network))
                        matchType, value = self.__getMatch(source['short'], netKey, netObj)
                        return (
                         matchType, value)
                    else:
                        return (
                         matchType, value)
                else:
                    if tree == 'short':
                        matchType, value = self.__getMatch(source['short'], netKey, netObj)
                        return (
                         matchType, value)
                    raise sbeValueError("/!\\getNetmap : valeur autre que 'long', 'short' ,'med'")

        return

    def __getMatch(self, tree, netKey, netObj):
        try:
            netMapEntries = tree[netKey]
        except:
            return (None, 'Not Found')
        else:
            for netMapEntry in netMapEntries:
                net = netMapEntry.getNetwork()
                if netObj in net:
                    if netObj._prefixlen == net._prefixlen:
                        matchType = '=='
                    else:
                        if netObj._prefixlen > net._prefixlen:
                            matchType = '<'
                        else:
                            raise sbeValueError('_getMatch: reseau inclu dans un autre alors que le mask est plus petit ?????')
                    return (
                     matchType, netMapEntry.getValue())

        return (None, 'Not Found')

    def __getAllMatches(self, tree, netKey, netObj):
        results = []
        try:
            netMapEntries = tree[netKey]
        except:
            return []
        else:
            for netMapEntry in netMapEntries:
                net = netMapEntry.getNetwork()
                if netObj in net:
                    if netObj._prefixlen == net._prefixlen:
                        matchType = '=='
                    else:
                        if netObj._prefixlen > net._prefixlen:
                            matchType = '>'
                        else:
                            raise sbeValueError('_getMatch: reseau inclu dans un autre alors que le mask est plus petit ?????')
                    results.append((matchType, netMapEntry.getValue()))

        return results

    def __getAllEnclosed(self, tree, netObj):
        results = []
        try:
            tree
        except:
            return []
        else:
            for netKey in tree:
                netmapEntries = tree[netKey]
                for netMapEntry in netmapEntries:
                    net = netMapEntry.getNetwork()
                    if net in netObj:
                        if netObj._prefixlen == net._prefixlen:
                            matchType = '=='
                        else:
                            if netObj._prefixlen < net._prefixlen:
                                matchType = '<'
                            else:
                                raise sbeValueError('_getMatch: reseau inclu dans un autre alors que le mask est plus petit ?????')
                        results.append((matchType, netMapEntry.getValue()))

        return results


class netmapEntry(object):
    __module__ = __name__

    def __init__(self, ipv4Obj, value):
        self.__net = ipv4Obj
        self.__value = value

    def getValue(self):
        return self.__value

    def getNetwork(self):
        return self.__net

    def __lt__(self, other):
        return self.getNetwork() < other.getNetwork()

    def __gt__(self, other):
        return self.getNetwork() > other.getNetwork()

    def __eq__(self, other):
        return self.getNetwork() == other.getNetwork()

    def __str__(self):
        return "%s: '%s'" % (self.getNetwork(), self.getValue())
	

def get_last_dump(directory):
	return max(glob.glob(directory+'/*'),key=os.path.getctime)	
		
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-n", "--network",action="store",help="Fichier pour lequel on cherche les informations netmap",required=True)
	parser.add_argument("-r", "--repertoire",action="store",default=NETMAP_DIR,help="repertoire contenant les dump de netmap",required=False)
	parser.add_argument("-V", "--Verbose",action="count",help="mode debug",required=False)
	args = parser.parse_args()
	
	logger = logging.getLogger('Logger Netmap')
	customHandler = logging.StreamHandler()
	
	if args.Verbose:
		if args.Verbose >= 2:
			logger.setLevel(logging.DEBUG)
			print("LOGGING LEVEL DEBUG")
		elif  args.Verbose >= 1:
			logger.setLevel(logging.INFO)
			print("LOGGING LEVEL INFO")
	else:
		logger.setLevel(logging.CRITICAL)
		
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	customHandler.setFormatter(formatter)
	logger.addHandler(customHandler)
	
	DUMP_NETMAP=get_last_dump(args.repertoire)
	logger.info("DUMP NETMAP:"+DUMP_NETMAP)
	
	results=[]
	
	if(args.network):
		netmapObj=netmapFile(DUMP_NETMAP,logger)
		netmapObj.parse()
		logger.info("OBJET NETMAP INSTANCE:"+str(netmapObj))
		logger.debug("Recherche NETMAP")
		results.append(netmapObj.getNetmap(args.network))
		
		print(results)
		

