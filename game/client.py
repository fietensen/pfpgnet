from pfpgnet.game.messages import NetMessage
import socket, struct, time, pygame, queue
import threading

class GameClient(threading.Thread):
    def __init__(self, address:str, port:int):
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__client.bind(('',0))
        
        self.__rendezvous_address = address
        self.__rendezvous_port = port

        self.__peer_address = None
        self.__peer_port = None


        self.__time_delta = 0
        self.remote_input_queue = queue.Queue()

        self.running = False

        super().__init__(daemon=True)
    

    @property
    def connected(self):
        return self.__peer_address


    def synchronize(self):
        if not self.connected:
            return
        
        self.__sendpkt(NetMessage.CHECK_DELAY, struct.pack("<d",time.time()))
        while True:
            pkt_type, pkt_data = self.__recvpkt()
            if pkt_type == NetMessage.CHECK_DELAY:
                self.__sendpkt(NetMessage.ANSWER_DELAY, struct.pack("<dd", struct.unpack("<d", pkt_data[0:8])[0], time.time()))
            
            elif pkt_type == NetMessage.ANSWER_DELAY:
                own_time, opp_time = struct.unpack("<dd", pkt_data[0:16])
                latency = (time.time()-own_time) / 2
                self.__time_delta = own_time-opp_time
                break
        


    def connect(self, session_id):
        self.__client.sendto(session_id, (self.__rendezvous_address, self.__rendezvous_port))
        connection_data,_ = self.__client.recvfrom(6)

        self.__peer_address = socket.inet_ntoa(connection_data[0:4])
        self.__peer_port = struct.unpack("<H", connection_data[4:6])[0]

        self.__sendpkt(NetMessage.HELLO, b"")
        self.__recvpkt()
        self.__sendpkt(NetMessage.ACK, b"")
    

    def unpack_keydata(self, data: bytes):
        time_at, ticks_in_future, keycode = struct.unpack("<dII", data[0:16])

        current_time_at = time_at + self.__time_delta
        ms_behind = (time.time()-current_time_at)*1000
        latency = 0

        lag = ticks_in_future*60 - ms_behind

        if lag < 0:
            ticks_in_future = 0
            latency = lag

        return latency, ticks_in_future, keycode


    def newest_keyevents(self):
        while not self.remote_input_queue.empty():
            action, in_ticks, latency, keycode = self.remote_input_queue.get()
            yield action, in_ticks, latency, keycode


    def send_keydown(self, keycode, future_ticks):
        self.__sendpkt(NetMessage.KEYDOWN, struct.pack("<dII", time.time(), future_ticks, keycode))

    def send_keyup(self, keycode, future_ticks):
        self.__sendpkt(NetMessage.KEYUP, struct.pack("<dII", time.time(), future_ticks, keycode))


    def handle_packet(self):
        pkt_type, pkt_data = self.__recvpkt()

        match pkt_type:
            case NetMessage.HELLO:
                self.__sendpkt(NetMessage.ACK, b"")
            
            case NetMessage.KEYDOWN:
                latency, in_ticks, keycode = self.unpack_keydata(pkt_data)
                self.remote_input_queue.put((
                    pygame.KEYDOWN, latency, in_ticks, keycode
                ))
            
            case NetMessage.KEYUP:
                latency, in_ticks, keycode = self.unpack_keydata(pkt_data)
                self.remote_input_queue.put((
                    pygame.KEYUP, latency, in_ticks, keycode
                ))


    def __recvpkt(self):
        data, conn = self.__client.recvfrom(64)
        if conn != (self.__peer_address, self.__peer_port):
            return
        
        pkt_length, pkt_type = struct.unpack("<BB", data[0:2])
        pkt_data = data[2:pkt_length]
        
        return pkt_type, pkt_data


    def __sendpkt(self, pkt_type:int, pkt_data:bytes):
        if not self.connected:
            return
        pkt_header = struct.pack("<BB", len(pkt_data)+2, pkt_type)
        self.__client.sendto(pkt_header + pkt_data, (self.__peer_address, self.__peer_port))


    def run(self):
        self.running = True
        while self.running:
            self.handle_packet()
