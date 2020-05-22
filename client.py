from _thread import start_new_thread

import pygame
import sys
from network import Network
from globals import *
import pygame_menu
import math


class DrawingCell(object):
    def __init__(self, pos, color=(128, 30, 30)):
        self.size = 12
        self.color = color
        self.subsurface = pygame.Surface((self.size,self.size))
        self.subsurface.fill(self.color)
        self.pos = (pos[0]-self.size//2, pos[1]-self.size//2)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)

    def change_color(self, color):
        self.color = color
        self.subsurface.fill(self.color)

    def draw(self, win):
        if self.color != [255, 255, 255]:
            win.blit(self.subsurface, self.pos)

    def move(self, dx, dy):
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)

class Button(object):
    def __init__(self, posX, posY, width, height, img_name, clicked, color=(80, 80, 80)):
        self.pos = (posX, posY)
        self.width, self.height = width, height
        self.color = color
        self.clicked = clicked
        self.subsurface = pygame.Surface((self.width, self.height))
        self.subsurface.fill(self.color)
        self.img = pygame.transform.scale(pygame.image.load(img_name), (self.width//4, self.height//4))
        self.rect = pygame.Rect(posX, posY, width, height)

    def draw(self, win):
        if self.clicked:
            self.subsurface.set_alpha(255)
        else:
            self.subsurface.set_alpha(150)

        win.blit(self.subsurface, self.pos)
        self.subsurface.blit(self.img, (15, self.height/3))
        win.blit(pygame.transform.scale(self.img, (22, 22)), (self.pos[0] + 3, self.pos[1] + 2))



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


def send_to_server_user_actions(network, user_action_str, user_action):
    network.only_send(user_action_str)
    return network.send(user_action)


def is_rect_clicked(rect, clicked_locations):
    for loc_clicked in clicked_locations:
        if rect.collidepoint(loc_clicked):
            return True
    return False

def play_as_captain(network, screen):
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    try:
        can_act, is_stopped, str_board = network.send("captain get")
    except Exception as e:
        print(e)

    bg_img_data = load_bg_img('img/AlphaMap2.jpeg')
    stop_button = pygame.Rect(4*screen_width//5, screen_height//2, 150, 150) # stop_button pos

    while game_states != "exit":
        # check for update from server
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                can_act, is_stopped, str_board = network.listen()

        # collect pygame events
        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                clicked_locations = clicked_locations.union({event.pos}) # add curr pos to the set
                print(event.pos) # debug

        # logic
        if can_act:
            target_clicked = detect_target_clicked(clicked_locations, str_board)
            if target_clicked:
                can_act, is_stopped, str_board = send_to_server_user_actions(network, "captain clicked loc", target_clicked)

        if not is_stopped and is_rect_clicked(stop_button, clicked_locations):
            can_act, is_stopped, str_board = network.send("captain stop")

        # draw
        draw_captain_screen(screen, bg_img_data, str_board, is_stopped, stop_button)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()


def draw_captain_screen(screen, bg_img_data, str_board, is_stopped, stop_button):
    if is_stopped:
        draw_stop_screen(screen)
        return

    screen.blit(bg_img_data[0], bg_img_data[1])

    pygame.draw.rect(screen, black, stop_button)  # draw button
    message_display(screen, "stop", stop_button.x+stop_button.width//2, stop_button.y+stop_button.height//2, stop_button.width//3)

    draw_captain_str_board(screen, str_board)


def draw_captain_str_board(screen, str_board):
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
        can_act, is_stopped, powers_charges, hp = network.send("first mate get")
    except Exception as e:
        print(e)

    bg_img_data = load_bg_img('img/FirstMateCard.jpeg')

    powers_rects = []
    for i in range(2):
        for j in range(3):
            powers_rects.append(pygame.Rect([143 + 394 * j, 173 + 265 * i, 232, 165]))

    while game_states != "exit":
        # check for update from server
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                can_act, is_stopped, powers_charges, hp = network.listen()

        # collect pygame events
        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                clicked_locations = clicked_locations.union({event.pos})
                print(event.pos)

        #logic
        if can_act:
            power_clicked = detect_power_clicked(powers_rects[:len(powers_charges)], clicked_locations)
            if power_clicked:
                can_act, is_stopped, powers_charges, hp = send_to_server_user_actions(network, "first mate clicked power", powers_rects.index(power_clicked))
                # power clicked is sent to the server as the index of the power in powerActionsList witch is the same as powers_rects

        # draw
        draw_first_mate_screen(screen, bg_img_data, is_stopped, powers_rects, powers_charges, can_act)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()



def detect_power_clicked(rects_list, clicked_locations):
    for rect in rects_list:
        if is_rect_clicked(rect, clicked_locations):
            return rect

    return None


def draw_first_mate_screen(screen, bg_img_data, is_stopped, powers_rects, powers_charges, can_act):
    if is_stopped:
        screen.fill(black)
        message_display(screen, "stop")
        return

    screen.blit(bg_img_data[0], bg_img_data[1])

    draw_charge_bars(screen, powers_charges, powers_rects, can_act)


def draw_charge_bars(screen, powers_charges, powers_rects, can_act):
    for power_charge, rect in zip(powers_charges, powers_rects):
        for k in range(power_charge[0]):
            pygame.draw.arc(screen, red, rect, math.pi/2 - ((k+1) * math.pi/4), math.pi/2 - (k * math.pi/4), 20)

        if can_act and power_charge[0] < power_charge[1]:
            pygame.draw.arc(screen, yellow, rect, math.pi/2 - ((power_charge[0]+1) * math.pi/4), math.pi/2 - (power_charge[0] * math.pi/4), 20)


def play_as_engineer(network, screen):
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    try:
        can_act, is_stopped, tools_state = network.send("engineer get")
    except Exception as e:
        print(e)

    bg_img_data = load_bg_img('img/EngineerCard.jpeg')
    tools_rects = []
    for j in range(3):
        tools_rects_row = []
        for i in range(12):
            tools_rects_row.append(pygame.Rect([164 + 71*i + 39*(i//3),418 + j*76,60,50]))
        tools_rects.append(tools_rects_row)

    while game_states != "exit":
        # check for update from server
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                can_act, is_stopped, tools_state = network.listen()

        # collect pygame events
        clicked_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                clicked_locations = clicked_locations.union({event.pos})
                print(event.pos)

        # logic
        if can_act:
            possible_tools_to_break_rects = []
            for tool in tools_state:
                if tool[1] == "y":
                    possible_tools_to_break_rects.append(tools_rects[tool[0][0]][tool[0][1]])
            tool_clicked = detect_power_clicked(possible_tools_to_break_rects, clicked_locations)
            if tool_clicked:
                tool_clicked_cords = [(i, colour.index(tool_clicked)) for i, colour in enumerate(tools_rects) if tool_clicked in colour][0]
                can_act, is_stopped, tools_state = send_to_server_user_actions(network, "engineer clicked tool", tool_clicked_cords)

        # draw
        draw_engineer_screen(screen, bg_img_data, is_stopped, tools_state, tools_rects)
        pygame.display.flip()
        clock.tick(FPS)

    network.close()
    pygame.quit()
    sys.exit()


def draw_engineer_screen(screen, bg_img_data, is_stopped, tools_state, tools_rects):
    if is_stopped:
        screen.fill(black)
        message_display(screen, "stop")
        return
    screen.blit(bg_img_data[0], bg_img_data[1])

    for tool in tools_state:
        if tool[1] == "r":
            draw_engineer_tool(screen, red, tools_rects, tool[0])
        elif tool[1] == "y":
            draw_engineer_tool(screen, yellow, tools_rects, tool[0])


def draw_engineer_tool(screen, color, tools_rects, cords):
    pygame.draw.rect(screen, color, tools_rects[cords[0]][cords[1]], 2)



def play_as_radio_operator(network, screen):
    clock = pygame.time.Clock()
    FPS = 60
    screen.fill(blue)
    game_states = "play"

    b_pen_tool = Button(screen_width/5*4, 60, 30, 30, "img/brush.png", True)
    b_eraser_tool = Button(screen_width/5*4+50, 60, 30, 30, "img/eraser.png", False)
    b_select_tool = Button(screen_width/5*4, 110, 30, 30, "img/select2.png", False)
    buttons = [b_pen_tool, b_eraser_tool, b_select_tool]

    drawing_cells_list = []
    selected_tool = 0
    clicking = False
    holding_ctrl = False

    select_tool_start_pos = None
    select_tool_move_start_pos = None
    select_tool_cells_selected = []
    select_tool_rect = None

    bg_img_data = load_bg_img('img/AlphaMap2.jpeg')

    try:
        is_stopped, last_enemy_move_direction = network.send("radio operator get")
    except Exception as e:
        print(e)

    if is_stopped:
        selected_tool = BRUSH
        b_pen_tool.clicked = True

    while game_states != "exit":
        # check for update from server
        got = network.listen(blocking=False)
        if got:
            if got == "sending game state":
                is_stopped, last_enemy_move_direction = network.listen()

        # collect pygame events
        mouse_locations = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_states = "exit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicking = True
                clicked_pos = event.pos
                mouse_locations = mouse_locations.union({clicked_pos})

                if selected_tool == SELECT:
                    if select_tool_rect and select_tool_rect.collidepoint(clicked_pos): # if starting to drug select box
                        select_tool_move_start_pos = clicked_pos
                    else: # starting a new select box
                        select_tool_cells_selected = None
                        select_tool_start_pos = clicked_pos

                for but in buttons:
                    if but.rect.collidepoint(clicked_pos):
                        selected_tool = buttons.index(but)
                        but.clicked = True
                        for other_but in buttons:
                            if other_but != but:
                                other_but.clicked = False

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                clicking = False
                if selected_tool == SELECT and select_tool_rect and select_tool_cells_selected is None:
                    select_tool_cells_selected = [drawing_cell for drawing_cell in drawing_cells_list if
                                                  drawing_cell.rect.colliderect(select_tool_rect)]

            if event.type == pygame.MOUSEMOTION:
                if clicking:
                    mouse_pos = pygame.mouse.get_pos()
                    mouse_locations = mouse_locations.union({mouse_pos})

                    if selected_tool == SELECT:
                        if select_tool_cells_selected is not None: # drugging the select box
                            select_tool_move_end_pos = pygame.mouse.get_pos()
                            dx = select_tool_move_end_pos[0] - select_tool_move_start_pos[0]
                            dy = select_tool_move_end_pos[1] - select_tool_move_start_pos[1]
                            for cell in select_tool_cells_selected:
                                cell.move(dx, dy)
                            select_tool_rect = select_tool_rect.move(dx, dy)
                            select_tool_move_start_pos = select_tool_move_end_pos
                        elif select_tool_start_pos: # drugging to create the select box
                            select_tool_end_pos = pygame.mouse.get_pos()
                            left_top = (min(select_tool_end_pos[0], select_tool_start_pos[0]),
                                        min(select_tool_end_pos[1], select_tool_start_pos[1]))
                            width = abs(select_tool_end_pos[0] - select_tool_start_pos[0])
                            height = abs(select_tool_end_pos[1] - select_tool_start_pos[1])
                            select_tool_rect = pygame.Rect(left_top[0], left_top[1], width, height)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL:
                    holding_ctrl = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL:
                    holding_ctrl = False

                if event.key == pygame.K_SPACE:
                    if holding_ctrl:
                        if select_tool_cells_selected is not None:
                            drawing_cells_list = [drawing_cell for drawing_cell in drawing_cells_list if drawing_cell not in select_tool_cells_selected]
                            select_tool_cells_selected = []
                        # elif select_tool_rect:
                        #     drawing_cells_list = [drawing_cell for drawing_cell in drawing_cells_list if
                        #                           not drawing_cell.rect.colliderect(select_tool_rect)]
                        else:
                            drawing_cells_list = []
        # logic
        if selected_tool != SELECT:
            select_tool_rect = None
            select_tool_cells_selected = None

        if not is_stopped:
            for mouse_pos in mouse_locations:
                if selected_tool == BRUSH:
                    drawing_cells_list.append(DrawingCell(mouse_pos))
                elif selected_tool == ERASER:
                    drawing_cells_list = [drawing_cell for drawing_cell in drawing_cells_list if
                                          not drawing_cell.rect.collidepoint(mouse_pos)]

        # draw
        draw_radio_operator_screen(screen, is_stopped, last_enemy_move_direction, bg_img_data, drawing_cells_list, buttons, selected_tool, select_tool_rect)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

def draw_radio_operator_screen(screen, is_stopped, last_enemy_move_direction, bg_img_data, drawing_cells_list, buttons, selected_tool, select_tool_rect):
    if is_stopped:
        screen.fill(black)
        message_display(screen, "stop")
        return

    screen.blit(bg_img_data[0], bg_img_data[1])

    for cell in drawing_cells_list:
        cell.draw(screen)

    message_display(screen, "Tools", screen_width/5*4, 30, 25)
    message_display(screen, last_enemy_move_direction, screen_width/5*4, 400, 40)
    pygame.draw.rect(screen, (180,180,180), (screen_width/5*4-30, 50, 170, 100))
    for but in buttons:
        but.draw(screen)

    if select_tool_rect:
        pygame.draw.rect(screen, [255, 255, 255], select_tool_rect, 2)


def start_the_game(network, screen, my_pick):
    try:
        my_role = my_pick[1]
        if my_role == CAPTAIN:
            play_as_captain(network, screen)
        elif my_role == FIRST_MATE:
            play_as_first_mate(network, screen)
        elif my_role == ENGINEER:
            play_as_engineer(network, screen)
        elif my_role == RADIO_OPERATOR:
            play_as_radio_operator(network, screen)

    except Exception as e:
        network.close()
        raise e


def load_bg_img(img):
    background_image = pygame.image.load(img)
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    background_image_rect = background_image.get_rect()
    background_image_rect.left, background_image_rect.top = [0, 0]
    return background_image, background_image_rect


def draw_stop_screen(screen):
    screen.fill(black)
    message_display(screen, "stop")


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
