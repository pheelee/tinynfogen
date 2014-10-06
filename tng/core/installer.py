"""
Created on 16.11.2013

@author: ritterph
"""

import os
import sys
import ConfigParser
from libs.git import LocalRepository


class Updater(object):
    
    def __init__(self, localrepopath, gitpath):
        self.repo = localrepopath
        self.gitpath = gitpath
        self.git = LocalRepository(self.repo, self.gitpath)
        self.hash = '0'

    def update_available(self):
        """
        Checks git source if update is available
        return true or false
        """
        self.git.fetch()
        current_branch = self.git.getCurrentBranch().name
        for branch in self.git.getRemoteByName('origin').getBranches():
            local = self.git.getHead()
            remote = branch.getHead()
            if current_branch == branch.name:
                if local.hash[:8] != remote.hash[:8]:
                    self.hash = remote.hash[:8]
                    return True
        return False

    def update(self):
        self.git.pull()

    def respawn(self):
        args = sys.argv[:]
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]

        os.chdir(self.repo)
        os.execv(sys.executable, args)


class Config(object):
    
    configfile = ''
    
    def __init__(self, configfile):
        self.configfile = configfile

    def available(self):
        return os.path.isfile(self.configfile)
    
    def create(self):
        """
        Creates a config file based on user input
        return true or false
        """
        
        cfg = ConfigParser.RawConfigParser()
        
        #Get the User input
        print "Generating a new config file.."

        interactive = self.__userprompt("Enable Interactive Mode", "True, False", "False")
        apikey = self.__userprompt("apikey for themoviedb.org")
        httpproxy = self.__userprompt("HTTP Proxy url")
        usexbmc = self.__userprompt("Use XBMC", "Yes,No", "No")
        autoupdate = self.__userprompt("Enable AutoUpdate", "true,false", "true")

        #=======================================================================
        # General Section
        #=======================================================================
        cfg.add_section("General")
        cfg.set("General", interactive)
        #=======================================================================
        # XBMC Section
        #=======================================================================
        if usexbmc.lower() == "yes":
            updatelibrary = "True"
            hostname = self.__userprompt("XBMC Hostname or IP Address")
            port = self.__userprompt("XBMC Port")
            username = self.__userprompt("XBMC Username")
            password = self.__userprompt("XBMC Password")
            librarypath = self.__userprompt("XBMC Library Path (e.g. nfs://192.168.1.100)")
        else:
            updatelibrary = "False"
            hostname = ""
            port = ""
            username = ""
            password = ""
            librarypath = ""
        cfg.add_section("XBMC")
        cfg.set("XBMC", "updatelibrary", updatelibrary)
        cfg.set("XBMC", "hostname", hostname)
        cfg.set("XBMC", "port", port)
        cfg.set("XBMC", "username", username)
        cfg.set("XBMC", "password", password)
        cfg.set("XBMC", "libraryPath", librarypath)
        
        #=======================================================================
        # TMDB Section
        #=======================================================================
        cfg.add_section("TMDB")
        
        cfg.set("TMDB", "apikey", apikey)
        
        #=======================================================================
        # Network Section
        #=======================================================================
        cfg.add_section("Network")
        
        if httpproxy != '':
            cfg.set("Network", "proxy", httpproxy)
            cfg.set("Network", "useProxy", "True")
        else:
            cfg.set("Network", "useProxy", "False")
            cfg.set("Network", "proxy", "")
        
        #=======================================================================
        # AutoUpdate Section
        #=======================================================================
        cfg.add_section("AutoUpdate")
        
        if autoupdate == "true":
            git = self.__userprompt("Path to git binary")
        else:
            git = ''
        
        cfg.set("AutoUpdate", "enabled", autoupdate)
        cfg.set("AutoUpdate", "git", git)

        #=======================================================================
        # Write the Config File
        #=======================================================================
        with open(self.configfile, 'w') as configuration:
            cfg.write(configuration)
        
    @staticmethod
    def __userprompt(prompt, validation=None, default=''):
        while True:
            cprompt = "%s (%s) [%s]:" % (prompt, validation, default)
            if validation is None:
                cprompt = "%s [%s]:" % (prompt, default)
            userinput = raw_input(cprompt)
            if userinput == '':
                return default
            elif validation is None or userinput.lower() in validation.lower():
                return userinput
            print "\nincorrect input"