from pfpgnet.game.messages import NetMessage
import threading
import socket
import struct
import time
import pygame
import queue

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
        self.latency_refreshrate = 5

        self.remote_input_queue = queue.Queue()
        self.remote_input_clock = pygame.time.Clock()

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


    def send_keydown(self, keycode):
        self.__sendpkt(NetMessage.KEYDOWN, struct.pack("<I", keycode))
    

    def send_keyup(self, keycode):
        self.__sendpkt(NetMessage.KEYUP, struct.pack("<I", keycode))


    def newest_keyevents(self):
        while not self.remote_input_queue.empty():
            action, time_at, keycode = self.remote_input_queue.get()
            yield action, time_at, keycode


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
    

    def handle_packet(self):
        pkt_type, pkt_data = self.__recvpkt()

        match pkt_type:
            case NetMessage.HELLO:
                self.__sendpkt(NetMessage.ACK, b"")
            case NetMessage.CHECK_DELAY:
                self.__sendpkt(NetMessage.ANSWER_DELAY, b"")
            case NetMessage.ANSWER_DELAY:
                self.__latency_wait = False
                print(time.time()-self.__latency_time)
                self.latency = round((time.time()-self.__latency_time)*1000/2)
            case NetMessage.KEYDOWN:
                self.remote_input_queue.put((
                    pygame.KEYDOWN, self.remote_input_clock.tick()-self.latency, struct.unpack("<I", pkt_data[0:4])[0]
                ))
            case NetMessage.KEYUP:
                self.remote_input_queue.put((
                    pygame.KEYUP, self.remote_input_clock.tick()-self.latency, struct.unpack("<I", pkt_data[0:4])[0]
                ))
            case _:
                pass


    def check_latency(self):
        while self.running:
            self.inquire_latency()
            time.sleep(self.latency_refreshrate)
            print(f"Latency: {self.latency}ms")


    def start_latency_check(self):
        threading.Thread(target=self.check_latency, daemon=True).start()


    def run(self):
        if not self.connected:
            return
        
        self.running = True
        while self.running:
            self.handle_packet()