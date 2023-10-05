#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import sys


import ipaddr
import string
import re
from optparse import OptionParser
import os
import os.path
from io import StringIO
import csv
import time
import signal
import socket
import glob
from netmap import netmapEntry
import pickle
import pdb
RESULT="/home/x112097/RESULT/PREFIX"

PREFIX_DUMP_DIR="/home/x112097/DUMP/PREFIX"
class _sbeObject(object):
    def __init__(self,name,objectType):
        super(_sbeObject,self).__init__()
        self.__name=name
        self.__type=objectType
        self.__incomplete=0
        self.__ignored=[]
		
        self.conf=[]

    def addConf(self,conf):
        if isinstance(conf,str):
            conf=[conf]
        self.conf.extend([x.rstrip('\r\n') for x in conf])

    def hasThisConf(self,compiled):
        for line in self.conf:
            if compiled.search(line):
                return True
        return False

    def getConf(self):
        return self.conf

    def getIgnored(self):
        return self.__ignored

    def addIgnored(self,line):
        self.setIncomplete()
        self.__ignored.append(line)

    def setIncomplete(self):
        self.__incomplete=1

    def getName(self):
        return self.__name

    def setName(self,name):
        self.__name=name

    def getType(self):
        return self.__type

    def getDescription(self):
        return self.__description

    def setDescription(self,description):
        self.__description=description

    def getExplodedElements(self):
        return [self]

    def isIncomplete(self):
        return self.__incomplete


