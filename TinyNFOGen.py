#!/usr/bin/python
'''
Created on 02.04.2013

@author: ritterph


TMDB API
---------
Search URL: http://api.themoviedb.org/3/search/movie?api_key=xxx&query=after+the+sunset
Detail URL: http://api.themoviedb.org/3/movie/10589?api_key=xxx&language=de


ToDo:
- Improved Error Handling
- overwrite NFO Parameter

'''
import os,sys,signal


#===========================================================================
# Add Program to PythonPath 
#===========================================================================
PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)
    
#===========================================================================
# Imports
#===========================================================================

import json
import ConfigParser
import logging
from logging import handlers
from argparse import ArgumentParser
from time import mktime,localtime
from classes.movie import Movie,Request
from classes.nfo import NFO
from classes.mover import Mover
from classes.log import TNGLog
from tools.xbmc import XBMCJSON


#===========================================================================
# Paths
#===========================================================================
LogFile = os.path.join(os.getcwd(),'logfiles',os.path.splitext(os.path.basename(__file__))[0]+'.log')
ConfigFile = os.path.join(os.getcwd(),'settings.cfg')

#===========================================================================
# NFO Specs
#===========================================================================



BoxeeBoxDict= {
               'title':'title',
               'rating':'vote_average',
               'year':'release_date',
               'outline':'overview',
               'plot':'overview',
               'runtime':'runtime',
               #'thumb':'poster_path',
               #'mpaa':'',
               'mID':'imdb_id', #imdb ID
               'genre':'genres', #separated by space and comma / CAPITAL LETTERS
               #'director':'',
               }

scriptname = os.path.basename(__file__)

