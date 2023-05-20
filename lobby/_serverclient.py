import threading
import socket
import struct

"""
Helper class to manage LobbyClients connected to the LobbyServer.
"""
class ServerClient(threading.Thread):
    def __init__(self, address:str, port:int, connection:socket.socket, onpkt, onclose, *args, **kwargs):
        self.__address = address
        self.__port = port
        self.__connection = connection
        self.__onpkt = onpkt
        self.__onclose = onclose
        self.__active = False

        super().__init__(*args, **kwargs)


    def sendpkt(self, pkt_type:int, pkt_data:bytes):
        pkt_length = len(pkt_data) + 3
        pkt_header = struct.pack("<HB", pkt_length, pkt_type)
        try:
            self.__connection.sendall(pkt_header + pkt_data)
        except socket.error:
            self.__onclose(self.__address, self.__port)


    def close(self):
        self.__active = False
        self.__connection.close()


    """
    Method for receiving all data
    """
    def __recvall(self, count:int):
        buffer = b""
        while not len(buffer) == count:
            try:
                buffer += self.__connection.recv(count-len(buffer))
            except socket.error:
                self.__onclose(self.__address, self.__port)
                self.close()
            
        return buffer


    """
    Method for receiving a packet from the server
    """
    def __recvpkt(self):
        try:
            pkt_length, pkt_type = struct.unpack("<HB", self.__recvall(3))
        except socket.error:
            return -1, None
        
        try:
            return pkt_type, self.__recvall(pkt_length-3)
        except socket.error:
            return -1, None


    def run(self):
        self.__active = True
        while self.__active:
            pkt_type, pkt_data = self.__recvpkt()
            if pkt_type >= 0:
                self.__onpkt(self.__address, self.__port, pkt_type, pkt_data)