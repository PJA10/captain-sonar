import time

from player import CaptainState, FirstMateState
from gameFile import *
from _thread import *
import sys, os
from network import *

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
    global game

    this_player = None
    while True: # player choose team
        try:
            this_player_team, this_player_role = recv(conn)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, str(e))
            break
        for player in game.players:
            if player.online and player.role == this_player_role and player.team == this_player_team:
                send_msg(conn, "role taken")
                break
        else:
            send_msg(conn, "ok")
            this_player = game.add_new_player(this_player_team, this_player_role)
            break

    reply = ""
    current_player_state = this_player.get_state(game)
    while this_player:
        try:
            data = recv(conn, blocking=False)
            if data:
            
                # captain stuff
                if data == "captain get":
                    current_player_state = this_player.get_state(game)
                elif data == "captain clicked loc":
                    target_clicked = recv(conn)
                    this_player.clicked(game, target_clicked)
                    current_player_state = this_player.get_state(game)
                elif data == "captain stop":
                    game.is_stopped = True
                    current_player_state = this_player.get_state(game)

                # first mate stuff
                elif data == "first mate get":
                    current_player_state = this_player.get_state(game)
                elif data == "first mate clicked power":
                    power_clicked_index = recv(conn)
                    # power clicked is sent to the server as the index of the power in powerActionsList witch is the same as powers_rects
                    this_player.load_power(power_clicked_index)
                    current_player_state = this_player.get_state(game)

                # engineer stuff
                elif data == "engineer get":
                    current_player_state = this_player.get_state(game)
                elif data == "engineer clicked tool":
                    tool_to_brake_cords = recv(conn)
                    this_player.brake_tool(tool_to_brake_cords)
                    current_player_state = this_player.get_state(game)

                # radio operator stuff
                elif data == "radio operator get":
                    current_player_state = this_player.get_state(game)

                send_msg(conn, tuple(current_player_state))


            # update client for the new state if needed
            if this_player.get_state(game) != current_player_state:
                send_msg(conn, "sending game state")
                current_player_state = this_player.get_state(game)
                send_msg(conn, tuple(current_player_state))

            #time.sleep(1)

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