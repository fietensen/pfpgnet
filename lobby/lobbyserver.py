from lobby.messages import NetMessage, VERSION
from lobby._serverclient import ServerClient
import socket
import sys
import struct

"""
===================== LobbyServer
- LobbyServer(address, port)
"""
class LobbyServer:
    def __init__(self, address:str, port:int, on_lobbyrequest):
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.__server.settimeout(10)
        self.__address = address
        self.__port = port
        self.__ready = False
        self.__clients = {}
        self.__searching_client = None
        self.__on_lobbyrequest = on_lobbyrequest


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
    Returns a bool whether the server is set up and ready. (No setter defined)
    """
    @property
    def ready(self):
        return self.__ready


    """
    Logs a message to stdout.
    """
    def __log(self, message:str):
        print("[LOG]"+message)


    """
    Logs an error to stderr.
    """
    def __error(self, message:str):
        print("[ERROR]"+message, file=sys.stderr)


    """
    Bind the address and port to the server.
    """
    def bind(self) -> bool:
        self.__server.bind((self.__address, self.__port))
        self.__server.listen(1000)
        self.__ready = True


    """
    Called by a client once a packet is received.
    """
    def __recvpkt(self, address:str, port:int, packet_type:int, packet_data:bytes):
        address = (address, port)
        
        if packet_type == NetMessage.CLIENT_DISCONNECT:
            self.__closeconn(*address)
        
        elif packet_type == NetMessage.CLIENT_HELLO:
            client_version = struct.unpack("<BBB", packet_data)
            if client_version != VERSION:
                self.__clients[address].sendpkt(NetMessage.SERVER_DISCONNECT, struct.pack("<BBB", VERSION))
            
            else:
                self.__clients[address].sendpkt(NetMessage.SERVER_ACK, b"")
        
        elif packet_type == NetMessage.CLIENT_SEARCH:
            self.__log(f"[LobbyServer] Client {address[0]}:{address[1]} entered queue.")

            if self.__searching_client == None:
                self.__searching_client = address
            
            else:
                game_info = self.__on_lobbyrequest()
                self.__log(f"[LobbyServer] Matching up {address[0]}:{address[1]} and {self.__searching_client[0]}:{self.__searching_client[1]}")
                self.__clients[self.__searching_client].sendpkt(NetMessage.SERVER_FOUND, game_info)
                self.__clients[address].sendpkt(NetMessage.SERVER_FOUND, game_info)

                # NOTE: May later decide whether or not to close both clients' connections here, but maybe they want to open another session later
                self.__searching_client = None


    """
    Closes the connection to a client
    """
    def __closeconn(self, address, port):
        self.__log(f"[LobbyServer] Removing client {address}:{port} from connections.")
        del self.__clients[(address, port)]

    
    """
    Disconnect all clients and close the server
    """
    def close(self):
        for address, client in self.__clients.items():
            client.close()
        self.__server.close()


    """
    Accept a connection.
    """
    def listen(self):
        try:
            conn, addr = self.__server.accept()
            self.__log(f"[LobbyServer] Connection from {addr[0]}:{addr[1]}")
            self.__clients[addr] = ServerClient(*addr, conn,
                                                lambda address, port, packet_type, packet_data: self.__recvpkt(address, port, packet_type, packet_data),
                                                lambda address, port: self.__closeconn(address, port))
            self.__clients[addr].start()
        except socket.timeout:
            self.listen()