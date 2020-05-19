from _thread import start_new_thread

import pygame
import sys
from network import Network
from globals import *
import pygame_menu
import math

def set_my_role(role_title, selcted_role):
    global my_role
    my_role = selcted_role


def set_my_team(team_title, selcted_team):
    global my_team
    my_team = selcted_team


def play_as_captain():
    global server_str_board, server_can_act, server_is_stopped
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    try:
        str_board, can_act, is_stopped = network.send("captain get")
    except Exception as e:
        print(e)


    while game_states != "exit":
        #last_iteration_str_board = str_board
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                str_board, can_act, is_stopped = network.listen()


        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP:
                click_pos = pygame.mouse.get_pos()
                print(click_pos)
                # switch 0,1 because (x,y) == (col,row)
                clicked_locations = clicked_locations.union({click_pos})
        if can_act:
            target_clicked = None
            for loc_clicked in clicked_locations:
                for i in range(board_height):
                    for j in range(board_width):
                        if math.hypot(int(126 + 51.7 * j) - loc_clicked[0], int(109 + 44.9 * i) - loc_clicked[1]) < 12:
                            if str_board[board_height*i + j] == "y":
                                target_clicked = (i,j)
                                break
                    else:
                        continue
                    break
                else:
                    continue
                break

            if target_clicked:
                network.only_send("captain clicked loc")
                result = network.send(target_clicked)
                print(result)
                str_board, can_act, is_stopped = result

        draw_captain_screen(screen, str_board, is_stopped)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()


def draw_captain_screen(screen, str_board, is_stopped):
    screen.fill(white)
    if is_stopped:
        return
    #background img
    background_image = pygame.image.load('../img/AlphaMap2.jpeg')
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    background_image_rect = background_image.get_rect()
    background_image_rect.left, background_image_rect.top = [0,0]
    screen.blit(background_image, background_image_rect)

    for i in range(board_height):
        for j in range(board_width):
            c = str_board[i*board_height + j]
            if c:
                if c == "r":
                    color = red
                    pygame.draw.circle(screen, color, (int(126 + 51.7 * j), int(109 + 44.9 * i)), 12)
                elif c == "b":
                    color = black
                    pygame.draw.circle(screen, color, (int(126 + 51.7 * j), int(109 + 44.9 * i)), 12)
                elif c == "y":
                    color = yellow
                    pygame.draw.circle(screen, color, (int(126 + 51.7 * j), int(109 + 44.9 * i)), 12)


def start_the_game():
    try:
        if my_role == CAPTAIN:
            play_as_captain()
    except Exception as e:
        network.close()
        raise e


def text_objects(text, font):
    text_surface = font.render(text, True, white)
    return text_surface, text_surface.get_rect()

def message_display(screen, text, x=screen_width / 2, y=screen_height / 2, size=100):
    large_text = pygame.font.SysFont('comicsansms', size)
    text_surf, text_rect = text_objects(text, large_text)
    text_rect.center = (x, y)
    screen.blit(text_surf, text_rect)

def choose_team():
    server_respond = network.send((my_team, my_role))
    if server_respond == "ok":
        return True


def try_start_game():
    global start_game_menu
    choose_team_result = choose_team()
    if choose_team_result:
        start_the_game()
    else:
        if not start_game_menu.get_widget("role taken"):
            start_game_menu.add_label("role taken", "role taken")



my_role = CAPTAIN
my_team = BLUE_TEAM
start_game_menu = None
network = None
screen = None

def main():
    global screen, network, start_game_menu, my_team, my_role
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))

    try:
        network = Network()
    except:
        try_again_menu = pygame_menu.Menu(300, 400, 'Cant connect to server', theme=pygame_menu.themes.THEME_BLUE)
        try_again_menu.add_button('Try again', main)
        try_again_menu.mainloop(screen)

    start_game_menu = pygame_menu.Menu(300, 400, 'Welcome', theme=pygame_menu.themes.THEME_BLUE)
    start_game_menu.add_selector('Team :', [('blue', BLUE_TEAM), ('yellow', YELLOW_TEAM)], onchange=set_my_team)
    start_game_menu.add_selector('Role :', [('captain', CAPTAIN), ('first mate', FIRST_MATE), ('engineer', ENGINEER),
                                            ('radio operator', RADIO_OPERATOR)], onchange=set_my_role)
    start_game_menu.add_button('Play', try_start_game)
    start_game_menu.add_button('Quit', pygame_menu.events.EXIT)

    start_game_menu.mainloop(screen)

if __name__ == '__main__':
    main()
