'''
Created on 29.03.2013

@author: ritterph
'''

import os, re, shutil
from nfo import NFO
import urllib2
import json
from log import TNGLog

class Movie(object):
    

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

    def __init__(self,
                 #Path to the Folder containing the Movie
                 path,
                 #Language for the Movie
                 language = '',
                 #ApiKey for TMDB
                 apikey = '',
                 #Global NFO Name
                 globalNFOName = None
                 ):

        self.files = {}
        self._newFiles = {}
        self._newFiles['video'] = []
        self._newFiles['nfo'] = []
        self.infos = u''
        self.NFO = u''
        self.nfoname = u''
        self.path = path
        self.log = TNGLog()
        self.id = False
        
        try:
            #=======================================================================
            # Get Paths for all Items in current movie
            #=======================================================================
            self.files['video'] = self._GetFileType(self.path, ('.mkv','.mp4','.mov','.mpg','.avi','.mpeg'))
            self.files['nfo'] = self._GetFileType(self.path, '.nfo')
            if globalNFOName is not None:
                self.files['nfo'].append(self.path + os.sep + globalNFOName)
            self.files['image'] = self._GetFileType(self.path, ('.jpg','.jpeg','.png','.tbn'))
    
            #=======================================================================
            # Extract the Name of the Movie from the Folder
            #=======================================================================
            self.Name = self._GetNamefromFolder(os.path.basename(path))
            self.Year = self._GetYear(os.path.basename(path))
            
            if len(apikey) > 0:
                self.tmdb = tmdb(apikey)
                #=======================================================================
                # Get an IMDB ID
                #=======================================================================
                self.id = self._GetID()
                
                #===================================================================
                # Get detailed Movie Information and store them in self.infos
                #===================================================================
                self._GetDetailedMovieInfos(language)

        except Exception as e:
            self.log.error("%s: %s" % (self.Name + ' ' + self.Year,e))
            raise Exception("Failed to create movie object")

    
    def GetImages(self):
        if self.infos['poster_path'] is not None:
            self._downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],'movie.tbn')
            self._downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],'poster.jpg')
            self._downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],os.path.basename(self.path)+'.tbn')
        if self.infos['backdrop_path'] is not None:
            self._downloadImage(self.tmdb.urls['images'] + self.infos['backdrop_path'], 'fanart.jpg')
  

     
    def clean(self,extensions):
        for i in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path,i)):
                shutil.rmtree(os.path.join(self.path,i))
            if os.path.splitext(i)[1].lstrip('.') in extensions:
                os.remove(os.path.join(self.path,i))
    
    def rename(self,force):
        
        self._rename_folder(force)
        self._rename_files(force)
    
    def _SearchIDbyTitle(self):
        found = False
        for result in self.tmdb.searchResult['results']:
            if result['original_title'] == self.Name:
                found = result['id']
            elif result['title'] == self.Name:
                found = result['id']
                 
        return found

    def _rename_folder(self,force):
           
        currentName = (os.path.basename(self.path))
        newName = self.infos['title'] + ' ' + self.Year
        newName = self._MakeSMBfriendly(newName)

        newPath = os.path.join(os.path.abspath(os.path.join(self.path,os.pardir)),newName)
        
        if currentName != newName or force == True:
            #Rename folder and set new path
            try:
                newPath = newPath.encode('utf-8')
                os.rename(self.path, newPath)
            except OSError as e:
                self.log.error(e)
            #Convert newPath back to unicode and pass to self.path
            self._update_files_path(self.path, newPath.decode('utf-8'))
            self.path = newPath.decode('utf-8')
            self.log.info("Movie renamed: %s" % newName)
    
    def _rename_files(self,force):
        
        
        
        #=======================================================================
        # Build the new Paths
        #=======================================================================
        
        nameprefix = self._MakeSMBfriendly(self.infos['title'] + ' ' + self.Year)
        
        if len(self.files['video']) > 1:
            self._newFiles['nfo'].insert(0,os.path.join(self.path,'movie.nfo'))
            for index,video in enumerate(self.files['video']):
                if re.search('cd[1-9]', video.lower()):
                    
                    _moviename = nameprefix + ' ' + re.findall('cd[1-9]',video.lower())[0]
                    _extension = os.path.splitext(self.files['video'][index])[1]
                    self._newFiles['video'].insert(index,os.path.join(self.path,_moviename +_extension))
        else:
            self._newFiles['nfo'].insert(0,os.path.join(self.path,nameprefix + '.nfo'))
            self._newFiles['video'].insert(0,os.path.join(self.path,nameprefix + os.path.splitext(self.files['video'][0])[1]))
            

    
        #=======================================================================
        # Move/Rename the Files
        #=======================================================================
        
        for index,value in enumerate(self._newFiles['video']):
            os.rename(self.files['video'][index], self._newFiles['video'][index].encode('utf-8'))
            self.log.info('moved: %s' % value)
    
  
    def _GetDetailedMovieInfos(self, language):
        _infos = self.tmdb.GetMovieDetails(self.id,language)
        if len(_infos) > 0:
            self.infos = json.loads(_infos)
            self.Name = self.infos['title']
            self.Year = '(%s)' % self.infos['release_date'][0:4]
        else:
            self.infos = False
    
    def _update_files_path(self,old,new):
        for key in self.files.keys():
            for index,value in enumerate(self.files[key]):
                current = self.files[key][index]
                self.files[key][index] = current.replace(old,new)
    
    def _GetFileType(self,path,fileext):
        rfile = []
        for root,dirs,files in os.walk(path):
            for item in files:
                if os.path.splitext(item)[1] in fileext:
                    rfile.append(os.path.join(root,item))
        return rfile
         
    def _SearchIDbyNFO(self):
        for item in self.files['nfo']:
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
    
    def _GetID(self):
        #First try to get ID from Foldername
        _id = self._GetIDFromFolder()
        if _id == False:
        #Search the NFO Files for ID
            _id = self._SearchIDbyNFO()
        #Query the TMDB
        if _id == False:
            self.tmdb.SearchMovie(self.Name + ' ' + self.Year)
            if self.tmdb.searchResult['total_results'] == 0:
                raise Exception('No Search Results')  
            elif self.tmdb.searchResult['total_results'] == 1:
                _id = self.tmdb.ParseID()
            elif self.tmdb.searchResult['total_results'] > 1:
                _id = self._SearchIDbyTitle()
            else:
                raise Exception("No Match found")
    
        if _id == False:
            raise Exception("Could not get ID")
        else:
            return _id
    
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


    def _MakeSMBfriendly(self,string):    
        restricted_chars = [ '\\' , '/' , ':' , '*' , '?' , '\"' , '<' , '>' , '|', '\'' ]
        slist = []
        slist += string
        output = u''
        for i in slist:
            if not i in restricted_chars:
                output += i
        return output
     
    
    def _force_decode(self,string, codecs=['utf-8', 'cp1252','ascii','euc_jp']):
        if isinstance(string,str):
            for i in codecs:
                try:
                    return string.decode(i)
                except:
                    pass
        else:
            return string
    
 
class tmdb():
    
    urls        = {
                   'search':'/3/search/movie?api_key=%s&query=',
                   'detail':'/3/movie/%s?api_key=%s&language=%s',
                   'config':'/3/configuration?api_key=%s'
                   }
    
    headers = {"Accept": "application/json"}
    
    apikey      = ''
    host        = 'http://api.themoviedb.org'
    port        = 80
    
    def __init__(self,apikey):
        try:
            self.apikey = apikey
            self.log = TNGLog()
            self.urls['images'] = self._GetImageURL() + 'original'
        except Exception as e:
            self.log.error(unicode(e))
            raise

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
    
 
        
            
            
