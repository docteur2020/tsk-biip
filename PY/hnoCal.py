#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals

from datetime import datetime , timedelta
import pyparsing as pp
from pprint import pprint as ppr
from pprint import pformat as pprs
import argparse
import pdb
import copy
import yaml
from xlsxToDict import xlsContainer , saveData
from xlsxDictWriter import xlsMatrix
import pickle

DIR_YML='/home/d83071/yaml/hno/'
DIR_EXCEL='/home/d83071/EXCEL/hno/'
DIR_DUMP='/home/d83071/DUMP/hno/'

def loadData(yaml_file):
	data__=None
	with open(yaml_file) as io_yml:
		data__=yaml.load(io_yml,Loader=yaml.SafeLoader)
	return data__

def saveData(data,filename):

	with open(filename,'w') as yml_w:
		yaml.dump(data,yml_w ,default_flow_style=False)
		
class tsChange(object):
	def __init__(self,dateStart: datetime, dateStop:datetime=None, timeStop:str="" ,description:str=""):
	
		self.dateStart=dateStart
		self.dateStop=dateStop
		self.description=description
		
		hour=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=23 and int(tokens[0]) >= 0 )
		minute=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=59 and int(tokens[0]) >= 0 )
		
		hourTime=pp.Combine(hour+pp.CaselessLiteral('H').setParseAction(lambda s,l,t : t[0].lower())+pp.Optional(minute,default='00'))
				
		if not dateStop and not timeStop:
			raise ValueError('tsChange: dateStop or timeStop is mandatory')
			
		if timeStop and dateStop:
			raise ValueError('tsChange: dateStop and timeStop is mutually exclusive')

		if timeStop:
			hourCur=hourTime.parseString(timeStop).asList()[0]
			hourCurTimeObj=datetime.strptime(hourCur,'%Hh%M')
			
			if hourCurTimeObj.hour <= dateStart.hour:
				self.dateStop=copy.deepcopy(dateStart)+timedelta(days=1)
				self.dateStop=self.dateStop.replace(hour=hourCurTimeObj.hour,minute=hourCurTimeObj.minute)
				
			else:
				self.dateStop=copy.deepcopy(dateStart)
				self.dateStop=self.dateStop.replace(hour=hourCurTimeObj.hour,minute=hourCurTimeObj.minute)

		if self.dateStart > self.dateStop:
			raise ValueError('tsChange: dateStop must be greater than dateStart')
			
			
		self.weekdayStart=self.dateStart.weekday()
		self.weekdayStop=self.dateStop.weekday()
		
		if self.weekdayStart >=0 and self.weekdayStart <=4:
			if self.dateStart.hour < 20 and self.dateStart.hour > 6 :
				pdb.set_trace()
				raise ValueError('tsChange: hno in week starts at 20:00')
	
		if self.weekdayStop >=0 and self.weekdayStop <=5:
			if ( (self.dateStop.hour >= 6 and self.dateStop.minute > 0 ) or self.dateStop.hour > 6 ) and self.dateStop.hour <=18:
				pdb.set_trace()
				raise ValueError('tsChange: hno in week ends at 6:00')	
			
			
		self._duration=None
		
	@property
	def duration(self):
		durationObj=self.dateStop-self.dateStart
		duration_in_hour=durationObj.days*24+durationObj.seconds/3600

		if duration_in_hour >=23:
			raise ValueError('tsChange: a change cannot exceed 1 day or 24 hours')
			
		self._duration=duration_in_hour
		return self._duration
		
	@duration.setter
	def duration(self):
		durationObj=self.dateStop-self.dateStart
		duration_in_hour=durationObj.days*24+durationObj.seconds/3600

		if duration_in_hour >=23:
			raise ValueError('tsChange: a change cannot exceed 1 day or 24 hours')
			
		self._duration=duration_in_hour
		
	
	def __str__(self):
		 return pprs(self.__dict__)

	def human_print(self):
		
		if self.weekdayStart==self.weekdayStop:
			str_readable=f' - le {self.dateStart.day}/{self.dateStart.month}/{self.dateStart.year} de {self.dateStart.hour:02d}:{self.dateStart.minute:02d} à {self.dateStop.hour:02d}:{self.dateStop.minute:02d} - {self.description}'
		else:
			str_readable=f' - du {self.dateStart.day}/{self.dateStart.month}/{self.dateStart.year} {self.dateStart.hour:02d}:{self.dateStart.minute:02d} au  {self.dateStop.day}/{self.dateStop.month}/{self.dateStop.year} {self.dateStop.hour:02d}:{self.dateStop.minute:02d} - {self.description}'
		return str_readable
		
	def __repr__(self):
		 return pprs(self.__dict__)
		 
	def split(self):
		result={'100':[],'125-semaine':[],'125-weekend':[],'150':[]}
		
		if self.weekdayStart >=0 and self.weekdayStart <=4:
			if ( self.dateStop.hour ==22 and self.dateStop.minute==0 ) or self.dateStop.hour ==21 or self.dateStop.hour==20:
				result['100'].append(copy.deepcopy(self))
				return result
			
			elif ( self.dateStart.hour ==20 or self.dateStart.hour ==21):
				endCur1=copy.deepcopy(self.dateStart)
				endCur1=endCur1.replace(hour=22,minute=0)
				result['100'].append(tsChange(self.dateStart,endCur1,description=self.description))
				result['125-semaine'].append(tsChange(endCur1,self.dateStop,description=self.description))
			
			else:
				result['125-semaine'].append(copy.deepcopy(self))
		
		if self.weekdayStart==5:
			if self.weekdayStop!=6:
				result['125'].append(copy.deepcopy(self))
			else:
				endCur2=copy.deepcopy(self.dateStop)
				endCur2=endCur2.replace(hour=0,minute=0)
				result['125-weekend'].append(tsChange(self.dateStart,endCur2,description=self.description))
				result['150'].append(tsChange(endCur2,self.dateStop,description=self.description))
	
		if self.weekdayStart==6:
			if self.weekdayStop==6:
				result['150'].append(copy.deepcopy(self))
			else:
				endCur3=copy.deepcopy(self.dateStop)
				endCur3=endCur3.replace(hour=0,minute=0)
				result['150'].append(tsChange(self.dateStart,endCur3))
				result['125-weekend'].append(tsChange(endCur3,self.dateStop))	
			
				
		return result
 

			
