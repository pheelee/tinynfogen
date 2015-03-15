"""
Created on Oct 08, 2014

@author: pri@irbe.ch
"""

__author__ = 'phil'
__version__= 0.1


class Crypt(object):

    __prefix = "130886"
    __salt2  = "17"

    def __init__(self, key):
        self.__salt1 = self.__keysalt(key)

    @staticmethod
    def __keysalt(key):
        salt = []
        for i in range(0, len(key),1):
            salt.append(hex(ord(key[i])).replace('0x','').upper())
        return ''.join(salt)

    def encrypt(self, s):
        outData = []
        for i in range(0,len(s)):
            num1 = ord(s[i])
            num2 = ord(self.__salt1[i % len(s) + 1])
            outData.append("%02X" % int(int(num1 ^ num2) ^ int(self.__salt2)))
        return self.__prefix + str(self.__salt2) + ''.join(outData)

    def decrypt(self, s):
        outData = []
        if s[0:len(self.__prefix)] == self.__prefix:
            salt2 = s[len(self.__prefix):len(self.__prefix) + len(self.__salt2)]
            s = s[len(self.__prefix) + len(self.__salt2):len(s) + 1]
            for i in range(0, int(round(len(s) / 2))):
                num1 = int(s[i * 2:i * 2 + 2],16)
                num2 = ord(self.__salt1[i % len(s) + 1])
                outData.append(chr(int((num1 ^ num2)) ^ int(salt2)))

            return ''.join(outData)

        else:
            return False
