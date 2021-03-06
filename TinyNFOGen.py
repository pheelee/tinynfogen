#!/usr/bin/python
"""
Created on 02.04.2013

@author: ritterph


TMDB API
---------
Search URL: http://api.themoviedb.org/3/search/movie?api_key=xxx&query=after+the+sunset
Detail URL: http://api.themoviedb.org/3/movie/10589?api_key=xxx&language=de



"""
import os
import sys
import signal


# ===========================================================================
# Add Program to PythonPath 
#===========================================================================
PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)

#===========================================================================
# Imports
#===========================================================================

import ConfigParser
import logging
import urllib2
from logging import handlers
from argparse import ArgumentParser
from time import mktime, localtime
from tng.core.movie import Movie
from tng.core.nfo import NFO
from tng.core.mover import Mover
from tng.core.log import TNGLog
from tng.core.installer import Config, Updater
from libs.xbmc import XbmcJson
from libs.crypt_s import Crypt


#===========================================================================
# Paths
#===========================================================================
LogFile = os.path.join(os.path.dirname(__file__), 'logfiles', os.path.splitext(os.path.basename(__file__))[0] + '.log')
ConfigFile = os.path.join(os.path.dirname(__file__), 'settings.cfg')

#===========================================================================
# NFO Specs
#===========================================================================

BoxeeBoxDict = {
    'title': 'title',
    'rating': 'vote_average',
    'year': 'release_date',
    'outline': 'overview',
    'plot': 'overview',
    'runtime': 'runtime',
    #'thumb':'poster_path',
    #'mpaa':'',
    'mID': 'imdb_id',  # imdb ID
    'genre': 'genres',  # separated by space and comma / CAPITAL LETTERS
    #'director':'',
}

scriptname = os.path.basename(__file__)

