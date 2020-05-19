import time

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
    client_board_str = this_player.get_board_str(game)
    client_can_act, client_stop = this_player.can_act, game.is_stopped
    client_powers_charges, client_hp = this_player
    while this_player:
        try:
            data = recv(conn, blocking=False)
            if data:

                # captain stuff
                if data == "captain get":
                    reply = this_player.get_board_str(game), this_player.can_act, game.is_stopped
                    client_board_str, client_can_act, client_stop = this_player.get_board_str(
                        game), this_player.can_act, game.is_stopped

                elif data == "captain clicked loc":
                    target_clicked = recv(conn)
                    this_player.clicked(game, target_clicked)
                    reply = this_player.get_board_str(game), this_player.can_act, game.is_stopped
                    client_board_str, client_can_act, client_stop = this_player.get_board_str(
                        game), this_player.can_act, game.is_stopped

                elif data == "captain stop":
                    game.is_stopped = True
                    reply = this_player.get_board_str(game), this_player.can_act, game.is_stopped

                # first mate stuff
                elif data == "first mate get":
                    reply = this_player.powers_charges, this_player.submarine.hp, this_player.can_act, game.is_stopped
                    client_powers_charges, client_hp, client_can_act, client_stop

                send_msg(conn, reply)

            if this_player_role == CAPTAIN:
                if (this_player.get_board_str(game), this_player.can_act, game.is_stopped) != (client_board_str, client_can_act, client_stop):
                    send_msg(conn, "sending game state")
                    send_msg(conn, (this_player.get_board_str(game), this_player.can_act, game.is_stopped))
                    client_board_str, client_can_act, client_stop = this_player.get_board_str(game), this_player.can_act, game.is_stopped

            if this_player_role == FIRST_MATE:
                pass
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