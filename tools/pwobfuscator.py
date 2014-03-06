'''
Created on Sept 13, 2013

@author: phil
'''

class obfuscator(object):
    
    def __init__(self,shift):
        self.shift = shift

    def _convert(self,string,operator):
        
        ob = []
        output = []
        for char in list(string):
            if operator == 'obfuscate':
                ob.append(ord(char) + self.shift)
            elif operator == 'deobfuscate':
                ob.append(ord(char) - self.shift)
            
        for item in ob:
            output.append(chr(item))
            
        return ''.join(output)

    def obfuscate(self,string):
        return self._convert(string, 'obfuscate')
        
    def deobfuscate(self,string):
        return self._convert(string, 'deobfuscate')
