from lobby.lobbyserver import LobbyServer
from game.server import GameServer
import time

if __name__ == '__main__':
    # Creating the two Servers
    gs = GameServer("127.0.0.1", 1338)
    ls = LobbyServer("127.0.0.1", 1337, gs.create_identifier)

    # "Starting" both Servers
    ls.bind()
    gs.bind()

    # accepting 2 clients
    for i in range(2):
        ls.listen()


    # accepting 2 clients
    for i in range(2):
        gs.listen()
    
    # closing game server
    gs.close()