if __name__ == '__main__':
    
    
    #===========================================================================
    # Handle Arguemnts
    #===========================================================================
    parser = ArgumentParser(description='Generate NFO Files')
    parser.add_argument('--src',dest='rootFolder',type=unicode,required=True,help='The root folder where the movies are')
    parser.add_argument('--dst',dest='destFolder',type=unicode,required=False,help='The folder where the movies should be put to after processing')
    parser.add_argument('-f',dest='forceRename',action='store_true',help='Forces Folder and File renaming for all items')
    parser.add_argument('-i',dest='ignoreTNGnfo',action='store_true',help='Ignores an existing TNG NFO and recreates it')
    parser.add_argument('-o',dest='forceOverwrite',action='store_true',help='Forces overwriting of existing movies in destination')
    parser.add_argument('-updateXBMC',dest='forceXBMCUpdate',action='store_true',help='Forces update of XBMC Library (regardless of config setting)')
    parser.add_argument('-v',dest='debugMode',action='store_true',help='Script Output is more verbose')
    parser.add_argument('-n',dest='globalNFOName',type=unicode,required=False,help='Specify a global name for the nfo file')
    parser.add_argument('-l',dest='language',type=unicode,default='de',required=False,help='Language of Movie Infos in ISO 639-1 code Default:German(de)')
    args = parser.parse_args()
    
 
    #===========================================================================
    # Logging
    #===========================================================================
    #Create the wrapper log instance
    log = TNGLog()

    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', '%H:%M:%S')
    
    #Initialize the File Logger
    hdlr = handlers.RotatingFileHandler(os.path.join(LogFile), 'a', 524288, 10)
    hdlr.setLevel(logging.DEBUG)
    #hdlr.setLevel(logging.DEBUG) if args.debugMode == True else hdlr.setLevel(logging.INFO)
    hdlr.setFormatter(formatter)
    log.logger.addHandler(hdlr)
    
    #Initialize the Stdout Logger
    hdlr2 = logging.StreamHandler(sys.stdout)
    hdlr2.setFormatter(formatter)
    hdlr2.setLevel(logging.DEBUG) if args.debugMode == True else hdlr2.setLevel(logging.INFO)
    log.logger.addHandler(hdlr2)
    
    log.logger.setLevel(logging.DEBUG)

    
    
    #===========================================================================
    # Init Classes
    #===========================================================================
    config = ConfigParser.ConfigParser() 
    rootPath = args.rootFolder
    log.info('Source Path: %s' % rootPath)
    if args.destFolder:
        mover = Mover(args.destFolder)
        log.info('Destination Path: %s' % args.destFolder)
    else:
        mover = False
    
    #===========================================================================
    # Read Config Settings
    #===========================================================================
    
    if os.path.isfile(ConfigFile):
        config.read(ConfigFile)
        useProxy = config.get('Network', 'useProxy')
    else:
        log.error('No config file found!!')
        sys.exit(1)
    

    

    
    #===========================================================================
    # Initialisation
    #===========================================================================
    
    start = mktime(localtime())

    log.info('Script started')
    log.debug('Debug Mode On')
    
    if useProxy == 'True':
        log.info('Using Proxy')
        proxy = Request()
        proxy.proxyURL = config.get('Network', 'proxy')
        proxy.InstallProxy()
    
      
        
    #===========================================================================
    # #Add a Signal Handler for Ctrl + C
    #===========================================================================
    def SignalHandler(signal,frame):
        log.error('Script terminated by User')  
        sys.exit(1)
    
    signal.signal(signal.SIGINT, SignalHandler)     
    #===========================================================================
    # Main Program
    #===========================================================================
    for item in os.listdir(rootPath):
        
        #We have to filter out folders beginning with . (Unix hidden dirs) or @ (Synology System Folders) or _ (sabnzbd Operations)
 
        if os.path.isdir(os.path.join(rootPath,item)) and not item.startswith('.') and not item.startswith('@') and not item.startswith('_'):
            
            log.debug("Processing: %s" % item)
            
            #Create the Movie Object
            try:
                movie = Movie(os.path.join(rootPath,item))
            except Exception as e:
                log.error("%s: %s" % (item,e))
                continue

            #Create the Request Object
            movie.Request = Request(config.get('TMDB', 'apikey'))

            movie.GetID()
                
            #If we don't get an ID we pass to next Movie
            if movie.id == False:
                log.warning('No Match found : %s' % (movie.Name + ' ' + movie.Year)) 
                #movie.WriteDebugData()
            else:
                movie.GetDetailedMovieInfos(args.language)
                if movie.infos != False:
                    #If we have the Information we rename the Folder and Files
                    movie.RenameFolder(args.forceRename)
                    movie.RenameFiles(args.forceRename)    

                    if args.globalNFOName:
                        movie.nfoname = args.globalNFOName
                        
                    movie.NFO = NFO(os.path.join(movie.path, movie.nfoname),movie.infos)
                    exists = movie.HasTNGnfo()
                    #Remove unwanted files from directory
                    movie.CleanFiles(('srf','sub','srr','sfv','sft','jpg','tbn','idx','nfo'))
                    log.debug('Cleaned files: %s' % (movie.Name + movie.Year))
                    if  not ((exists == True) and (args.ignoreTNGnfo == False)):
                        #Write new NFO
                        movie.NFO.Write(BoxeeBoxDict)
                        log.info('NFO Generated : %s' % (movie.Name + movie.Year)) 

                    #Get Fanart and Poster
                    movie.GetImages()
                        
                    #Move the Movie
                    if not mover == False:
                        mover.move(movie.path,args.forceOverwrite)
                        
                        
    #===========================================================================
    # Update the XBMC Library
    #===========================================================================
    if config.get('XBMC', 'updateLibrary') == 'True' or args.forceXBMCUpdate == True:
        
        hostname = config.get('XBMC', 'hostname')
        port = config.get('XBMC', 'port')
        username = config.get('XBMC', 'username')
        password = config.get('XBMC', 'password')
        
    
        http_address = 'http://%s:%s/jsonrpc' % (hostname, port)
    
        xbmc = XBMCJSON(http_address,username,password)
        try:
            result = xbmc.VideoLibrary.Scan()
        except:
            result = 'failed'
        log.info('Updating XBMC Library: %s' % result)
    
    #===========================================================================
    # End Secion / Cleanup
    #===========================================================================
    
    end = mktime(localtime())
    log.info('Script Finished!')
    log.info('Script Runtime: %s seconds' % str(end-start))
    logging.shutdown()
        
        
        
        
        