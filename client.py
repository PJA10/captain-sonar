from _thread import start_new_thread

import pygame
import sys
from network import Network
from globals import *
import pygame_menu
import math


def detect_target_clicked(clicked_locations, str_board):
    target_clicked = None
    for loc_clicked in clicked_locations:
        for i in range(board_height):
            for j in range(board_width):
                if math.hypot(int(0.0984375 * screen_width + 0.040390625 * screen_width * j) - loc_clicked[0],
                              int(0.13625 * screen_height + 0.056125 * screen_height * i) - loc_clicked[1]) < int(
                        0.00576923077 * (screen_height + screen_width)):
                    if str_board[board_height * i + j] == "y":
                        target_clicked = (i, j)
                        break
            else:
                continue
            break
        else:
            continue
        break
    return target_clicked

def send_to_server_target_clicked(network, target_clicked):
    network.only_send("captain clicked loc")
    return network.send(target_clicked)


def detect_button_clicked(button, clicked_locations):
    for loc_clicked in clicked_locations:
        if button.collidepoint(loc_clicked):
            return True
    return False

def play_as_captain(network, screen):
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    try:
        str_board, can_act, is_stopped = network.send("captain get")
    except Exception as e:
        print(e)

    stop_button = pygame.Rect(4*screen_width//5, screen_width//3, 200, 200)

    while game_states != "exit":

        # check for update from server
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                str_board, can_act, is_stopped = network.listen()

        # collect pygame events
        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                click_pos = event.pos
                print(click_pos)
                clicked_locations = clicked_locations.union({click_pos})

        # logic
        if can_act:
            target_clicked = detect_target_clicked(clicked_locations, str_board)
            if target_clicked:
                str_board, can_act, is_stopped = send_to_server_target_clicked(network, target_clicked)

        if not is_stopped and detect_button_clicked(stop_button, clicked_locations):
            str_board, can_act, is_stopped = network.send("captain stop")

        # draw
        draw_captain_screen(screen, str_board, is_stopped, stop_button)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()


def draw_captain_screen(screen, str_board, is_stopped, stop_button):
    if is_stopped:
        screen.fill(black)
        message_display(screen, "stop")
        return
    #background img
    background_image = pygame.image.load('img/AlphaMap2.jpeg')
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    background_image_rect = background_image.get_rect()
    background_image_rect.left, background_image_rect.top = [0,0]
    screen.blit(background_image, background_image_rect)

    pygame.draw.rect(screen, white, stop_button)  # draw button

    for i in range(board_height):
        for j in range(board_width):
            c = str_board[i*board_height + j]
            if c:
                if c == "r":
                    color = red
                    pygame.draw.circle(screen, color, (int(0.0984375*screen_width + 0.040390625*screen_width * j), int(0.13625*screen_height + 0.056125*screen_height * i)), int(0.00576923077*(screen_height+screen_width)))
                elif c == "b":
                    color = black
                    pygame.draw.circle(screen, color, (int(0.0984375*screen_width + 0.040390625*screen_width * j), int(0.13625*screen_height + 0.056125*screen_height* i)), int(0.00576923077*(screen_height+screen_width)))
                elif c == "y":
                    color = yellow
                    pygame.draw.circle(screen, color, (int(0.0984375*screen_width + 0.040390625*screen_width * j), int(0.13625*screen_height + 0.056125*screen_height * i)), int(0.00576923077*(screen_height+screen_width)))

def play_as_first_mate(network, screen):
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    try:
        powers_charges, hp, can_act, is_stopped= network.send("first mate get")
    except Exception as e:
        print(e)


    while game_states != "exit":
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                powers_charges, hp, can_act, is_stopped = network.listen()

        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                click_pos = event.pos
                print(click_pos)
                clicked_locations = clicked_locations.union({click_pos})

        draw_first_mate_screen(screen, is_stopped)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()

def draw_first_mate_screen(screen, is_stopped):
    if is_stopped:
        screen.fill(black)
        message_display(screen, "stop")
        return

    # background img
    background_image = pygame.image.load('img/FirstMateCard.jpeg')
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    background_image_rect = background_image.get_rect()
    background_image_rect.left, background_image_rect.top = [0, 0]
    screen.blit(background_image, background_image_rect)

def start_the_game(network, screen, my_pick):
    try:
        my_role = my_pick[1]
        if my_role == CAPTAIN:
            play_as_captain(network, screen)
        elif my_role == FIRST_MATE:
            play_as_first_mate(network, screen)

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

def choose_team(network, my_pick):
    server_respond = network.send(my_pick)
    if server_respond == "ok":
        return True


def try_start_game(network, screen, my_picking_selectors, start_game_menu):
    my_pick = (my_picking_selectors[0].get_value()[1], my_picking_selectors[1].get_value()[1])
    choose_team_result = choose_team(network, my_pick)
    if choose_team_result:
        start_the_game(network, screen, my_pick)
    else:
        if not start_game_menu.get_widget("role taken"):
            start_game_menu.add_label("role taken", "role taken")



def main():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    my_team, my_role = BLUE_TEAM, CAPTAIN
    try:
        network = Network()
    except:
        try_again_menu = pygame_menu.Menu(300, 400, 'Cant connect to server', theme=pygame_menu.themes.THEME_BLUE)
        try_again_menu.add_button('Try again', main)
        try_again_menu.mainloop(screen)

    start_game_menu = pygame_menu.Menu(300, 400, 'Welcome', theme=pygame_menu.themes.THEME_BLUE)
    team_selector = start_game_menu.add_selector('Team :', [('blue', BLUE_TEAM), ('yellow', YELLOW_TEAM)])
    role_selector = start_game_menu.add_selector('Role :', [('captain', CAPTAIN), ('first mate', FIRST_MATE), ('engineer', ENGINEER),
                                            ('radio operator', RADIO_OPERATOR)])
    start_game_menu.add_button('Play', try_start_game, network, screen, (team_selector, role_selector), start_game_menu)
    start_game_menu.add_button('Quit', pygame_menu.events.EXIT)

    start_game_menu.mainloop(screen)

if __name__ == '__main__':
    main()
