import os
import sys
import time
import socket
from _thread import start_new_thread

# developer note: player must be imported from before game_file to avoid circular importing
from player import CaptainState, FirstMateState
from game_file import Game
from network import send_msg, recv

server = "127.0.0.1"
port = 7777
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")

game = Game()



def threaded_client(conn, this_player_id):
    """
    This function serves and handles one client
    """
    global game

    # recieves player request to join game
    this_player = None
    while True:
        # recieves player team & role
        try:
            this_player_team, this_player_role = recv(conn)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, str(e))
            break

        # checks if role is not taken
        for player in game.players:
            if player.online and player.role == this_player_role and player.team == this_player_team:
                send_msg(conn, "role taken")
                break

        # if role is accepted
        else:
            send_msg(conn, "role accepted")
            this_player = game.add_new_player(this_player_team, this_player_role)
            break

    # recieves and handles requests and notifications from user
    current_player_state = this_player.get_state(game)
    while this_player:
        try:
            data = recv(conn, blocking=False)

            if data:

                if data == "get": # client init
                    current_player_state = this_player.get_state(game)

                elif "clicked" in data: # user acted and the client will send what he clicked on
                    target_clicked = recv(conn)
                    this_player.clicked(game, target_clicked)
                    current_player_state = this_player.get_state(game)

                # captain stuff
                elif data == "captain stop":
                    game.is_stopped = True
                    current_player_state = this_player.get_state(game)

                send_msg(conn, tuple(current_player_state))

            # update client for the new state if needed
            if this_player.get_state(game) != current_player_state:
                send_msg(conn, "sending game state")
                current_player_state = this_player.get_state(game)
                send_msg(conn, tuple(current_player_state))

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, str(e))
            break

    print("Lost connection")
    conn.close()
    this_player.disconnected()

def main():
    currentPlayer = 0
    addreses_dict = {}
    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)
        if currentPlayer < 8:
            start_new_thread(threaded_client, (conn, currentPlayer))
            addreses_dict[addr[0]] = currentPlayer
            currentPlayer += 1
        elif addr[0] in addreses_dict:
            start_new_thread(threaded_client, (conn, addreses_dict[addr[0]]))





if __name__ == '__main__':
    main()