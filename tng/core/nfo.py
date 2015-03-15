"""
Created on 30.03.2013

@author: ritterph
"""

import cgi
import re, os
import xml.etree.ElementTree as et
import logging

class NFO(object):

    header  = [
                  u'<?xml version="1.0" encoding="utf-8"?>',
                  u'<movie xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
                 ]
    
    footer  = [
                 u'<generated>422344cf76177667d7d3fded1e7538df</generated>',
                 u'<fileinfo />',
                 u'</movie>' 
                 ]

    name = u''
    
        
    def __init__(self,path,content):
        self.path = path
        self.content = content
        self.logger = logging.getLogger('TinyNFOGen')
    
    def GetIMDBID(self):
        self.logger.debug('Searching for IMDB in: %s' % self.path)
        with open(self.path,'r') as nfo:
            content = nfo.readlines()
        IMDBid = re.findall('tt\d{7}',str(content).encode('utf-8'))
        if len(IMDBid) > 0:
            self.logger.debug('Found IMDB in: %s' % self.path)
            return IMDBid[0]
        else:
            return False
    
    def CheckElement(self,key,value):  
        if os.path.isfile(self.path):
            try:
                val = et.parse(self.path)
                val2 = val.find(key)
                if val2 is not None:
                    return val2.text == value
                else:
                    return False
            except:
                self.logger.log(logging.ERROR,'Invalid XML Format: %s' % self.path)
                return False
        else:
            return False
 
    def Write(self,NamingDict):
        self.__NormalizeData()
        with open(self.path,'w') as NFOfile:
            #Write the Header
            for line in self.header:
                NFOfile.write(str(line + '\n'))
            
            #Write the main Content
            for item in NamingDict.keys():
                content = self.content[NamingDict[item]]
                if isinstance(content, unicode):
                    content = cgi.escape(content)
                s = '  <%s>%s</%s>' % (item,content,item)
                NFOfile.write(s.encode('utf-8') + '\n')
            
            #Write the Footer
            for line in self.footer:
                NFOfile.write(str(line + '\n'))

    @staticmethod
    def __multiValueToString(value):
        s=''
        for item in value:
            s += item['name'] + ', '
        return s.rstrip(', ')
    
    def __NormalizeData(self):
        for sub in self.content:
            if isinstance(self.content[sub], list):
                self.content[sub] = self.__multiValueToString(self.content[sub])
