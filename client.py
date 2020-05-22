import math
import sys
import pygame
import pygame_menu

from _thread import start_new_thread
from player import State, CaptainState, FirstMateState, EngineerState, RadioOperatorState
from network import Network
from globals import *



class DrawingCell:
    def __init__(self, pos, color=(128, 30, 30)):
        self.size = 12
        self.color = color
        self.subsurface = pygame.Surface((self.size, self.size))
        self.subsurface.fill(self.color)
        self.pos = (pos[0] - self.size // 2, pos[1] - self.size // 2)
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

class Button:
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
        self.subsurface.blit(self.img, (15, self.height / 3))
        win.blit(pygame.transform.scale(self.img, (22, 22)), (self.pos[0] + 3, self.pos[1] + 2))

class Client:
    FPS = 60
    game_states = "play"
    img_file_name = None

    def __init__(self, screen, network):
        self.screen = screen
        self.network = network
        self.clock = pygame.time.Clock()
        self.state = None
        self.clicked_locations = set()
        self.bg_img_data = self.load_bg_img()

    def play(self):
        # request game state
        self.request_game_state()

        while self.game_states != "exit":
            # check for update from server
            self.listen_for_server_update()

            # collect pygame events
            self.clicked_locations = set()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_states = "exit"

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.clicked_locations.add(event.pos)  # add curr pos to the set
                    print(event.pos)  # debug

            # logic
            if self.state.can_act:
                self.play_turn()

            self.play_outside_of_turn()

            # draw
            if self.state.is_game_stopped:
                self.draw_stop_screen()

            else:
                self.draw()

            pygame.display.flip()
            self.clock.tick(self.FPS)

        self.end_game()

    def update_state(self, state_tuple):
        self.state = state_class_map[self.__class__](*state_tuple)

    def request_game_state(self):
        try:
            self.update_state(self.network.send("get"))
        except Exception as e:
            print(e)

    def listen_for_server_update(self):
        got = self.network.listen(blocking=False)
        if got:
            if got == "sending game state":
                self.update_state(self.network.listen())

    def draw_stop_screen(self):
        self.screen.fill(black)
        self.message_display(self.screen, "stop")

    def send_action_to_server(self, user_action_str, user_action):
        self.network.only_send(user_action_str)
        return self.network.send(user_action)

    def play_turn(self):
        pass

    def play_outside_of_turn(self):
        pass

    def draw(self):
        pass

    def draw_bg_img(self):
        self.screen.blit(self.bg_img_data[0], self.bg_img_data[1])

    def end_game(self):
        self.network.close()
        pygame.quit()
        sys.exit()

    @staticmethod
    def is_rect_clicked(rect, clicked_locations):
        for loc_clicked in clicked_locations:
            if rect.collidepoint(loc_clicked):
                return True
        return False

    @staticmethod
    def detect_rect_clicked(rects_list, clicked_locations):
        for rect in rects_list:
            if Client.is_rect_clicked(rect, clicked_locations):
                return rect

    @staticmethod
    def text_objects(text, font):
        text_surface = font.render(text, True, white)
        return text_surface, text_surface.get_rect()

    def message_display(self, text, x=screen_width / 2, y=screen_height / 2, size=100, font='comicsansms'):
        large_text = pygame.font.SysFont(font, size)
        text_surf, text_rect = Client.text_objects(text, large_text)
        text_rect.center = (x, y)
        self.screen.blit(text_surf, text_rect)

    def load_bg_img(self):
        background_image = pygame.image.load(self.img_file_name)
        background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
        background_image_rect = background_image.get_rect()
        background_image_rect.left, background_image_rect.top = [0, 0]
        return background_image, background_image_rect


class CaptainClient(Client):
    img_file_name = 'img/AlphaMap2.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.stop_button = pygame.Rect(4 * screen_width // 5, screen_height // 2, 150, 150)

    def play_turn(self):
        target_clicked = self.detect_target_clicked()
        if target_clicked:
            self.update_state(self.send_action_to_server("captain clicked loc", target_clicked))

    def play_outside_of_turn(self):
        if not self.state.is_game_stopped and Client.is_rect_clicked(self.stop_button, self.clicked_locations):
            self.update_state(self.network.send("captain stop"))

    def draw(self):
        self.draw_bg_img()

        pygame.draw.rect(self.screen, black, self.stop_button)  # draw button
        self.message_display("stop", self.stop_button.x + self.stop_button.width // 2, self.stop_button.y + self.stop_button.height // 2,
                        self.stop_button.width // 3)

        self.draw_captain_board()

    def detect_target_clicked(self):
        target_clicked = None
        for loc_clicked in self.clicked_locations:
            for i in range(board_height):
                for j in range(board_width):
                    if math.hypot(int(0.0984375 * screen_width + 0.040390625 * screen_width * j) - loc_clicked[0],
                                  int(0.13625 * screen_height + 0.056125 * screen_height * i) - loc_clicked[1]) < int(
                        0.00576923077 * (screen_height + screen_width)):
                        if self.state.board_str[board_height * i + j] == "y":
                            target_clicked = (i, j)
                            break
                else:
                    continue
                break
            else:
                continue
            break
        return target_clicked

    def draw_captain_board(self):
        for i in range(board_height):
            for j in range(board_width):
                c = self.state.board_str[i*board_height + j]
                if c:
                    if c == "r":
                        color = red
                        pygame.draw.circle(self.screen, color, (int(0.0984375 * screen_width + 0.040390625 * screen_width * j), int(0.13625 * screen_height + 0.056125 * screen_height * i)), int(0.00576923077 * (screen_height + screen_width)))
                    elif c == "b":
                        color = black
                        pygame.draw.circle(self.screen, color, (int(0.0984375 * screen_width + 0.040390625 * screen_width * j), int(0.13625 * screen_height + 0.056125 * screen_height * i)), int(0.00576923077 * (screen_height + screen_width)))
                    elif c == "y":
                        color = yellow
                        pygame.draw.circle(self.screen, color, (int(0.0984375 * screen_width + 0.040390625 * screen_width * j), int(0.13625 * screen_height + 0.056125 * screen_height * i)), int(0.00576923077 * (screen_height + screen_width)))


class FirstMateClient(Client):
    img_file_name = 'img/FirstMateCard.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.powers_rects = []
        for i in range(2):
            for j in range(3):
                self.powers_rects.append(pygame.Rect([143 + 394 * j, 173 + 265 * i, 232, 165]))

    def play_turn(self):
        power_clicked = Client.detect_rect_clicked(self.powers_rects[:len(self.state.powers_charges)],
                                                 self.clicked_locations)
        if power_clicked:
            self.update_state(self.send_action_to_server("first mate clicked power", self.powers_rects.index(power_clicked)))
            # power clicked is sent to the server as the index of the power in powerActionsList witch is the same as powers_rects

    def draw(self):
        self.draw_bg_img()
        self.draw_charge_bars()

    def draw_charge_bars(self):
        for power_charge, rect in zip(self.state.powers_charges, self.powers_rects):
            for k in range(power_charge[0]):
                pygame.draw.arc(self.screen, red, rect, math.pi / 2 - ((k + 1) * math.pi / 4), math.pi / 2 - (k * math.pi / 4), 20)

            if self.state.can_act and power_charge[0] < power_charge[1]:
                pygame.draw.arc(self.screen, yellow, rect, math.pi / 2 - ((power_charge[0] + 1) * math.pi / 4), math.pi / 2 - (power_charge[0] * math.pi / 4), 20)


class EngineerClient(Client):
    img_file_name = 'img/EngineerCard.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.tools_rects = [[pygame.Rect([164 + 71 * i + 39 * (i // 3), 418 + j * 76, 60, 50]) for i in range(12)] for j in
                           range(3)]

    def play_turn(self):
        possible_tools_to_break_rects = [self.tools_rects[tool[0][0]][tool[0][1]] for tool in self.state.tools_state if
                                         tool[1] == "y"]
        tool_clicked = Client.detect_rect_clicked(possible_tools_to_break_rects, self.clicked_locations)

        if tool_clicked:
            tool_clicked_cords = \
            [(i, colour.index(tool_clicked)) for i, colour in enumerate(self.tools_rects) if tool_clicked in colour][0]
            self.update_state(self.send_action_to_server("engineer clicked tool", tool_clicked_cords))

    def draw(self):
        self.draw_bg_img()

        for tool in self.state.tools_state:
            if tool[1] == "r":
                self.draw_engineer_tool(red, tool[0])
            elif tool[1] == "y":
                self.draw_engineer_tool(yellow, tool[0])

    def draw_engineer_tool(self, color, cords):
        pygame.draw.rect(self.screen, color, self.tools_rects[cords[0]][cords[1]], 2)


class RadioOperatorClient(Client):
    img_file_name = 'img/AlphaMap2.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        b_pen_tool = Button(screen_width / 5 * 4, 60, 30, 30, "img/brush.png", True)
        b_eraser_tool = Button(screen_width / 5 * 4 + 50, 60, 30, 30, "img/eraser.png", False)
        b_select_tool = Button(screen_width / 5 * 4, 110, 30, 30, "img/select2.png", False)
        self.buttons = [b_pen_tool, b_eraser_tool, b_select_tool]

        self.drawing_cells_list = []
        self.selected_tool = 0
        self.clicking = False
        self.holding_ctrl = False

        self.select_tool_start_pos = None
        self.select_tool_move_start_pos = None
        self.select_tool_cells_selected = []
        self.select_tool_rect = None

    def play(self):
        # request game state
        self.request_game_state()

        while self.game_states != "exit":
            # check for update from server
            self.listen_for_server_update()

            # collect pygame events
            self.clicked_locations = set()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_states = "exit"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mouse_pressed(event)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouse_released()

                elif event.type == pygame.MOUSEMOTION and self.clicking:
                    self.mouse_drug()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LCTRL:
                        self.holding_ctrl = True

                elif event.type == pygame.KEYUP:
                    self.key_pressed(event)

            #logic
            self.play_outside_of_turn()

            # draw
            if self.state.is_game_stopped:
                self.draw_stop_screen()
            else:
                self.draw()

            pygame.display.flip()
            self.clock.tick(self.FPS)

        self.end_game()

    def mouse_pressed(self, event):
        self.clicking = True
        clicked_pos = event.pos
        self.clicked_locations.add(clicked_pos)  # add curr pos to the set

        if self.selected_tool == SELECT:
            if self.select_tool_rect and self.select_tool_rect.collidepoint(
                    clicked_pos):  # if starting to drug select box
                self.select_tool_move_start_pos = clicked_pos
            else:  # starting a new select box
                self.select_tool_cells_selected = None
                self.select_tool_start_pos = clicked_pos

        for but in self.buttons:
            if but.rect.collidepoint(clicked_pos):
                self.selected_tool = self.buttons.index(but)
                but.clicked = True
                for other_but in self.buttons:
                    if other_but != but:
                        other_but.clicked = False

    def mouse_released(self):
        self.clicking = False
        if self.selected_tool == SELECT and self.select_tool_rect and self.select_tool_cells_selected is None:
            self.select_tool_cells_selected = [drawing_cell for drawing_cell in self.drawing_cells_list if
                                          drawing_cell.rect.colliderect(self.select_tool_rect)]

    def mouse_drug(self):
        mouse_pos = pygame.mouse.get_pos()
        self.clicked_locations = self.clicked_locations.union({mouse_pos})

        if self.selected_tool == SELECT:
            if self.select_tool_cells_selected is not None:  # drugging the select box
                self.drug_existing_select_box()
            elif self.select_tool_start_pos:  # drugging to create the select box
                self.drug_to_create_select_box()

    def drug_existing_select_box(self):
        select_tool_move_end_pos = pygame.mouse.get_pos()
        dx = select_tool_move_end_pos[0] - self.select_tool_move_start_pos[0]
        dy = select_tool_move_end_pos[1] - self.select_tool_move_start_pos[1]
        for cell in self.select_tool_cells_selected:
            cell.move(dx, dy)
        self.select_tool_rect = self.select_tool_rect.move(dx, dy)
        self.select_tool_move_start_pos = select_tool_move_end_pos

    def drug_to_create_select_box(self):
        select_tool_end_pos = pygame.mouse.get_pos()
        left_top = (min(select_tool_end_pos[0], self.select_tool_start_pos[0]),
                    min(select_tool_end_pos[1], self.select_tool_start_pos[1]))
        width = abs(select_tool_end_pos[0] - self.select_tool_start_pos[0])
        height = abs(select_tool_end_pos[1] - self.select_tool_start_pos[1])
        self.select_tool_rect = pygame.Rect(left_top[0], left_top[1], width, height)

    def key_pressed(self, event):
        if event.key == pygame.K_LCTRL:
            self.holding_ctrl = False

        if event.key == pygame.K_SPACE:
            if self.holding_ctrl:
                # if there is a select box, only delete the selected drawing cells
                if self.select_tool_cells_selected is not None:
                    self.drawing_cells_list = [drawing_cell for drawing_cell in self.drawing_cells_list if
                                          drawing_cell not in self.select_tool_cells_selected]
                    self.select_tool_cells_selected = []
                else: # if there is no select box delete all drawing cells
                    self.drawing_cells_list = []

    def play_outside_of_turn(self):
        if self.selected_tool != SELECT:
            self.select_tool_rect = None
            self.select_tool_cells_selected = None

        if not self.state.is_game_stopped:
            for mouse_pos in self.clicked_locations:
                if self.selected_tool == BRUSH:
                    self.drawing_cells_list.append(DrawingCell(mouse_pos))
                elif self.selected_tool == ERASER:
                    self.drawing_cells_list = [drawing_cell for drawing_cell in self.drawing_cells_list if
                                          not drawing_cell.rect.collidepoint(mouse_pos)]

    def draw(self):
        self.draw_bg_img()

        for cell in self.drawing_cells_list:
            cell.draw(self.screen)

        self.message_display("Tools", screen_width / 5 * 4, 30, 25)
        self.message_display(self.state.last_enemy_move_direction, screen_width / 5 * 4, 400, 40)
        pygame.draw.rect(self.screen, (180, 180, 180), (screen_width / 5 * 4 - 30, 50, 170, 100))
        for but in self.buttons:
            but.draw(self.screen)

        if self.select_tool_rect:
            pygame.draw.rect(self.screen, [255, 255, 255], self.select_tool_rect, 2)


state_class_map = {
    CaptainClient: CaptainState,
    FirstMateClient: FirstMateState,
    EngineerClient: EngineerState,
    RadioOperatorClient: RadioOperatorState
}


def start_the_game(network, screen, my_pick):
    try:
        my_role = my_pick[1]
        if my_role == CAPTAIN:
            client = CaptainClient(screen, network)
        elif my_role == FIRST_MATE:
            client = FirstMateClient(screen, network)
        elif my_role == ENGINEER:
            client = EngineerClient(screen, network)
        elif my_role == RADIO_OPERATOR:
            client = RadioOperatorClient(screen, network)

        client.play()


    except Exception as e:
        network.close()
        raise e


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
