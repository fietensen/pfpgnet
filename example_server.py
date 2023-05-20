from lobby.lobbyserver import LobbyServer
import time

if __name__ == '__main__':
    ls = LobbyServer("127.0.0.1", 1337)
    ls.bind()
    
    for i in range(10):
        ls.listen()
        time.sleep(6)
    
    ls.close()