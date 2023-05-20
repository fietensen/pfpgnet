import socket
import hashlib
import time
import struct

"""
Class implementing
"""
class GameServer:
    def __init__(self, address:str, port:int, advert_address:str=None):
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = address
        self.__advert_address = advert_address
        self.__port = port
        self.__identifiers = {}
    
    
    def bind(self):
        self.__server.bind((self.__address, self.__port))
    

    def __encode_address(self, address):
        return socket.inet_aton(address[0])+struct.pack("<H", address[1])


    def __pair(self, addr1:tuple, addr2:tuple):
        self.__server.sendto(self.__encode_address(addr2), addr1)
        self.__server.sendto(self.__encode_address(addr1), addr2)


    def listen(self):
        sessid,addr = self.__server.recvfrom(32)
        if self.__identifiers.get(sessid) != None:
            if self.__identifiers[sessid] == 0:
                self.__identifiers[sessid] = addr
            else:
                self.__pair(self.__identifiers[sessid], addr)
                del self.__identifiers[sessid]
    
    def close(self):
        self.__server.close()


    def create_identifier(self):
        if self.__advert_address:
            addr = socket.inet_aton(socket.gethostbyname(self.__advert_address))
        else:
            addr = socket.inet_aton(self.__address)
        
        port = struct.pack("<H", self.__port)
        sess_id = hashlib.sha256(str(time.time()).encode()).digest()
        self.__identifiers[sess_id] = 0

        return addr + port + sess_id