'''
Created on 16.11.2013

@author: ritterph
'''

import os,sys
import ConfigParser


class Updater(object):
    
    def __init__(self):
        pass
    
    def updateAvailable(self):
        '''
        Checks git source if update is available
        return true or false
        '''

class Config(object):
    
    configfile = ''
    
    def __init__(self,configfile):
        self.configfile = configfile
    
    
    def isAvailable(self):
        return os.path.isfile(self.configfile)
    
    def create(self):
        '''
        Creates a config file based on user input
        return true or false
        '''
        
        cfg = ConfigParser.RawConfigParser()
        
        #Get the Userinput
        print "Generating a new config file.."

        apikey = self._getUserInput("apikey for themoviedb.org")
        httpproxy = self._getUserInput("HTTP Proxy url")
        useXBMC = self._getUserInput("Use XBMC", "Yes,No", "No")
        autoupdate = self._getUserInput("Enable AutoUpdate", "true,false", "true")
        


        #=======================================================================
        # XBMC Section
        #=======================================================================
        if useXBMC.lower() == "yes":
            updateLibrary = "True"
            xbmcHostname = self._getUserInput("XBMC Hostname or IP Address")
            xbmcPort = self._getUserInput("XBMC Port")
            xbmcUsername = self._getUserInput("XBMC Username")
            xbmcPassword = self._getUserInput("XBMC Password")
            libraryPath = self._getUserInput("XBMC Library Path (e.g. nfs://192.168.1.100)")
        else:
            updateLibrary = "False"
            xbmcHostname = ""
            xbmcPort = ""
            xbmcUsername = ""
            xbmcPassword = ""
            libraryPath = ""
        cfg.add_section("XBMC")
        cfg.set("XBMC", "updateLibrary", updateLibrary)
        cfg.set("XBMC","hostname", xbmcHostname)
        cfg.set("XBMC","port", xbmcPort)
        cfg.set("XBMC","username",xbmcUsername)
        cfg.set("XBMC","password",xbmcPassword)
        cfg.set("XBMC","libraryPath",libraryPath)
        
        #=======================================================================
        # TMDB Section
        #=======================================================================
        cfg.add_section("TMDB")
        
        cfg.set("TMDB","apikey",apikey)
        
        #=======================================================================
        # Network Section
        #=======================================================================
        cfg.add_section("Network")
        
        if httpproxy != '':
            cfg.set("Network","proxy",httpproxy)
            cfg.set("Network","useProxy","True")
        else:
            cfg.set("Network","useProxy","False")
            cfg.set("Network","proxy","")
        
        #=======================================================================
        # AutoUpdate Section
        #=======================================================================
        cfg.add_section("AutoUpdate")
        
        if autoupdate == "true":
            gitbinary = self._getUserInput("Path to git binary")
        else:
            gitbinary = ''
        
        cfg.set("AutoUpdate","enabled",autoupdate)
        cfg.set("AutoUpdate","git",gitbinary)
        
        
        #=======================================================================
        # Write the Config File
        #=======================================================================
        with open(self.configfile,'w') as configuration:
            cfg.write(configuration)
        
    def _getUserInput(self,prompt,validation=None,default=''):
        while True:
            cprompt = "%s (%s) [%s]:" % (prompt,validation,default)
            if validation is None:
                cprompt = "%s [%s]:" % (prompt,default)
            userinput = raw_input(cprompt)
            if userinput == '':
                return default
            elif validation is None or userinput.lower() in validation.lower():
                return userinput
            print "\nincorrect input"
            
            
            
            