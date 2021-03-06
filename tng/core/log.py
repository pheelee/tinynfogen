"""
Created on 30.03.2013

@author: pri@irbe.ch
"""

import logging
import re


class TNGLog(object):

    __private_strings = ('apikey', 'api_key')
    
    def __init__(self):
    
        self.logger = logging.getLogger('TinyNFOGen')
        #Add coloring
        logging.StreamHandler.emit = self.__add_coloring_to_emit_ansi(logging.StreamHandler.emit)

    def info(self, msg):
        self.logger.info(self.__privatize(msg))
    
    def warning(self, msg):
        self.logger.warning(self.__privatize(msg))
    
    def error(self, msg):
        self.logger.error(self.__privatize(msg))
        
    def debug(self, msg):
        self.logger.debug(self.__privatize(msg))

    def __privatize(self, msg):
        for r in self.__private_strings:
            msg = re.sub('(%s=)[^\&]+' % r, '%s=xxx' % r, msg)
        return msg

    @staticmethod
    def __add_coloring_to_emit_ansi(fn):
            def new(*args):
                levelno = args[1].levelno
                if levelno >= 50:
                    color = '\x1b[31m'  # red
                elif levelno >= 40:
                    color = '\x1b[31m'  # red
                elif levelno >= 30:
                    color = '\x1b[33m'  # yellow
                elif levelno >= 20:
                    color = '\x1b[0m'
                elif levelno >= 10:
                    color = '\x1b[36m'
                else:
                    color = '\x1b[0m'  # normal
        
                if not args[1].msg.startswith(color):
                    args[1].msg = color + args[1].msg + '\x1b[0m'
        
                return fn(*args)
            return new