if __name__ == '__main__':

    #===========================================================================
    # Handle Arguments
    #===========================================================================
    parser = ArgumentParser(description='Generate NFO Files')
    parser.add_argument('--src', dest='rootFolder', type=unicode, required=True,
                        help='The root folder where the movies are')
    parser.add_argument('--dst', dest='destFolder', type=unicode, required=False,
                        help='The folder where the movies should be put to after processing')
    parser.add_argument('--create-config', dest='createConfig', action='store_true', help='Create a new config file')
    parser.add_argument('-f', dest='forceRename', action='store_true',
                        help='Forces Folder and File renaming for all items')
    parser.add_argument('-o', dest='forceOverwrite', action='store_true',
                        help='Forces overwriting of existing movies in destination')
    parser.add_argument('-updateXBMC', dest='forceXBMCUpdate', action='store_true',
                        help='Forces update of XBMC Library (regardless of config setting)')
    parser.add_argument('-v', dest='debugMode', action='store_true', help='Script Output is more verbose')
    parser.add_argument('-n', dest='globalNFOName', type=unicode, required=False,
                        help='Specify a global name for the nfo file')
    parser.add_argument('-l', dest='language', type=unicode, default='de', required=False,
                        help='Language of Movie Infos in ISO 639-1 code Default:German(de)')
    args = parser.parse_args()

    #===========================================================================
    # Logging
    #===========================================================================

    logpath = os.path.abspath(os.path.join(LogFile, os.pardir))
    if not os.path.isdir(logpath):
        os.mkdir(logpath)
    #Create the wrapper log instance
    log = TNGLog()

    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', '%d-%m-%Y %H:%M:%S')

    #Initialize the File Logger
    hdlr = handlers.RotatingFileHandler(os.path.join(LogFile), 'a', 524288, 10)
    hdlr.setLevel(logging.DEBUG)
    #hdlr.setLevel(logging.DEBUG) if args.debugMode == True else hdlr.setLevel(logging.INFO)
    hdlr.setFormatter(formatter)
    log.logger.addHandler(hdlr)

    #Initialize the Stdout Logger
    hdlr2 = logging.StreamHandler(sys.stdout)
    hdlr2.setFormatter(formatter)
    hdlr2.setLevel(logging.DEBUG) if args.debugMode is True else hdlr2.setLevel(logging.INFO)
    log.logger.addHandler(hdlr2)

    log.logger.setLevel(logging.DEBUG)

    #===========================================================================
    # Read Config Settings
    #===========================================================================

    myconf = Config(ConfigFile)

    if myconf.available() is False or args.createConfig:
        myconf.create()

    config = ConfigParser.ConfigParser()
    config.read(ConfigFile)

    #===========================================================================
    # Init Classes
    #===========================================================================
    mycrypt = Crypt(__file__)
    rootPath = args.rootFolder
    log.info('Source Path: %s' % rootPath)
    mover = None
    if args.destFolder:
        mover = Mover(args.destFolder)
        log.info('Destination Path: %s' % args.destFolder)

    #===========================================================================
    # Initialisation
    #===========================================================================

    start = mktime(localtime())

    log.info('Script started')
    log.debug('Debug Mode On')

    if config.get("Network", "useProxy") == 'True':
        log.info('Using Proxy')
        httpproxy = urllib2.ProxyHandler({'http': mycrypt.decrypt(config.get('Network', 'proxy'))})
        opener = urllib2.build_opener(httpproxy)
        urllib2.install_opener(opener)

    #===========================================================================
    # Check for git update
    #===========================================================================
    if config.get('AutoUpdate', 'enabled') == 'true':
        updater = Updater(os.getcwd(), config.get('AutoUpdate', 'git'))

        if updater.update_available():
            log.info('New Version available: %s' % updater.hash)
            log.info('Performing Self-Update')
            updater.update()
            log.info('Re-spawning %s' % ' '.join(args))
            updater.respawn()

    #===========================================================================
    # #Add a Signal Handler for Ctrl + C
    #===========================================================================
    def signalhandler():
        log.error('Script terminated by User')
        sys.exit(1)

    signal.signal(signal.SIGINT, signalhandler)
    #===========================================================================
    # Main Program
    #===========================================================================
    for item in os.listdir(rootPath):

        #filter out folders beginning with . (Unix hidden dirs) or @ (Synology System Folders) or _ (sabnzbd Operations)
        filterext = (
            '.',  # unix hidden folders
            '@',  # Synology System Folders
            '_'   # sabnzbd Operations
        )
        if os.path.isdir(os.path.join(rootPath, item)) and not item.startswith(filterext):

            log.debug("Processing: %s" % item)

            try:
                #===================================================================
                # Create the Movie Object
                #===================================================================
                movie = Movie(os.path.join(rootPath, item), args.language, config.get('TMDB', 'apikey'))
                #===================================================================
                # Rename the Folder and Files
                #===================================================================
                movie.rename(args.forceRename)

            except Exception as e:
                log.error(str(e))
                continue

            #===================================================================
            # Prepare NFO name and check if already created by tinynfogen
            #===================================================================
            if args.globalNFOName:
                movie.newFiles['nfo'][0] = os.path.join(movie.path, args.globalNFOName)

            movie.NFO = NFO(movie.newFiles['nfo'][0], movie.infos)

            #===================================================================
            # Remove unwanted files from directory
            #===================================================================
            movie.clean(('srf', 'sub', 'srr', 'sfv', 'sft', 'jpg', 'tbn', 'idx', 'nfo', 'html', 'url', 'par2', 'rar'))
            log.debug('Cleaned files: %s' % (movie.Name + movie.Year))

            #===================================================================
            # Create the new NFO File
            #===================================================================
            #Write new NFO
            movie.NFO.Write(BoxeeBoxDict)
            log.info('NFO generated : %s' % (movie.Name + movie.Year))

            #===================================================================
            # Get Fanart and Poster
            #===================================================================
            movie.GetImages()

            #===================================================================
            # Move the Movie
            #===================================================================
            if mover:
                if mover.move(movie.path, args.forceOverwrite):

                    #===========================================================================
                    # Update the XBMC Library
                    #===========================================================================
                    if config.get('XBMC', 'updateLibrary') is 'True' or args.forceXBMCUpdate is True:

                        hostname = config.get('XBMC', 'hostname')
                        port = config.get('XBMC', 'port')
                        username = config.get('XBMC', 'username')
                        password = mycrypt.decrypt(config.get('XBMC', 'password'))
                        libraryPath = config.get('XBMC', 'libraryPath')

                        http_address = 'http://%s:%s/jsonrpc' % (hostname, port)

                        xbmc = XbmcJson(http_address, username, password)
                        try:
                            dst = libraryPath + mover.dst
                            result = xbmc.VideoLibrary.Scan(**{"directory": dst})
                        except Exception as e:
                            result = str(e)
                        log.info('Updating XBMC Library: %s' % result)

    #===========================================================================
    # End Section / Cleanup
    #===========================================================================

    end = mktime(localtime())
    log.info('Script Finished!')
    log.info('Script Runtime: %s seconds' % str(end - start))
    logging.shutdown()