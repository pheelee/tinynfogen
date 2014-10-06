"""
Created on 29.03.2013

@author: pri@irbe.ch
"""

import os
import re
import shutil
import urllib2
import json
from ConfigParser import ConfigParser

from tng.core.nfo import NFO
from tng.core.log import TNGLog


class Movie(object):
    

    def __init__(self,
                 #Path to the Folder containing the Movie
                 path,
                 #Language for the Movie
                 language='',
                 #ApiKey for TMDB
                 apikey='',
                 ):

        self.files = {}
        self.newFiles = {}
        self.newFiles['video'] = []
        self.newFiles['nfo'] = []
        self.infos = u''
        self.NFO = u''
        self.nfoname = u''
        self.path = path
        self.log = TNGLog()
        self.id = False

        # Read the configuration
        self.config = ConfigParser()
        self.config.read(os.path.join(os.getcwd(), 'settings.cfg'))
        
        try:
            #=======================================================================
            # Get Paths for all Items in current movie
            #=======================================================================
            self.files['video'] = self.__GetFileType(self.path, ('.mkv','.mp4','.mov','.mpg','.avi','.mpeg'),100) #For Movies we want a minimum filesize of 100 MB, otherwise we assume it is a sample
            self.files['nfo'] = self.__GetFileType(self.path, '.nfo')
            self.files['image'] = self.__GetFileType(self.path, ('.jpg','.jpeg','.png','.tbn'))
    
            #=======================================================================
            # Extract the Name of the Movie from the Folder
            #=======================================================================
            self.Name = self.__GetNamefromFolder(os.path.basename(path))
            self.Year = self.__GetYear(os.path.basename(path))
            
            if len(apikey) > 0:
                self.tmdb = tmdb(apikey)
                #=======================================================================
                # Get an IMDB ID
                #=======================================================================
                self.id = self.__GetID()
                
                #===================================================================
                # Get detailed Movie Information and store them in self.infos
                #===================================================================
                self.__GetDetailedMovieInfos(language)

        except Exception:
            raise

    def GetImages(self):
        if self.infos['poster_path'] is not None:
            self.__downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],'movie.tbn')
            self.__downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],'poster.jpg')
            self.__downloadImage(self.tmdb.urls['images'] + self.infos['poster_path'],os.path.basename(self.path)+'.tbn')
        if self.infos['backdrop_path'] is not None:
            self.__downloadImage(self.tmdb.urls['images'] + self.infos['backdrop_path'], 'fanart.jpg')
  
    def GetMovieFile(self):
        files = self.__GetFileType(self.path, ('.mkv','.mp4','.mov','.mpg','.avi','.mpeg'))
        if len(files) == 1:
            return files[0]
        else:
            return False
     
    def clean(self, extensions):
        for i in os.listdir(self.path):
            itempath = os.path.join(self.path, i)
            if os.path.isdir(itempath):
                shutil.rmtree(itempath)
            elif os.path.splitext(i)[1].lstrip('.') in extensions:
                os.remove(itempath)
            #Remove Sample Files
            elif 'sample' in i.lower():
                os.remove(itempath)
    
    def rename(self, force):
        
        self.__rename_folder(force)
        self.__rename_files()
    
    def __SearchIDbyTitle(self):
        found = False
        for result in self.tmdb.searchResult['results']:
            if result['original_title'] == self.Name:
                found = result['id']
            elif result['title'] == self.Name:
                found = result['id']
                 
        return found

    def __rename_folder(self, force):
           
        currentName = (os.path.basename(self.path))
        newName = self.infos['title'] + ' ' + self.Year
        newName = self.__MakeSMBfriendly(newName)

        newPath = os.path.join(os.path.abspath(os.path.join(self.path,os.pardir)),newName)
        
        if currentName != newName or force == True:
            #Rename folder and set new path
            try:
                #ToDo:Check if we have already UTF-8
                newPath = newPath.encode('utf-8')
                os.rename(self.path, newPath)
            except OSError as e:
                raise Exception("cannot rename folder %s:%s" % (newPath,e))
            #Convert newPath back to unicode and pass to self.path
            self.__update_files_path(self.path, newPath.decode('utf-8'))
            self.path = newPath.decode('utf-8')
            self.log.info("Movie renamed: %s" % newName)
    
    def __rename_files(self):

        #=======================================================================
        # Build the new Paths
        #=======================================================================
        
        nameprefix = self.__MakeSMBfriendly(self.infos['title'] + ' ' + self.Year)
        
        if len(self.files['video']) > 1:
            self.newFiles['nfo'].insert(0, os.path.join(self.path, 'movie.nfo'))

            for index, video in enumerate(self.files['video']):

                # Check if we have a naming scheme cd1,cd2 etc.
                if re.search('cd[1-9]', video.lower()):
                    _moviename = nameprefix + ' ' + re.findall('cd[1-9]', video.lower())[0]
                    _extension = os.path.splitext(self.files['video'][index])[1]
                    self.newFiles['video'].insert(index, os.path.join(self.path, _moviename + _extension))

            # Check if the last byte of the filename is an incrementing number
            suffixList = []
            for item in self.files['video']: suffixList.append(os.path.splitext(os.path.basename(item))[0][-1])
            # Compare against number
            try:
                suffixList = [int(i) for i in suffixList]
                if suffixList == range(1, len(self.files['video'])+1):
                    for index, video in enumerate(self.files['video']): self.newFiles['video'].insert(index, os.path.join(self.path, "%s cd%i%s" % (nameprefix, index + 1, os.path.splitext(self.files['video'][index])[1])))

            except ValueError:
                # We have characters
                pass

        elif len(self.files['video']) == 1:
            self.newFiles['nfo'].insert(0, os.path.join(self.path, nameprefix + '.nfo'))
            self.newFiles['video'].insert(0, os.path.join(self.path, nameprefix + os.path.splitext(self.files['video'][0])[1]))
        else:
            self.log.warning("We have no video file for %s" % nameprefix)
            

    
        #=======================================================================
        # Move/Rename the Files
        #=======================================================================
        
        for index, value in enumerate(self.newFiles['video']):
            os.rename(self.files['video'][index], self.newFiles['video'][index].encode('utf-8'))
            self.log.info('renamed video file: %s' % value)
    
  
    def __GetDetailedMovieInfos(self, language):
        _infos = self.tmdb.GetMovieDetails(self.id, language)
        if _infos:
            self.infos = json.loads(_infos)
            self.Name = self.infos['title']
            self.Year = '(%s)' % self.infos['release_date'][0:4]
        else:
            self.infos = False
    
    def __update_files_path(self,old,new):
        for key in self.files.keys():
            for index,value in enumerate(self.files[key]):
                current = self.files[key][index]
                self.files[key][index] = current.replace(old,new)

    @staticmethod
    def __GetFileType(path,fileext,minSize=None):
        rfile = []
        for root,dirs,files in os.walk(path):
            for item in files:
                itempath = os.path.join(root,item)
                if os.path.splitext(item)[1].lower() in fileext:
                    if minSize is not None:
                        if os.path.getsize(itempath) / 1024 / 1024 > minSize:
                            rfile.append(itempath)
                    else:
                        rfile.append(itempath)
        return rfile
         
    def __SearchIDbyNFO(self):
        for item in self.files['nfo']:
            if os.path.isfile(item):
                getid = NFO(item,None).GetIMDBID()
                if  getid:
                    return getid
        return False
      
    def __downloadImage(self, url, filename):
        if not os.path.isfile(os.path.join(self.path, filename)):
            request = urllib2.Request(url)
            resp = urllib2.urlopen(request)
            data = resp.read()
            f = open(os.path.join(self.path, filename),'wb')
            f.write(data)
            f.close()
            self.log.info('%s downloaded: %s' % (filename,os.path.basename(self.path)))
        else:
            self.log.debug('%s exists: %s' % (filename,os.path.basename(self.path)))

    def __GetID(self):
        #First try to get ID from Foldername
        _id = self.__GetIDFromFolder()
        if _id is False:
        #Search the NFO Files for ID
            _id = self.__SearchIDbyNFO()
        #Query the TMDB
        if _id is False:
            #ToDo: Put the whole tmdb search shit into the tmdb object
            self.tmdb.search(self.Name)
            if self.tmdb.searchResult['total_results'] == 0:
                if self.config.get('General', 'interactive') == 'True':
                    _id = self.__GetIDfromUser()
                #raise Exception('No Search Results')
            elif self.tmdb.searchResult['total_results'] == 1:
                _id = self.tmdb.ParseID()
            elif self.tmdb.searchResult['total_results'] > 1:
                _id = self.__SearchIDbyTitle()
            else:
                raise Exception("No Match found")
    
        if _id is False:
            raise Exception("Could not get ID for item %s" % os.path.basename(self.path))
        else:
            return _id

    @staticmethod
    def __GetIDfromUser():
        # Asks the User for IMDB ID
        # return: (string)ID
        #         False
        while True:
            imdbID = raw_input("Enter IMDB ID (tt0208092) or enter to abort:")
            if re.match('tt\d{7}', imdbID):
                return imdbID
            if len(imdbID) == 0:
                return False

    @staticmethod
    def __GetYear(string):
        pattern = re.compile('(\\(\d{4}\\))')
        m = pattern.search(string)
        if m:
            return m.group(1)
        else:
            return ''
    
    def __GetIDFromFolder(self):
        _IMDBid = re.findall('tt\d{7}',os.path.basename(self.path))
        if len(_IMDBid) > 0:
            return _IMDBid[0]
        else:
            return False
    
    def __GetNamefromFolder(self,string):
        #If we have a trailing ",The" we place it at the Beginning
        if ', The' in string:
            string = 'The %s' % string.replace(', The','')
            
                
        #Filter out some common scene words specified by the user
        #Todo: make scene words optional (don't integrate in project)
        scene_words = open('scene_words.txt').read().replace(' ','').strip(os.linesep)
        
        string = self.__sanitizeReleaseName(string, scene_words)
        
        #Remove the year from movie title
        string = re.sub('(\\(\d{4}\\))', '', string)
        string = re.sub('\d{4}','',string)
        return string.strip()

    @staticmethod
    def __sanitizeReleaseName(string,words):
        output = []
        arrMovTitle = string.split('.')
        if len(arrMovTitle) < 4:
            arrMovTitle = string.split(' ')
        for item in arrMovTitle:
            if not item.lower() in words:
                output.append(item)
                    
        return ' '.join(output)
        
    @staticmethod
    def __MakeSMBfriendly(string):
        restricted_chars = [ '\\' , '/' , ':' , '*' , '?' , '\"' , '<' , '>' , '|', '\'' ]
        slist = []
        slist += string
        output = u''
        for i in slist:
            if not i in restricted_chars:
                output += i
        return output
     
    @staticmethod
    def __force_decode(string, codecs=('utf-8', 'cp1252','ascii','euc_jp')):
        if isinstance(string,str):
            for i in codecs:
                try:
                    return string.decode(i)
                #ToDo: Find exceptions
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
            self.urls['images'] = self.__GetImageURL() + 'original'
        except Exception as e:
            self.log.error(unicode(e))
            raise

    def search(self, string):
        self.log.debug('Search String:%s' % string)
        url = self.host + self.urls['search'] % self.apikey + self.__CreateQuery(string)
        self.log.debug('Search URL:%s' % url)
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
    
    def GetMovieDetails(self, movieID, lang):
        data = ''
        url = self.host + self.urls['detail'] % (movieID, self.apikey, lang)
        self.log.debug('Search Request: %s' % url)
        try:
            request = urllib2.Request(url, headers=self.headers)
            resp = urllib2.urlopen(request)
            data = resp.read()
        except urllib2.HTTPError:
            self.log.error('HTTPError (searchURL): %s' % url)
        finally:   
            if data != '':
                return data
            else:
                return False

    @staticmethod
    def __CreateQuery(string):
        return string.replace(' ','+').replace('(','').replace(')','')
    
    def __GetImageURL(self):
        url = self.host + self.urls['config'] % self.apikey
        request = urllib2.Request(url, headers=self.headers)
        resp = urllib2.urlopen(request)
        data = json.loads(resp.read())
        return data['images']['base_url']
    
 
        
            
            
