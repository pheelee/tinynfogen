'''
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
'''


import os, re
import shutil
from log import TNGLog
from tools import enzyme
from tools.enzyme.exceptions import ParseError
from movie import Movie


class Mover(object):

    _dstFolders = {}
    _IgnoreFolders = ('_','@')
    
    def __init__(self,RootDestination):
        #Root Folder has to Contain Folders like this A-D, E-G etc.
        if self._ContainsGroupFolders(RootDestination) == False:
            self._dstFolders['root'] = RootDestination
        else:
            self._GetDstFolders(RootDestination)

        
        self.log = TNGLog()
        
    def move(self,src,overwrite):
        if self._dstFolders.has_key('root'):
            dst = os.path.join(self._dstFolders['root'],os.path.basename(src))
        else:
            try:
                dst = os.path.join(self._ChooseDestination(src),os.path.basename(src))
            except AttributeError:
                self.log.error('Could not move %s' % os.path.basename(src))
                return False
        
        if os.path.isdir(dst):
            #There exists already a Movie
            #we compare the resolution or size using the metadata of the movie
            compare = Comparer()
            compare.addFile(src)
            compare.addFile(dst)
            if compare.hasResolution() == True:
                if compare.item[src]['resolution'] > compare.item[dst]['resolution']:
                    overwrite = True
                else:
                    overwrite = False
            else:
                if compare.item[src]['size'] > compare.item[dst]['size']:
                    overwrite = True
                else:
                    overwrite = False
                
            if overwrite == True:
                self.log.info('Overwriting existing Movie : %s' % dst)
                shutil.rmtree(dst)
                shutil.move(src, dst)
            elif overwrite == False:
                self.log.warning('Existing Movie has same or better quality, ignoring it : %s' % os.path.basename(dst))
                
        else:
            shutil.move(src, dst)
            self.log.info('Movie moved : %s' % dst)
    
    
    
    def _ContainsGroupFolders(self,path):
        contains = False
        for item in os.listdir(path):
            if not item[0] in self._IgnoreFolders:
                if '-' in item and len(item) == 3:
                    contains= True
                    
        return contains
    
    def _ChooseDestination(self,name):
        if os.path.basename(name).startswith(('The','Der','Die','Das')):
            _letter = os.path.basename(name)[4]
        else:
            _letter = os.path.basename(name)[0]
        
        if self._is_number(_letter):
            _letter = 'A' #For now we put Movies beginning with a Number to Folder A-
	elif _letter.isalnum() == False: #if we have a special char, we search for the first Alphabetic Char
            _letter = self._getFirstAlphaChar(os.path.basename(name))
		
		
        if _letter == False:
            self.log.error('Could not get Start Char for Movie %s' % os.path.basename(name))
            return False
        else:
            for i in self._dstFolders.keys():
                if _letter.upper() in self._dstFolders[i]:
                    return i
            

    def _getFirstAlphaChar(self,string):
        i = 0
        while i < len(string):
            if string[i].isalpha():
                return string[i]
            i += 1
        return False
    

    def _is_number(self,_s):
        try:
            float(_s)
            return True
        except ValueError:
            return False

    def _CalcChars(self,string):
        charset = []
        alpha = ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z')
        firstIndex = alpha.index(string[0])
        lastIndex = alpha.index(string[2]) + 1
        while firstIndex < lastIndex:
            charset.append(alpha[firstIndex])
            firstIndex += 1
            
        return charset
        
    def _GetDstFolders(self,path):
        for item in os.listdir(path):
            p = os.path.join(path,item)
            if os.path.isdir(p) and not item[0] in self._IgnoreFolders:
                #check for valid group folder and create Dictionary
                if re.search('\w{1}-\w{1}',item):
                    self._dstFolders[p] = self._CalcChars(item)

class Comparer(object):
    
    def __init__(self):
        self.log = TNGLog()
        self.item = {}
    
    def addFile(self,path):
        m = Movie(path)
        mfile = os.path.join(path,m._GetMovieFile())
        self.item[path] = {}
        self.item[path]['resolution'] = self._getResolution(mfile)
        self.item[path]['size'] = self._getSize(mfile)
    
    def hasResolution(self):
        for i in self.item.keys():
            if self.item[i]['resolution'] == False:
                return False
        return True
    
    
    def _getResolution(self,path):

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
     
    def _getSize(self,path):
        return os.path.getsize(path)
        
    