class tsChangesCtn(object):
	def __init__(self,excel="",dump=""):
		self.tsChangesObj={}
		
		hour=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=23 and int(tokens[0]) >= 0 )
		minute=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=59 and int(tokens[0]) >= 0 )
		hourTime=pp.Combine(hour+pp.CaselessLiteral('H').setParseAction(lambda s,l,t : t[0].lower())+pp.Optional(minute,default='00'))
		
		if excel:
			dataHnoCtnObj=xlsContainer(args.xlsx)
			dataHnoCtn=dataHnoCtnObj.datas
			for sheet in dataHnoCtn:
				self.tsChangesObj[sheet]=[]
				for entry in dataHnoCtn[sheet]:
					dateCur=entry['date']
					start=entry['start']
					stop=entry['end']
					end=entry['end']
					description=entry['description']
					dateCurObj=copy.deepcopy(dateCur)
					hourCur=hourTime.parseString(start).asList()[0]
					hourCurTimeObj=datetime.strptime(hourCur,'%Hh%M')
					dateCurObj=dateCurObj.replace(hour=hourCurTimeObj.hour,minute=hourCurTimeObj.minute)
					self.tsChangesObj[sheet].append( tsChange(dateCurObj,timeStop=stop,description=description) )
			
		elif dump:
			self.tsChangesObj=self.load(dump)
			
	def calculate(self,tjm=700):
		
		
		self.tsChangeByType={}
		
		for sheet in self.tsChangesObj:
			self.tsChangeByType[sheet]={}
			for entry in self.tsChangesObj[sheet]:
				entrySplittedCur=entry.split()
				for sub_entry in entrySplittedCur:
					if entrySplittedCur[sub_entry]:
						if sub_entry not in self.tsChangeByType[sheet]:
							self.tsChangeByType[sheet][sub_entry] =[]
						for tschCurSplit in entrySplittedCur[sub_entry]:
							self.tsChangeByType[sheet][sub_entry].append(tschCurSplit)
		
							
		ppr(self.tsChangeByType)
		
		print('change by timeslot type:')
		
		self.result={}
		for sheet in self.tsChangeByType:
			self.result[sheet]={}
			for typeCur in self.tsChangeByType[sheet]:
				if typeCur not in self.result[sheet]:
					self.result[sheet][typeCur]= {'change':[],'total':0 }
					
				for entry in self.tsChangeByType[sheet][typeCur]:
					self.result[sheet][typeCur]['change'].append(entry)
					self.result[sheet][typeCur]['total']+=entry.duration
						
		ppr(self.result)
		
		print('total:')
		
		self.total={}
		self.final={}
		for sheet in self.result:
			self.total[sheet]={key: 0 for key in self.result[sheet]}
			self.final[sheet]=0
			for typeCur in self.result[sheet]:
				totalCur=self.result[sheet][typeCur]['total']
				majoration=int(typeCur.split('-')[0])
				self.total[sheet][typeCur]+=tjm*(majoration/100)/8*totalCur
					
				self.final[sheet]+=self.total[sheet][typeCur]
		
		for sheet in self.final:
			print(f'{sheet}:')
			print(f'final:{self.final[sheet]}€')
			
	def extract_resume(self,excel_file):
		excelDict={}
		
		for sheet in self.result:
			totalHour=0
			excelDict[sheet]=[['majoration','nombre','detail','total']]
			for typeCur in self.result[sheet]:
				nombreCur=self.result[sheet][typeCur]['total']
				detail="\n".join( [ element.human_print() for element in self.result[sheet][typeCur]['change'] ])
				totalCur=self.total[sheet][typeCur]
				excelDict[sheet].append([typeCur,str(nombreCur),detail,str(totalCur)])
				totalHour+=nombreCur

			excelDict[sheet].append(['N/A',f'total:{totalHour}','HT',f'{self.final[sheet]}€'])
			TTC=self.final[sheet]*1.2
			excelDict[sheet].append(['N/A',f'total:{totalHour}','TTC',f'{TTC}€'])
		saveXlsxFilename=DIR_EXCEL+excel_file
		print(f'Saving report file{saveXlsxFilename}...')
		xlsMatrix(saveXlsxFilename,excelDict)
			
	
	def save(self,filename):
		saveDumpFilename=DIR_DUMP+filename
		print(f'Saving dump file{saveDumpFilename}...')		
		#saveData(self.tsChangesObj,saveDumpFilename)
		
		with open(saveDumpFilename,'wb') as file__:
			pickle.dump(self.tsChangesObj,file__)
		
	def load(self,filename):
	
		dataCur=None
		with open(filename,'rb') as file__:
			dataCur=pickle.load(file__)
			
		return dataCur		
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-x","--xlsx", action="store",help="excel with hno (not working hours) detail",required=False)
	group1.add_argument("-d","--dump", action="store",help="yaml with hno (not working hours) detail",required=False)
	parser.add_argument("--save",dest='savedump',action="store",help="Save to dump file",required=False)
	parser.add_argument("--extract-to-excel",dest='saveXlsx',action="store",help="Save result to excel file",required=False)
	
	args = parser.parse_args()
	
	if not args.xlsx and not args.dump:
		deb=datetime(2022,2,3,20,0)
		fin=datetime(2022,2,4,6,0)
		
		tsChangeObj=tsChange(deb,fin)
		
		resultSplit=tsChangeObj.split()
		ppr(resultSplit)
		
	if args.xlsx or args.dump:
		
		if args.xlsx:
			HnoObj=tsChangesCtn(excel=args.xlsx)

		if args.dump:
			HnoObj=tsChangesCtn(dump=args.dump)

			
			
			
		
		HnoObj.calculate()
		
		if args.saveXlsx:
			HnoObj.extract_resume(args.saveXlsx)
			
		if args.savedump:
			HnoObj.save(args.savedump)
			
		
	
	
	