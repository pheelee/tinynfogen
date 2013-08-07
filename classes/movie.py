'''
Created on 29.03.2013

@author: ritterph
'''

import os,pprint, re
from nfo import NFO
import urllib2
import json
from log import TNGLog

class Movie(object):
    

    _FileExts        = ['.mkv','.mp4','.mov','.mpg','.avi','.mpeg']
    _IgnoreFilePrefix= ('.','@')
    
    _banned_words    = [
                       'xvid',
                       'dvdrip',
                       'dvd-rip',
                       'bluray',
                       #'dl',
                       'german',
                       'br-rip',
                       'ac3',
                       '1080p',
                       '720p',
                       '-rwp',
                       'fsk18',
                       '-defused',
                       'defused',
                       'x264',
                       'complete', 
                       'bdrip',
                       'brrip',
                       'internal',
                       '-exps',
                       '-qrc',
                       '-sons',
                       '-ephemerid',
                       '-poe',
                       '-icq4711',
                       '-qom',
                       '-havefun'
                       ]

    def __init__(self,path):

        self.infos = u''
        self.Request = u''
        self.NFO = u''
        self.NFOPaths = []
        self.nfoname = u''
        self.path = path
        self.log = TNGLog()
        self.id = False

        #Extract the Name of the Movie from the Folder
        self.Name = self._GetNamefromFolder(os.path.basename(path))
        self.Year = self._GetYear(os.path.basename(path))
        
        self.multiCDMovie = self._MultiCDMovie()
        
        #Call basic functions for Information Gathering about the movie
        self.NFOPaths = self._GetNFOPaths()
        
        if self.multiCDMovie:
            self.nfoname = 'movie.nfo' #if the movie consists of multiple CDs we simply name the file movie.nfo (suitable for multiple programs like boxee, xbmc etc.)
        else:
            m = self._GetMovieFile()
            if not m:
                raise Exception("No valid movie container found!")
            else:
                self.nfoname = m.replace(os.path.splitext(m)[1],'.nfo')
    
    def GetImages(self):
        if self.infos['poster_path'] is not None:
            self._downloadImage(self.Request.urls['images'] + self.infos['poster_path'],'movie.tbn')
            self._downloadImage(self.Request.urls['images'] + self.infos['poster_path'],'poster.jpg')
            self._downloadImage(self.Request.urls['images'] + self.infos['poster_path'],os.path.basename(self.path)+'.tbn')
        if self.infos['backdrop_path'] is not None:
            self._downloadImage(self.Request.urls['images'] + self.infos['backdrop_path'], 'fanart.jpg')
  
    def GetID(self):
        #First try to get ID from Foldername
        _id = self._GetIDFromFolder()
        if _id == False:
        #Search the NFO Files for ID
            _id = self._SearchIDbyNFO()
        #Query the TMDB
        if _id == False:
            self.Request.SearchMovie(self.Name + ' ' + self.Year)
            if self.Request.searchResult['total_results'] == 0:
                self.log.warning('No Search Results : %s' % (self.Name + ' ' + self.Year))  
                self.id = False
                return False
            elif self.Request.searchResult['total_results'] == 1:
                _id = self.Request.ParseID()
            elif self.Request.searchResult['total_results'] > 1:
                _id = self.SearchIDbyTitle()
            else:
                _id = False
            
        self.id = _id
     
    def GetDetailedMovieInfos(self, language):
        _infos = self.Request.GetMovieDetails(self.id,language)
        if len(_infos) > 0:
            self.infos = json.loads(_infos)
            self.Name = self.infos['title']
            self.Year = '(%s)' % self.infos['release_date'][0:4]
        else:
            self.infos = False
     
    def CleanFiles(self,extensions):
        for i in os.listdir(self.path):
            if os.path.splitext(i)[1].lstrip('.') in extensions:
                os.remove(os.path.join(self.path,i))
    
    def SearchIDbyTitle(self):
        found = False
        for result in self.Request.searchResult['results']:
            if result['original_title'] == self.Name:
                found = result['id']
            elif result['title'] == self.Name:
                found = result['id']
                 
        return found

    def HasTNGnfo(self):
        return self.NFO.CheckElement(u'generated', u'422344cf76177667d7d3fded1e7538df')

    def RenameFolder(self,force):
           
        currentName = (os.path.basename(self.path))
        newName = self.infos['title'] + ' ' + self.Year
        newName = self._MakeSMBfriendly(newName)

        newPath = os.path.join(os.path.abspath(os.path.join(self.path,os.pardir)),newName)
        
        if currentName != newName or force == True:
            #Rename folder and set new path
            try:
                newPath = newPath.encode('utf-8')
                os.rename(self.path, newPath)
            except OSError:
                pass
            #Convert newPath back to unicode and pass to self.path
            self.path = newPath.decode('utf-8')
            self.log.info("Movie renamed: %s" % newName)
            
    def RenameFiles(self,force):       
        if self.multiCDMovie == True:
            return 1
        else:
            for f in os.listdir(self.path):
                if not f.startswith(self._IgnoreFilePrefix):
                    f = self._force_decode(f)
                    fullname = os.path.splitext(os.path.join(self.path,f))
                    currentName =  self._force_decode(os.path.basename(fullname[0]))
                    #currentName = os.path.basename(fullname[0])                

                    newName = self.infos['title'] + ' ' + self.Year
                    
                    if currentName != newName or force == True:
                        newName = os.path.join(self.path,f.replace(currentName,self._MakeSMBfriendly(newName)))

                        try:
                            curPath = os.path.join(self.path,f)
                            os.rename(curPath, newName.encode('utf-8'))
                        except OSError:
                            pass
                        m = self._GetMovieFile()
                        self.nfoname = m.replace(os.path.splitext(m)[1],'.nfo')
                
    def WriteDebugData(self):
        with open(self.path + os.sep +  'debug.log','w') as d:
            pp = pprint.PrettyPrinter(indent=10, stream=d)
            pp.pprint(self.Request.searchResult)
      
    def _GetMovieFile(self):
        for item in os.listdir(self.path):
            if os.path.splitext(item)[1] in self._FileExts:
                return item
         
    def _SearchIDbyNFO(self):
        for item in self.NFOPaths:
            getid = NFO(item,None).GetIMDBID()
            if  getid != False:
                return getid
        return False
      
    def _downloadImage(self,url,filename):
        request = urllib2.Request(url)
        resp = urllib2.urlopen(request)
        data = resp.read()
        f = open(os.path.join(self.path,filename),'wb')
        f.write(data)
        f.close()
        self.log.debug('%s downloaded: %s' % (filename,os.path.basename(self.path)))
    

    
    def _GetYear(self,string):
        pattern = re.compile('(\\(\d{4}\\))')
        m = pattern.search(string)
        if m:
            return m.group(1)
        else:
            return ''
    
    def _GetIDFromFolder(self):
        _IMDBid = re.findall('tt\d{7}',os.path.basename(self.path))
        if len(_IMDBid) > 0:
            return _IMDBid[0]
        else:
            return False
    
    def _GetNamefromFolder(self,string):
        #If we have a trailing ",The" we place it at the Beginning
        if ', The' in string:
            string = 'The %s' % string.replace(', The','')
            
        string = string.strip('[').strip(']')
        string = string.replace('.',' ')
        
        #Filter out the banned scene words
        for item in self._banned_words:
            string = re.sub('('+item+')', '', string,flags=re.IGNORECASE)
            
        #merge multiple blanks into one
        string = re.sub(' +',' ',string)
        #Remove the year from movie title
        string = re.sub('(\\(\d{4}\\))', '', string)
        return string.strip()

    def _GetNFOPaths(self):
        paths = []
        for item in os.listdir(self.path):
            if os.path.splitext(item)[1] == '.nfo':
                nfopath =  self.path + os.sep + item
                paths.append(nfopath)
        return paths

    def _MakeSMBfriendly(self,string):    
        restricted_chars = [ '\\' , '/' , ':' , '*' , '?' , '\"' , '<' , '>' , '|', '\'' ]
        slist = []
        slist += string
        output = u''
        for i in slist:
            if not i in restricted_chars:
                output += i
        return output
     
    def _MultiCDMovie(self):
        multiCD = False
        for item in os.listdir(self.path):
            if os.path.splitext(item)[1] in self._FileExts:
                if 'cd1' in item.lower():
                    multiCD = True
        return multiCD
    
    def _force_decode(self,string, codecs=['utf-8', 'cp1252','ascii','euc_jp']):
        if isinstance(string,str):
            for i in codecs:
                try:
                    return string.decode(i)
                except:
                    pass
        else:
            return string
    
 