class eqPrefixMapping(_sbeObject):
    ''' Map un prefix a des equipements et des NH. En fait, permet de retrouver rapidement des association Prefix ==> Equipement.
    '''
    def __init__(self,vrf,prefix):
        super(eqPrefixMapping,self).__init__(eqPrefixMapping.constructName(vrf,prefix),'eqPrefixMapping')
        self.__map={} # Map dont les cles sont les equipements. Les valeurs etant un NH
        self.__vrf=vrf
        self.__netmap=None
        self.__allNetmaps=[]
        try:
            self.__network=ipaddr.IPv4Network(prefix)
        except:
            raise dmoValueError("/!\\ Erreur dans eqPrefixMapping.__init__: '%s' n'est pas un prefix. /!\\"%prefix)

    def __str__(self):
        return "%s;%s;"%(self.__network,self.__vrf)

    @staticmethod
    def constructName(vrf,prefix):
        return ("%s!%s"%(vrf,prefix))

    @staticmethod
    def iterPrefix(source):
        """ On passe en entree un hash utilisable par getNetmap: permet utilisation dans une boucle for... """
        for tree in source:
            for key in source[tree]:
                for prefix in source[tree][key]:
                    yield prefix


    @staticmethod
    def getNetkeys(netObj):
        prefixLen=netObj._prefixlen
        if prefixLen >= 24:
            netKey=str(ipaddr.IPv4Network('%s/24'%netObj.network).network)
            tree='long'
        elif prefixLen <= 15:
            netKey=str(ipaddr.IPv4Network('%s/0'%netObj.network).network)
            tree='short'
        else:
            netKey=str(ipaddr.IPv4Network('%s/16'%netObj.network).network)
            tree='med'
        return(tree,netKey)

    @staticmethod
    def constructNetmap(source):
        ''' Source: hash ayant pour cle des objets reseaux
            la fonction retourne un hash utilisable avec getNetmap()
        '''
        result={}
        result['short']={}
        result['med']={}
        result['long']={}

        for netObj in source:
            (tree,netKey)=eqPrefixMapping.getNetkeys(netObj)
            try:
                result[tree][netKey].append(netmapEntry(netObj,source[netObj]))
            except:
                result[tree][netKey]=[netmapEntry(netObj,source[netObj])]


        #Maintenant on tri chaque branche pour avoir un bon ordre
        for tree in ['short','med','long']:
            treeHash=result[tree]
            for baseNet in treeHash:
                currentArray=treeHash[baseNet]
                treeHash[baseNet]=sorted(currentArray,reverse=True)

        return result


    def matchEQ(self,eq):
        """ Retourne True si appris sur l'equipement"""
        return eq in self.__map

    def matchNH(self,nh):
        """ Retourne True si le NH apparait """
        return nh in self.__map.values()

    def __getMatch(self,tree,netKey):
        netObj=self.__network
        try:
            netMapEntries=tree[netKey]
        except:
            return (None,'Not Found')
        for netMapEntry in netMapEntries:
            net=netMapEntry.getNetwork()
            if netObj in net:
                if netObj._prefixlen == net._prefixlen:
                    matchType='=='
                elif netObj._prefixlen > net._prefixlen:
                    matchType='<'
                else:
                    raise dmoValueError("_getMatch: reseau inclu dans un autre alors que le mask est plus petit ?????")
                return (matchType,netMapEntry.getValue())
        return(None,'Not Found')


    def __getAllMatches(self,tree,netkey):
        netObj=self.__network
        results=[]
        try:
            netMapEntries=tree[netKey]
        except:
            return (None,'Not Found')
        for netMapEntry in netMapEntries:
            net=netMapEntry.getNetwork()
            if netObj in net:
                if netObj._prefixlen == net._prefixlen:
                    matchType='=='
                elif netObj._prefixlen > net._prefixlen:
                    matchType='<'
                else:
                    raise dmoValueError("_getMatch: reseau inclu dans un autre alors que le mask est plus petit ?????")
                results.append((matchType,netMapEntry.getValue()))
        return(results)

    def getAllNetmaps(self,source,caching=True):
        if caching and self.__allNetmaps:
            return self.__allNetmaps

        netObj=self.__network
        prefixLen=netObj._prefixlen

        (tree,netKey)=eqPrefixMapping.getNetkeys(netObj)

        if tree=='long':
            self.allNetmaps.extend(self.__getMatch(source['long'],netKey))
            (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/16'%netObj.network))
            self.allNetmaps.extend(eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/16'%netObj.network)))
            (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/0'%netObj.network))
            self.allNetmaps.extend(eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/0'%netObj.network)))
        elif tree=='med':
            self.allNetmaps.extend(self.__getMatch(source['med'],netKey))
            (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/8'%netObj.network))
            self.allNetmaps.extend(self.__getMatch(source['short'],netKey))
        elif tree=='short':
            self.allNetmaps.extend(self.__getMatch(source['short'],netKey))
        else:
            raise dmoValueError("/!\\getNetmap : valeur autre que 'long', 'short' ,'med'")
        return self.__netmap

    def getNetmap(self,source,caching=True):
        if caching and self.__netmap:
            return self.__netmap

        netObj=self.__network
        prefixLen=netObj._prefixlen

        (tree,netKey)=eqPrefixMapping.getNetkeys(netObj)

        if tree=='long':
            (matchType,value)=self.__getMatch(source['long'],netKey)
            if matchType == None:
                (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/16'%netObj.network))
                (matchType,value)=self.__getMatch(source['med'],netKey)
                if matchType==None:
                    (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/0'%netObj.network))
                    (matchType,value)=self.__getMatch(source['short'],netKey)
                    self.__netmap=(matchType,value)
                else:
                    self.__netmap=(matchType,value)
            else:
                self.__netmap=(matchType,value)
        elif tree=='med':
            (matchType,value)=self.__getMatch(source['med'],netKey)
            if matchType==None:
                (tree,netKey)=eqPrefixMapping.getNetkeys(ipaddr.IPv4Network('%s/8'%netObj.network))
                (matchType,value)=self.__getMatch(source['short'],netKey)
                self.__netmap=(matchType,value)
            else:
                self.__netmap=(matchType,value)
        elif tree=='short':
            (matchType,value)=self.__getMatch(source['short'],netKey)
            self.__netmap=(matchType,value)
        else:
            raise dmoValueError("/!\\getNetmap : valeur autre que 'long', 'short' ,'med'")
        return self.__netmap

    def addMap(self,eq,cnh):
        (nh,flag)=cnh.split(':')
        if eq in self.__map:
            self.__map[eq].append((nh,list(flag)))
        else:
            self.__map[eq]=[(nh,list(flag))]

    def getPrefix(self):
        return self.__network
    def getVrf(self):
        return self.__vrf
    def getEqList(self):
        return self.__map.keys()

    def getNhHashByEquipment(self,acceptList=None,exceptList=None,iflags=[]):
        '''
        exceptList= List d'adresses IP/rzo dont il ne faut pas tenir compte comme NH valides.
        Retourne un Tuple:
             (hash,multiple)
             hash: cle: Eq. Valeurs: liste de NH
             multiple: True|False. Renvoie True si la liste NH n'est pas  vide pour au moins 2 equipements.
        '''

        aCollapsedList=acceptList
#        if not acceptList:
#            aCollapsedList=None
#        else:
#            try:
#                aCollapsedList=ipaddr.collapse_address_list(acceptList)
#            except:
#                raise dmoValueError("/!\\eqPrefixMapping.getNhHashByEquipment: il ne s'agit pas d'une liste d'objet ipaddr")

        eCollapsedList=exceptList
#        if not exceptList:
#            eCollapsedList=None
#        else:
#            try:
#                eCollapsedList=ipaddr.collapse_address_list(exceptList)
#            except:
#                raise dmoValueError("/!\\eqPrefixMapping.getNhHashByEquipment: il ne s'agit pas d'une liste d'objet ipaddr")

       # print "collapsedList=%s"%collapsedList
        nhHash={}
        multiple=False

        nonNull=0
        for eq in self.__map:
            nhHash[eq]=[]
            #routeObjList=self.__map[eq]
            #for routeObj in routeObjList:
            routeNhList=self.__map[eq]
            for (nh,flags) in routeNhList:

                doNotAppend=False
                alreadyAppended=False

                    #print "flags=%s"%flags
                if not len(flags):
                    print("Pas flags pour Eq= %s /route=%s / nh=%s"%(eq,self.getPrefix(),nh) )
                for flag in flags:
                     #   print "flag=%s nh=%s iflags=%s"%(flag,nh,iflags)
                    if flag in iflags:
                        doNotAppend=True
                            #print "Match"
                        break
                if doNotAppend:
                    #  print "Skipped"
                    continue

                if aCollapsedList:
                    for acceptNh in aCollapsedList:
                        if ipaddr.IPv4Address(nh) in acceptNh:
                            nhHash[eq].append(nh)
                            alreadyAppended=True
                            break

                if alreadyAppended:
                    continue

                if not eCollapsedList:
                    nhHash[eq].append(nh)
                    continue
                for exceptNh in eCollapsedList:
                    if ipaddr.IPv4Address(nh) in exceptNh:
                        doNotAppend=True
                        break
                if not doNotAppend:
                    nhHash[eq].append(nh)

            nhHash[eq]=list(set(nhHash[eq]))
            if len(nhHash[eq]) >0:
                nonNull=nonNull+1

        if nonNull >=2 :
            multiple=True
        routeNhList=None
        return (nhHash,multiple)


class dmoCache(object):
    def __init__(self,srcName,prefix="_",suffix=".db",targetDir=None):
        self.srcName=srcName
        self.timeString=None
        if targetDir:
            baseDir=targetDir
        else:
            baseDir=os.path.dirname(srcName)

        baseName=os.path.basename(srcName)
        targetFile="%s%s"%(prefix,baseName)
        matched=re.match(r'^(.+)(\.[^.]+)$',targetFile)
        if matched:
            targetFile="%s%s"%(matched.group(1),suffix)
        else:
            targetFile="%s%s"%(targetFile,suffix)
        self.target=os.path.join(baseDir,targetFile)

        realSrc=os.path.realpath(srcName)
        if os.path.exists(srcName):
            try:
                timeCreation=os.path.getmtime(realSrc)
                self.timeString=time.strftime("%a, %d %b %Y %H:%M:%S",time.localtime(timeCreation))
            except:
                pass

    def getSrcTime(self):
        return self.timeString

    def isOK(self):
        realSrc=os.path.realpath(self.srcName)
        realDB=os.path.realpath(self.target)

        if not os.path.exists(realSrc) or not os.path.exists(realDB):
            return False

        try:
            realTime=os.path.getmtime(realSrc)
            dbTime=os.path.getmtime(realDB)
        except:
            return False

        if dbTime >= realTime:
            return True

        return False


    def get_pickling_errors(obj,seen=None):
        if seen == None:
            seen=[]
        try:
            state=obj.__getstate__()
        except AttributeError:
            return
        if state==None:
            return
        if isinstance(state,tuple):
            if not isinstance(state[0],dict):
                state=state[1]
            else:
                state=state[0].update(state[1])
        result={}
        for i in state:
            try:
                pickle.dumps(state[i],protocol=2)
            except pickle.PicklingError:
                if not state[i] in seen:
                    seen.append(state[i])
                    result[i]=self.get_pickling_errors(state[i],seen)
        return result

    def load(self):
        try:
            f=open(self.target,'rb')
        except:
            raise dmoValueError("/!\\ Je ne parviens pas a ouvrir le fichier DB '%s' /!\\"%self.target)


        if 'jsonpickle' in sys.modules.keys():
            # On utilise json par defaut sauf si pas present
            try:
                jsonObj=f.read()
                db=jsonpickle.decode(jsonObj)
            except:
                raise sbeValueError("/!\\ Erreur lors du chargement del DB : pas bon format ? /!\\")
        else:
            try:
                db=pickle.load(f)
            except:
                raise sbeValueError ("/!\\ Erreur lors du chargement de la DB : pas bon format ? /!\\")

        f.close()

        return db

    def save(self,value):
        if os.path.exists(self.target):
            try:
                os.remove(self.target)
            except:
                pass
        try:
            f=open(self.target,'wb')
        except:
            raise dmoValueError("/!\\ Impossible de creer le fichier de DB /!\\")

        if 'jsonpickle' in sys.modules.keys():
            try:
                jsonObj=jsonpickle.encode(value)
                f.write(jsonObj)
            except:
                f.close()
                raise
        else:
            try:
                pickle.dump(value,f)
            except:
                f.close()
                #raise dmoValueError("/!\\ Pb lors du dump de la DB /!\\")
                pdb.set_trace()
                raise
        f.close()


def get_last_dump(directory):
	return max(glob.glob(directory+'/*.csv'),key=os.path.getctime)

class sbeValueError(ValueError):
	pass

def getBaseDir():
	return RESULT

def handler(signum, frame):

    sys.stderr.write( '>>  Programme interrompu a la demande de l\'utilisateur  <<')

    os._exit(2)

def printVersion():
    print("0.0.1")
    sys.exit(0)



def getAddresses(source):
    try:
        s=open(source,'r')
    except:
        sys.stderr.write( "/!\\ PB pour ouvrir le fichier 1'%s' /!\\" % source )
        sys.exit(1)
       #raise
  
    aList=[]
    for line in s:
        line=re.sub(r' +','',line)
        if re.match(r'^$',line):
            continue
        line=line.rstrip('\r\n')
        aList.append(line)
    return aList


def sourceFile(source,hashOfNet):

    gTime=[]
    try:
        s=csv.reader(open(source,encoding='utf-8'),delimiter=';')
    except:
        sys.stderr.write( "/!\\ PB pour ouvrir le fichier 2 '%s' /!\\" % source )
        raise
        sys.exit(1)
		
    sys.stderr.write(  "Processing '%s' source File..."%source )

    firstLine=True

    for aLine in s:
        if firstLine:
            firstLine=False       
            reMatched=re.match('#DMO COMPACT NET v1.0 \((.+)\)',aLine[0])
            if not reMatched:
                sys.stderr.write( "/!\\ '%s' n'est pas un fichier genere par 'parseBgpTables.py -c'/!\\"%source )
                sys.exit(1)
            gTime=reMatched.group(1)
            continue

            


        net=aLine[1]
        try:
            netObj=ipaddr.IPv4Network("%s"%net)
        except:
            sys.stderr.write( "Probleme dans le fichier netmap avec l'entree: '%s'. Je continue..."%(net) )
            continue
        vrf=aLine[0]    
        try:
            currentHash=hashOfNet[vrf]
        except:
            hashOfNet[vrf]={}
            currentHash=hashOfNet[vrf]


        value=aLine[1:]
        currentHash[netObj]=value
    return gTime
   

def printSpecific(resultHash):
    
    specific={}
    specific['prefixObj']=None
    specific['vrf']=[]


    for vrf in resultHash:
        prefix=resultHash[vrf][0]
        if not specific['prefixObj']:
            specific['prefixObj']=ipaddr.IPv4Network(prefix)
            specific['vrf']=[vrf]
            continue
        prefixObj=ipaddr.IPv4Network(prefix)
        if prefixObj == specific['prefixObj']:
            specific['vrf'].append(vrf)
        elif prefixObj in specific['prefixObj']:
            specific['prefixObj']=prefixObj
            specific['vrf']=[vrf]
            

    
    
    for vrf in sorted(specific['vrf']):
        print("\n- %s" % vrf )
        value=resultHash[vrf]
         
        prefix=value[0]
        peL=eval(value[2].strip('"'))
        
        print("  - Matching Prefix: %s"%prefix)
        print("  - PEs :  NHs")
        for pe in peL:
            print("    - %s: %s"%(pe,peL[pe]) )
        if len(value)>4:
            print("  - Netmap Infos:")
            print("    %s"%value[4:])



def getNetMatch(listOfAddresses=None,matchString=None,quietString=None,specificString=None,sortedByVrfs=None,options=None):
    for ip in listOfAddresses:
        print("Correspondance pour '%s' %s %s %s dans les VRFs suivantes : " %(ip,matchString,quietString,specificString) )

        resultHash={}


        try:
            targetObj=eqPrefixMapping(None,ip)
        except:
            sys.stderr.write( "Not an IP Address, trying to get IP from hostname..." )
            try:
                address=socket.gethostbyname(ip)
            except socket.error:
                sys.stderr.write("Cannot resolve IP address: '%s'"%ip )
                continue
            sys.stderr.write( 'Name: %s    Resolved IP Address : %s' %(ip,address) )
            ip=address
            targetObj=eqPrefixMapping(None,ip)

        for vrf in sorted(sortedByVrfs):
            if options.vrfs and vrf not in options.vrfs:
                continue
            matchingEntry=targetObj.getNetmap(sortedByVrfs[vrf],caching=False)
            (matchingType,value)=matchingEntry
            if not options.quiet or (matchingType and not options.exactMatch) or (options.exactMatch and matchingType == '=='):
                resultHash[vrf]=None

            else:
                continue
            if not options.quiet and (not matchingType or (options.exactMatch and matchingType!= '==')):
                resultHash[vrf]="    Non Trouve"
                #print "    Non Trouve"
                continue
            
            resultHash[vrf]=value
        

        if not options.specific:
            for vrf in sorted(resultHash):
                print("\n- %s" % vrf )
                value=resultHash[vrf]
                if not isinstance(value,list):
                    print("  - %s"%value)
                    continue
                
                prefix=value[0]
                peL=eval(value[2].strip('"'))
                            
                print("  - Matching Prefix: %s"%prefix)
                print("  - PEs :  NHs")
                for pe in peL:
                    print("    - %s: %s"%(pe,peL[pe]))
                if len(value)>4:
                    print("  - Netmap Infos:")
                    print("    %s"%value[4:])
                print('\n')
        else:
            printSpecific(resultHash)
			
        print("\n\n")
			
    return resultHash

def getNetMatchSilent(listOfAddresses=None,matchString=None,quietString=None,specificString=None,sortedByVrfs=None,options=None,vrfs=[]):
    for ip in listOfAddresses:
        resultHash={}


        try:
            targetObj=eqPrefixMapping(None,ip)
        except:
            sys.stderr.write( "Not an IP Address, trying to get IP from hostname..." )
            try:
                address=socket.gethostbyname(ip)
            except socket.error:
                sys.stderr.write("Cannot resolve IP address: '%s'"%ip )
                continue
            sys.stderr.write( 'Name: %s    Resolved IP Address : %s' %(ip,address) )
            ip=address
            targetObj=eqPrefixMapping(None,ip)
			
        #pdb.set_trace()
		

        for vrf in sorted(sortedByVrfs):
            if options and not vrfs:
                if options.vrfs and vrf not in options.vrfs:
                    continue
                matchingEntry=targetObj.getNetmap(sortedByVrfs[vrf],caching=False)
                (matchingType,value)=matchingEntry
                if not options.quiet or (matchingType and not options.exactMatch) or (options.exactMatch and matchingType == '=='):
                    resultHash[vrf]=None
	
                else:
                    continue
                if not options.quiet and (not matchingType or (options.exactMatch and matchingType!= '==')) :
                    resultHash[vrf]="    Non Trouve"
                    #print "    Non Trouve"
                    continue
                
            elif vrfs:
                if vrf in vrfs:
                   matchingEntry=targetObj.getNetmap(sortedByVrfs[vrf],caching=False)
                   (matchingType,value)=matchingEntry
                   resultHash[vrf]=value

                
    return resultHash
    

def getPrefixesByEq(eq=None,sortedByVrfs=None,options=None):
    for vrf in sorted(sortedByVrfs):
        if options.vrfs and vrf not in options.vrfs:
            continue
        for prefix  in eqPrefixMapping.iterPrefix(sortedByVrfs[vrf]):
            if prefix.matchEQ(eq):
                if  options.short:
                     prefix=str(prefix).split(';')[0]
                print("%s;%s;%s"%(eq,vrf,prefix))
                

def getPrefixesByNH(NH=None,sortedByVrfs=None,options=None):
    for vrf in sorted(sortedByVrfs):
        if options.vrfs and vrf not in options.vrfs:
            continue
        for prefix  in eqPrefixMapping.iterPrefix(sortedByVrfs[vrf]):
            if prefix.matchNH(NH):
                if  options.short:
                    prefix=str(prefix).split(';')[0]

                print("%s;%s;%s"%(NH,vrf,prefix))


def main():
    signal.signal(signal.SIGINT,handler)
    contextFile='.context'

############ BEGIN: VARIABLES MODIFIABLES ################
# prompt : contient une liste de caracteres definissant un prompt
   # prompt=['\r\n\S+#','\r\n\S+\$','\r\n\S+>']
    #ssh_opts="-o StrictHostKeyChecking no"
############ FIN : VARIABLES MODIFIABLES #################

    usage=""" %prog [-i sourceFile] [-v vrf] [-C|-f] {[-Q][-e|-l|-n] {-I File|IP}| -E nom_equipement} 
     Ce script permet de rechercher les entrées correspondant à l'adresse IP. Le fichier source doit être créé à l'aide de 'parseBgpTable.py -c'
       - [options] : '%prog -h' pour les lister
       - IP : adresse IP ou réseau au format CIDR.
"""

    detailedUsage="""

Utilisation:
=============
Ce script permet de traiter les fichiers résultats de "parseBgpTables.py -c ..." et recherche dedans l'entrée qui va bien.


Option '-i sourceFile' :
=====================
 sourceFile doit etre un fichier genere par "parseBgpTables.py -c...". Si '-i' est omis, tente avec un fichier par defaut. 

Option '-v vrf':
==============
 VRF pour lesquels la recherche est effectuee. Peut etre precisee plusieurs fois.

Si cette option est omise. La recherche se fait dans toutes les VRFs.


"""
    defaultSource=get_last_dump(PREFIX_DUMP_DIR)
    parser=OptionParser(usage=usage)
    nThreads=0

    parser.add_option("-d","--directory",action="store",dest="directory",help="Nom du repertoire dans lequel seront placés les fichiers résultats. '%s' par defaut. " % getBaseDir())

    parser.add_option("-i","--input-file",action="store",dest="source",default=None,help="Fichier provenant de parseBgpTables.py -c. Si non precisé, utilise '%s' par defaut." %defaultSource)
    parser.add_option("-v","--vrf",action="append",dest="vrfs",default=[],help="La recherche s'effectuera dans la VRF en question. L'option peut être precisée plusieurs fois. Si omise : recherche dans toutes les VRFs.")
    parser.add_option("-I","--address-file",action="store",dest="addressFile",default=None,help="Fichier contenant une IP/reseau/FQDN/ligne...")
    parser.add_option("-e","--exact-match",action="store_true",dest="exactMatch",default=False,help="Cette option permet de ne renvoyer que les égalites strictes.")
    parser.add_option("-E","--equipment",action="store",dest="equipement",default=None,help="On recherche toutes les routes apprises par un equipement (verbeux)")
    parser.add_option("-n","--next-hop",action="store_true",dest="NH",default=False,help="L'adresse IP represente un NH. On recherche donc tous les prefixes appris depuis un NH.")
    parser.add_option("-s","--short",action="store_true",dest="short",default=False,help="Short output avec option '-n' et '-E'")

    parser.add_option("-Q","--not-quiet",action="store_false",dest="quiet",default=True,help="Cette options permet d'afficher toutes les VRFs même s'il n'y a pas de match.")
    parser.add_option("-l","--longest-match",action="store_true",dest="specific",default=False,help="Cette options permet de n'afficher que les résultats les plus specifiques (longest Match). Ne peut pas être utilisée avec '-Q' ou '-e'.")
    
    parser.add_option("-C","--no-caching",action="store_true",dest="nocaching",default=False,help="Ne cree pas de fichier cache ou l'ignore s'il existe. Ne peut pas etre utilise avec '-C'.")
    parser.add_option("-f","--force-caching",action="store_true",dest="force",default=False,help="Force la creation du fichier DB meme s'il existe et est a jour.")

    parser.add_option("-H","--detailed-help",action="store_true",dest="detailed",default=False,help="Affiche une aide détaillée.")
    parser.add_option("-V","--version",action="store_true",dest="version",default=False,help="Version du package")
    
    
    (options,args)=parser.parse_args()

    

    if options.version:
        printVersion()

    if options.detailed:
        parser.print_usage()
        sys.stderr.write( detailedUsage)
        sys.exit(0)

    if options.specific and (not options.quiet or options.exactMatch):
        sys.stderr.write( "/!\\ L'option '-l' n'est pas utilisable avec '-Q','-e' /!\\" )
        parser.print_usage()
        sys.exit(1)

    if( not options.source):
        options.source=defaultSource

    
    if options.force and options.nocaching:
        sys.stderr.write( "/!\\ Les options '-C' et '-f' ne peuvent etre utilisee en meme temp /!\\" )
        sys.exit(1)

    if options.equipement and (len(args) or options.addressFile):
        sys.stderr.write("/!\\ L'option -E n'est pas utilisable avec une adresse IP et ou un fichier d'adresses. /!\\")
        parser.print_usage()
        sys.exit(1)
        
    if not len(args)==1 and not options.addressFile and not options.equipement:
        sys.stderr.write("/!\\ Il est nécessaire de préciser une IP en argument ou un nom /!\\")
        parser.print_usage()
        sys.exit(1)


    cache=dmoCache(options.source)
    listOfAddresses=[]
    if not options.addressFile and not options.equipement:
        listOfAddresses.append(args[0])
    elif options.addressFile:
        listOfAddresses=getAddresses(options.addressFile)


        
    netByVrfHash={}
    if not cache.isOK() or options.nocaching or options.force:
        gTime=sourceFile(options.source,netByVrfHash)
        sortedByVrfs={}
        sys.stderr.write( "Sorting nets...")
        for vrf in netByVrfHash:
            if options.vrfs and (vrf not in options.vrfs) and options.nocaching:
                continue
            sortedByVrfs[vrf]=eqPrefixMapping.constructNetmap(netByVrfHash[vrf])
        if not options.nocaching:
            sys.stderr.write( "Creation du fichier de cache...")
            try:
                cache.save(sortedByVrfs)
            except sbeValueError as e:
                print >> sys.stderr,e
    else:
        sys.stderr.write("J'ai trouvé un fichier de cache, je l'utilise....")
        try:
            sortedByVrfs=cache.load()
        except sbeValueError as e:
            sys.stderr.write(e)
            print("Je travaille à partir du fichier source...")

            gTime=sourceFile(options.source,netByVrfHash)
            sortedByVrfs={}
            sys.stderr.write("Sorting nets...")
            for vrf in netByVrfHash:
                if options.vrfs and (vrf not in options.vrfs) and options.nocaching:
                    continue
                sortedByVrfs[vrf]=eqPrefixMapping.constructNetmap(netByVrfHash[vrf])
            if not options.nocaching:
                sys.stderr.write( "Creation du fichier de cache...")
                try:
                    cache.save(sortedByVrfs)
                except sbeValueError as e:
                    print >> sys.stderr,e
	
    try:
        if options.specific:
            specificString="(longestMatch)"
        else:
            specificString=""
        if options.quiet:
            quietString="(quiet)"
        else:
            quietString=""
        if options.exactMatch:
            matchString="(exact matching)"
        else:
            matchString="(loose matching)"
        print("\n/!\ Le Fichier utilise date du '%s' /!\\\n"%cache.getSrcTime())
    except AttributeError:
        print('Coucocu')
        pass


    if options.equipement:
        getPrefixesByEq(eq=options.equipement,sortedByVrfs=sortedByVrfs,options=options)
    elif options.NH:
        getPrefixesByNH(NH=args[0],sortedByVrfs=sortedByVrfs,options=options)
    else:
        #getNetMatch(listOfAddresses=listOfAddresses,matchString=matchString,quietString=quietString,specificString=specificString,sortedByVrfs=sortedByVrfs,options=options)
        print(getNetMatchSilent(listOfAddresses=listOfAddresses,matchString=matchString,quietString=quietString,specificString=specificString,sortedByVrfs=sortedByVrfs,options=options,vrfs=options.vrfs))

if __name__ == "__main__":
        main()


