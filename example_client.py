from lobby.lobbyclient import LobbyClient
import time

if __name__ == '__main__':
    lc = LobbyClient("127.0.0.1", 1337, debug=True, cid="testclient")
    lc.connect()
    time.sleep(5)
    lc.close()