class Request():
    
    urls        = {
                   'search':'/3/search/movie?api_key=%s&query=',
                   'detail':'/3/movie/%s?api_key=%s&language=%s',
                   'config':'/3/configuration?api_key=%s'
                   }
    
    headers = {"Accept": "application/json"}
    
    apikey      = ''
    host        = 'http://api.themoviedb.org'
    port        = 80
    proxyURL       = ''

    def __init__(self,apikey):
        self.apikey = apikey
        self.log = TNGLog()
        self.urls['images'] = self._GetImageURL() + 'original'

    def SearchMovie(self,string):
        url = self.host + self.urls['search'] % self.apikey + self._CreateQuery(string)
        request = urllib2.Request(url, headers=self.headers)
        resp = urllib2.urlopen(request)
        data = resp.read()
        self.searchResult = json.loads(data)

    
    def ParseID(self):
        if self.searchResult['total_results'] == 1:
            movieID = self.searchResult['results'][0]['id']
            return movieID
        else:
            return False
            
    
    def InstallProxy(self):
        httpproxy = urllib2.ProxyHandler({'http':self.proxyURL})
        opener = urllib2.build_opener(httpproxy)
        urllib2.install_opener(opener)
    
    def GetMovieDetails(self,movieID,lang):
        data = ''
        url = self.host + self.urls['detail'] % (movieID,self.apikey,lang)
        self.log.debug('Search Request: %s' % url)
        try:
            request = urllib2.Request(url, headers=self.headers)
            resp = urllib2.urlopen(request)
            data = resp.read()
            self.detailResult = data
        except urllib2.HTTPError:
            self.log.error('HTTPError (searchURL): %s' % url)
        finally:   
            if data != '':
                return self.detailResult
            else:
                return ''
       
    def _CreateQuery(self,string):
        return string.replace(' ','+').replace('(','').replace(')','')
    
    def _GetImageURL(self):
        url = self.host + self.urls['config'] % self.apikey
        request = urllib2.Request(url, headers=self.headers)
        resp = urllib2.urlopen(request)
        data = json.loads(resp.read())
        return data['images']['base_url']
    
 
        
            
            
