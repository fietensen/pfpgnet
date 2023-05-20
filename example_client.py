from lobby.lobbyclient import LobbyClient
from game.client import GameClient
import time

if __name__ == '__main__':
    lc = LobbyClient("127.0.0.1", 1337, debug=True, cid="testclient")
    lc.connect()
    rendezvous_address, rendezvous_port, session_id = lc.find_partner()
    print("Found partner")
    lc.close()

    gc = GameClient(rendezvous_address, rendezvous_port)
    gc.connect()
    gc.wait_for_peer(session_id)
    gc.start()

    while True:
        pass