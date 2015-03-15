"""
Created on 30.04.2013

@author: ritterph

Mover Modul for TinyNFOGen

Usage:
mov = Mover(dstFolder)
mov.move(srcFolder)

Example:
mov = Mover(/volume1/video/2_Movies)
mov.move('/volume1/video/_incoming/Sample Movie (2013)')


dstFolder must have the following structure:

   2_Movies
        _incoming
        A-F
        G-H
        I-L
        M-S
        T-Z

Folders starting with _ are ignored
"""

import os
import re
import shutil

from tng.core.log import TNGLog
from libs import enzyme
from libs.enzyme.exceptions import ParseError
from tng.core.movie import Movie


class Mover(object):

    __dstFolders = {}
    __IgnoreFolders = ('_','@')
    dst = u''

    def __init__(self,RootDestination):
        #Root Folder has to Contain Folders like this A-D, E-G etc.
        if self.__ContainsGroupFolders(RootDestination) is False:
            self.__dstFolders['root'] = RootDestination
        else:
            self.__GetDstFolders(RootDestination)

        self.log = TNGLog()
        
    def move(self,src,forceOverwrite):
        if self.__dstFolders.has_key('root'):
            dst = os.path.join(self.__dstFolders['root'],os.path.basename(src))
        else:
            try:
                dst = os.path.join(self.__ChooseDestination(src),os.path.basename(src))
            except AttributeError:
                self.log.error('Could not move %s' % os.path.basename(src))
                return False
        
        if os.path.isdir(dst):
            #There exists already a Movie
            #we compare the resolution or size using the metadata of the movie
            try:
                compare = Comparer(src,dst)
	
                if compare.hasResolution():
                    if compare.item[src]['resolution'] > compare.item[dst]['resolution']:
                        overwrite = True
                    else:
                        overwrite = False
                else:
                    if compare.item[src]['size'] > compare.item[dst]['size']:
                        overwrite = True
                    else:
                        overwrite = False
            except Exception, e:
                overwrite = False
                self.log.error(unicode(e))
                
            if overwrite or forceOverwrite:
                self.log.info('Overwriting existing Movie : %s' % dst)
                shutil.rmtree(dst)
                shutil.move(src, dst)
            else:
                self.log.warning('Existing Movie has same or better quality, ignoring it : %s' % os.path.basename(dst))
                return False
                
        else:
            shutil.move(src, dst)
            self.log.info('Movie moved : %s' % dst)

        self.dst = dst
        return True
    
    
    def __ContainsGroupFolders(self,path):
        contains = False
        for item in os.listdir(path):
            if not item[0] in self.__IgnoreFolders:
                if '-' in item and len(item) == 3:
                    contains= True
                    
        return contains
    
    def __ChooseDestination(self,name):
        if os.path.basename(name).startswith(('The','Der','Die','Das')):
            _letter = os.path.basename(name)[4]
        else:
            _letter = os.path.basename(name)[0]
        
        if self.__is_number(_letter):
            _letter = 'A' #For now we put Movies beginning with a Number to Folder A-
        elif _letter.isalnum() is False: #if we have a special char, we search for the first Alphabetic Char
            _letter = self.__getFirstAlphaChar(os.path.basename(name))
		
		
        if _letter is False:
            self.log.error('Could not get Start Char for Movie %s' % os.path.basename(name))
            return False
        else:
            for i in self.__dstFolders.keys():
                if _letter.upper() in self.__dstFolders[i]:
                    return i
            
    @staticmethod
    def __getFirstAlphaChar(string):
        i = 0
        while i < len(string):
            if string[i].isalpha():
                return string[i]
            i += 1
        return False
    
    @staticmethod
    def __is_number(_s):
        try:
            float(_s)
            return True
        except ValueError:
            return False

    @staticmethod
    def __CalcChars(string):
        charset = []
        alpha = ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z')
        firstIndex = alpha.index(string[0])
        lastIndex = alpha.index(string[2]) + 1
        while firstIndex < lastIndex:
            charset.append(alpha[firstIndex])
            firstIndex += 1
            
        return charset
        
    def __GetDstFolders(self,path):
        for item in os.listdir(path):
            p = os.path.join(path,item)
            if os.path.isdir(p) and not item[0] in self.__IgnoreFolders:
                #check for valid group folder and create Dictionary
                if re.search('\w{1}-\w{1}',item):
                    self.__dstFolders[p] = self.__CalcChars(item)

class Comparer(object):
    
    def __init__(self, path1, path2):
        self.log = TNGLog()
        self.item = {}
        if self.addFile(path1) or self.addFile(path2):
            raise Exception("skipping compare: at least one file is missing")
    
    def addFile(self,path):
        m = Movie(path)
        mcont = m.GetMovieFile()
        if not mcont:
            return False
        mfile = os.path.join(path,mcont)
        self.item[path] = {}
        self.item[path]['resolution'] = self.__getResolution(mfile)
        self.item[path]['size'] = os.path.getsize(path)
        
        return True
    
    def hasResolution(self):
        for i in self.item.keys():
            if self.item[i]['resolution'] is False:
                return False
        return True
    
    
    def __getResolution(self,path):

        self.log.debug('Getting Metadata for: %s' % path)
        try:
            p = enzyme.parse(path)
            height = p.video[0].height
            width = p.video[0].width
            return height * width
        except ParseError:
            self.log.warning('Metadata ParseError: %s' % path)
        except:
            self.log.warning('Metadata fetching failed: %s' % path)
        return False
        
    
