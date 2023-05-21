from pfpgnet.lobby.messages import NetMessage, VERSION
import socket
import sys
import struct

"""
Exception raised when client connects to a server with the wrong version.
"""
class VersionMismatchException(Exception):
    pass


"""
===================== LobbyClient
- LobbyClient(address, port, debug = False, cid = "")
"""
class LobbyClient:
    def __init__(self, address:str, port:int, debug:bool=False, cid:str=""):
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__address = address
        self.__port = port
        self.__cid = cid
        self.__debug = debug
        self.__connected = False


    """
    Returns the address of the server. (No setter defined)
    """
    @property
    def address(self):
        return self.__address
    

    """
    Returns the port of the server. (No setter defined)
    """
    @property
    def port(self):
        return self.__port


    """
    Returns a bool whether the LobbyClient is connected to the LobbyServer. (No setter defined)
    """
    @property
    def connected(self) -> bool:
        return self.__connected


    """
    Logs a message to stdout if debug is enabled.
    """
    def __log(self, message:str):
        if self.__debug:
            print("[LOG]"+message)


    """
    Logs an error to stderr regardless of whether debug is enabled.
    """
    def __error(self, message:str):
        print("[ERROR]"+message, file=sys.stderr)


    """
    Method for reconnecting to the server.
    """
    def reset_connection(self):
        if self.__server:
            try:
                print("CLOSE")
                self.__server.close()
            except socket.error:
                pass
            self.__server = None
        self.__connected = False
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server.settimeout(10)
        return self.connect()


    """
    Method for sending packet to server.
    """
    def __sendpkt(self, packet_type:int, data:bytes):
        if self.connected:
            pkt_header = struct.pack("<HB", len(data)+3, packet_type)
            try:
                self.__server.sendall(pkt_header + data)
            except socket.error:
                self.__error(f"[PFPGNET:LobbyClient#{self.__cid}] Failed to send packet to LobbyServer. Resetting connection.")
                self.reset_connection()
                raise socket.error
        
    
    """
    Method for receiving all data
    """
    def __recvall(self, count:int):
        buffer = b""
        while not len(buffer) == count:
            try:
                buffer += self.__server.recv(count-len(buffer))
            except socket.error as e:
                self.__error(f"[PFPGNET:LobbyClient#{self.__cid}] Failed to receive packet from LobbyServer. Resetting connection.")
                self.reset_connection()
                raise socket.error
            
        return buffer


    """
    Method for receiving a packet from the server
    """
    def __recvpkt(self):
        if self.connected:
            try:
                pkt_length, pkt_type = struct.unpack("<HB", self.__recvall(3))
            except socket.error:
                return -1, None
        
            try:
                return pkt_type, self.__recvall(pkt_length-3)
            except socket.error:
                return -1, None
        else:
            return -1, None


    """
    Method for sending a message and retrieving it's answer.
    """
    def __answer(self, pkt_type:int, packet_data:bytes):
        self.__sendpkt(pkt_type, packet_data)
        return self.__recvpkt()


    """
    Try and connect and authenticate to LobbyServer via address and port
    supplied in the constructor. Returns whether the connection was successful.
    """
    def connect(self) -> bool:
        try:
            self.__server.connect((self.__address, self.__port))
            self.__connected = True
            self.__log(f"[PFPGNET:LobbyClient#{self.__cid}] Connected to LobbyServer@{self.__address}:{self.__port}")
            self.__authenticate()
        except socket.error:
            self.__error(f"[PFPGNET:LobbyClient#{self.__cid}] Failed to connect to LobbyServer@{self.__address}:{self.__port}")
            return False
    

    """
    Close the connection to the LobbyServer
    """
    def close(self):
        self.__sendpkt(NetMessage.CLIENT_DISCONNECT, b"")
        print("CLOSE")
        self.__server.close()


    """
    Request a search a peer
    """
    def find_partner(self) -> tuple:
        self.__sendpkt(NetMessage.CLIENT_SEARCH, b"")
        while True:
            pkt_type, pkt_data = self.__recvpkt()
            if pkt_type == -1:
                continue
            elif pkt_type == NetMessage.SERVER_FOUND:
                server_addr = socket.inet_ntoa(pkt_data[0:4])
                server_port = struct.unpack("<H", pkt_data[4:6])[0]
                return server_addr, server_port, pkt_data[6:]
            elif pkt_type == NetMessage.SERVER_DISCONNECT:
                print("CLOSE")
                self.close()
                return None, None, None


    """
    Try and authenticate to the LobbyServer as a LobbyClient
    """
    def __authenticate(self):
        try:
            answer_type, answer_data = self.__answer(NetMessage.CLIENT_HELLO, struct.pack("<BBB", *VERSION))
            if answer_type == NetMessage.SERVER_ACK:
                # Everything went right, the client and the server are connected and authenticated
                return
            
            elif answer_type == NetMessage.SERVER_DISCONNECT:
                # At this stage, this can only mean the version is mismatching
                raise VersionMismatchException("LobbyClient Version: {}.{}.{}; LobbyServer Version: {}.{}.{}".format(
                    *VERSION, *struct.unpack("<BBB", answer_data)))

        except socket.error:
            return