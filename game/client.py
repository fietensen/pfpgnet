from game.messages import NetMessage
import threading
import socket
import struct
import time

class GameClient(threading.Thread):
    def __init__(self, address:str, port:int):
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = address
        self.__port = port

        self.__peer_address = None
        self.__peer_port = None

        self.__latency_time = 0
        self.__latency_wait = False
        self.latency = 0
        self.running = False

        super().__init__(daemon=True)
    
    @property
    def connected(self):
        return self.__peer_address != None

    
    def connect(self):
        self.__client.bind(('', 0))


    def inquire_latency(self):
        if not self.connected or self.__latency_wait:
            return
        
        self.__latency_time = time.time()
        self.__latency_wait = True
        self.__sendpkt(NetMessage.CHECK_DELAY, b"")


    """
    Sends a packet to the peer. Note: the maximum length of pkt_data may be 62 bytes
    """
    def __sendpkt(self, pkt_type:int, pkt_data:bytes):
        if not self.connected:
            return
        pkt_header = struct.pack("<BB", len(pkt_data)+2, pkt_type)
        self.__client.sendto(pkt_header + pkt_data, (self.__peer_address, self.__peer_port))


    def __recvpkt(self):
        data, conn = self.__client.recvfrom(64)
        if conn != (self.__peer_address, self.__peer_port):
            return
        
        pkt_length, pkt_type = struct.unpack("<BB", data[0:2])
        pkt_data = data[2:pkt_length]

        # for latency checking
        if pkt_type == NetMessage.ANSWER_DELAY:
            self.latency = round((time.time()-self.__latency_time)*1000/2)
            self.__latency_wait = False
        
        return pkt_type, pkt_data


    def wait_for_peer(self, session_id):
        self.__client.sendto(session_id, (self.__address, self.__port))
        connection_data,_ = self.__client.recvfrom(6)

        self.__peer_address = socket.inet_ntoa(connection_data[0:4])
        self.__peer_port = struct.unpack("<H",connection_data[4:6])[0]

        self.__sendpkt(NetMessage.HELLO, b"")
        self.__recvpkt()
        self.__sendpkt(NetMessage.ACK, b"")
        self.__recvpkt()
    

    def run(self):
        if not self.connected:
            return
        
        self.running = True
        while self.running:
            self.inquire_latency()
            print("Latency:", self.latency,"ms")
            pkt_type, pkt_data = self.__recvpkt()
            if pkt_type == NetMessage.CHECK_DELAY:
                self.__sendpkt(NetMessage.ANSWER_DELAY, b"")