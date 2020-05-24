import math
import sys
import pygame
import pygame_menu

from player import CaptainState, FirstMateState, EngineerState, RadioOperatorState
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
        self.img = pygame.transform.scale(pygame.image.load(img_name),
                                          (self.width // 4, self.height // 4))
        self.rect = pygame.Rect(posX, posY, width, height)

    def draw(self, win):
        if self.clicked:
            self.subsurface.set_alpha(max_alpha)
        else:
            self.subsurface.set_alpha(max_alpha // 2)

        win.blit(self.subsurface, self.pos)
        self.subsurface.blit(self.img, (15, self.height / 3))
        win.blit(pygame.transform.scale(self.img, (self.width * 3 // 4, self.height * 3 // 4)),
                 (self.pos[0], self.pos[1]))


class PlayerClient:
    """
    Base class representing a player behavior in the client
    Main method `play()` handles the client main loop
    Inheriting classes implements the behavior for specific role
    """
    FPS = 60
    game_states = "play"
    image_filename = None

    def __init__(self, screen, network):
        """
        Instansiates a base client player object
        """
        self.screen = screen
        self.network = network
        self.clock = pygame.time.Clock()
        self.state = None
        self.clicked_locations = set()
        self.background_image = self.load_background_image()

    def play(self):
        """
        The main method of the client player
        Contact sever, draws background and play single turns
        """
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

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == left_mouse_btn:
                    self.mouse_pressed(event)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == left_mouse_btn:
                    self.mouse_released()

                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_drag()

                elif event.type == pygame.KEYDOWN:
                    self.key_pressed(event)

                elif event.type == pygame.KEYUP:
                    self.key_released(event)

            # logic
            if self.state.can_act:
                self.play_turn()
            self.play_outside_of_turn()

            # draw
            if self.state.is_game_stopped:
                self.draw_stop_screen()

            else:
                self.draw_background_image()
                self.draw()

            pygame.display.flip()
            self.clock.tick(self.FPS)

        self.end_game()

    def key_released(self, event):
        """
        Respond to user keyboard key release
        """
        pass

    def key_pressed(self, event):
        """
        Respond to user keyboard key pressed
        """
        pass

    def mouse_drag(self):
        """
        Respond to user mouse drag
        """
        pass

    def mouse_released(self):
        """
        Respond to user mouse button release
        """
        pass

    def mouse_pressed(self, event):
        """
        Respond to user mouse button press
        """
        self.clicked_locations.add(event.pos)  # add curr pos to the set
        print(event.pos)  # TODO: debug

    def update_state(self, state_tuple):
        """
        Gets a tuple of the new state and updates the current state
        """
        self.state = STATE_CLASS_MAP[self.__class__](*state_tuple)

    def request_game_state(self):
        """
        Sends request to the server to get the game state
        Comitted on the beginning of the game
        """
        try:
            self.update_state(self.network.send("get"))
        except Exception as e:
            print(e)

    def listen_for_server_update(self):
        """
        Checks if the server notified about sending an updated game state
        If so, listens until the new game state will be recieved
        """
        got = self.network.listen(blocking=False)
        if got:
            if got == "sending game state":
                self.update_state(self.network.listen())

    def draw_stop_screen(self):
        """
        Draws a black screen for stop mode
        """
        self.screen.fill(black)
        self.display_message("stop")

    def send_action_to_server(self, action_name, action_value):
        """
        Sends action to the server and listens for response
        """
        self.network.only_send(action_name)
        return self.network.send(action_value)

    def play_turn(self):
        """
        This function commits the logic of a single turn
        """
        pass

    def play_outside_of_turn(self):
        """
        This function commits the logic that is done after the turn is finished
        """
        pass

    def draw(self):
        """
        Draws the screen according to the current game state
        """
        pass

    def draw_background_image(self):
        """
        Draws the background image
        """
        self.screen.blit(self.background_image[0], self.background_image[1])

    def end_game(self):
        """
        Ends and closes the game
        """
        self.network.close()
        pygame.quit()
        sys.exit()

    @staticmethod
    def is_rect_clicked(rect, clicked_locations):
        """
        Gets a rectangle and a list of clicked locations
        and returns whether the rectangle was clicked
        """
        for loc_clicked in clicked_locations:
            if rect.collidepoint(loc_clicked):
                return True
        return False

    @staticmethod
    def detect_rect_clicked(rects_list, clicked_locations):
        """
        Gets a list of rectangles and a list of clicked locations
        If one of the rectangles was clicked, returns it
        Otherwise returns None
        """
        for rect in rects_list:
            if PlayerClient.is_rect_clicked(rect, clicked_locations):
                return rect
        return None

    @staticmethod
    def text_objects(text, font):
        """
        Renders a text object
        """
        text_surface = font.render(text, True, white)
        return text_surface, text_surface.get_rect()

    def display_message(self, text, x=screen_width / 2, y=screen_height / 2, size=100,
                        font='comicsansms'):
        """
        Displays message in the given location at the screen
        """
        large_text = pygame.font.SysFont(font, size)
        text_surf, text_rect = PlayerClient.text_objects(text, large_text)
        text_rect.center = (x, y)
        self.screen.blit(text_surf, text_rect)

    def load_background_image(self):
        """
        Loads the background image
        """
        background_image = pygame.image.load(self.image_filename)
        background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
        background_image_rect = background_image.get_rect()
        background_image_rect.left, background_image_rect.top = [0, 0] # top left pos
        return background_image, background_image_rect


class CaptainClient(PlayerClient):
    """
    This class implements all client logic of the Captain player
    """
    image_filename = 'img/AlphaMap2.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.stop_button = pygame.Rect(4 * screen_width // 5,
                                       screen_height // 2,
                                       screen_height // 5,
                                       screen_height // 5)

    def play_turn(self):
        target_clicked = self.detect_target_clicked()
        if target_clicked:
            self.update_state(self.send_action_to_server("captain clicked loc", target_clicked))

    def play_outside_of_turn(self):
        if not self.state.is_game_stopped \
           and PlayerClient.is_rect_clicked(self.stop_button, self.clicked_locations):
            self.update_state(self.network.send("captain stop"))

    def draw(self):
        # draw stop button
        pygame.draw.rect(self.screen, black, self.stop_button)
        self.display_message("stop",
                             self.stop_button.x + self.stop_button.width // 2,
                             self.stop_button.y + self.stop_button.height // 2,
                             self.stop_button.width // 3)

        self.draw_captain_board()

    def detect_target_clicked(self):
        """
        Check if one of the target circles (optional step) was clicked
        If so, return the coordinates of the circle
        Otherwise return None
        """
        for loc_clicked in self.clicked_locations:
            for i in range(board_height):
                for j in range(board_width):
                    if math.hypot(int(0.0984375 * screen_width + 0.040390625 * screen_width * j) \
                                  - loc_clicked[0],
                                  int(0.13625 * screen_height + 0.056125 * screen_height * i) \
                                  - loc_clicked[1]) < \
                                  int(0.00576923077 * (screen_height + screen_width)):
                        if self.state.board_str[board_height * i + j] == "y":
                            return (i, j)
        return None

    def draw_captain_board(self):
        """
        Draws the captain board according to the current state
        """
        for i in range(board_height):
            for j in range(board_width):
                char = self.state.board_str[i * board_height + j]
                circle_params = ((int(0.0984375 * screen_width + 0.040390625 * screen_width * j),
                                  int(0.13625 * screen_height + 0.056125 * screen_height * i)),
                                 int(0.00576923077 * (screen_height + screen_width)))
                if char:
                    if char == "r":
                        color = red
                        pygame.draw.circle(self.screen, color, *circle_params)
                    elif char == "b":
                        color = black
                        pygame.draw.circle(self.screen, color, *circle_params)
                    elif char == "y":
                        color = yellow
                        pygame.draw.circle(self.screen, color, *circle_params)


class FirstMateClient(PlayerClient):
    """
    This class implements all client logic of the First Mate player
    """
    image_filename = 'img/FirstMateCard.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.powers_rects = [pygame.Rect([143 + 394 * j, 173 + 265 * i, 232, 165])
                             for i in range(power_rows)
                             for j in range(power_cols)]

    def play_turn(self):
        power_clicked = PlayerClient.detect_rect_clicked(
                        self.powers_rects[:len(self.state.powers_charges)],
                        self.clicked_locations)

        if power_clicked:
            # power clicked is sent to the server as the index of the power in power_rects
            self.update_state(self.send_action_to_server("first mate clicked power",
                                                         self.powers_rects.index(power_clicked)))

    def draw(self):
        self.draw_charge_bars()

    def draw_charge_bars(self):
        """
        Draws the charge bars of each power of the first mate
        """
        start_angle = math.pi/2
        one_arch_angle = math.pi/4
        arch_border_width = 20
        for power_charge, rect in zip(self.state.powers_charges, self.powers_rects):
            for k in range(power_charge[0]):
                pygame.draw.arc(self.screen, red, rect, start_angle - ((k + 1) * one_arch_angle),
                                start_angle - (k * one_arch_angle), arch_border_width)

            if self.state.can_act and power_charge[0] < power_charge[1]:
                pygame.draw.arc(self.screen, yellow, rect,
                                start_angle - ((power_charge[0] + 1) * one_arch_angle),
                                start_angle - (power_charge[0] * one_arch_angle), arch_border_width)


class EngineerClient(PlayerClient):
    """
    This class implements all client logic of the Engineer player
    """
    image_filename = 'img/EngineerCard.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.tools_rects = [[pygame.Rect([164 + 71 * i + 39 * (i // 3), 418 + j * 76, 60, 50])
                             for i in range(tools_cols)]
                            for j in range(tools_rows)]

    def play_turn(self):
        possible_tools_to_break_rects = [self.tools_rects[tool[0][0]][tool[0][1]]
                                         for tool in self.state.tools_state if tool[1] == "y"]
        tool_clicked = PlayerClient.detect_rect_clicked(possible_tools_to_break_rects,
                                                  self.clicked_locations)

        if tool_clicked:
            tool_clicked_cords = [(i, colour.index(tool_clicked))
                                  for i, colour in enumerate(self.tools_rects)
                                  if tool_clicked in colour][0]
            self.update_state(self.send_action_to_server("engineer clicked tool",
                                                         tool_clicked_cords))

    def draw(self):
        for tool in self.state.tools_state:
            if tool[1] == "r":
                self.draw_engineer_tool(red, tool[0])
            elif tool[1] == "y":
                self.draw_engineer_tool(yellow, tool[0])

    def draw_engineer_tool(self, color, cords):
        """
        Draws a tool of the engineer
        """
        border_width = 2
        pygame.draw.rect(self.screen, color, self.tools_rects[cords[0]][cords[1]], border_width)


class RadioOperatorClient(PlayerClient):
    """
    This class implements all client logic of the Radio Operator player
    """
    image_filename = 'img/AlphaMap2.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        button_size = 30
        b_pen_tool = Button(screen_width / 5 * 4, 60,
                            button_size, button_size, "img/brush.png", True)
        b_eraser_tool = Button(screen_width / 5 * 4 + button_size + 20, 60,
                               button_size, button_size, "img/eraser.png", False)
        b_select_tool = Button(screen_width / 5 * 4, 60 + button_size + 20,
                               button_size, button_size, "img/select2.png", False)
        self.buttons = [b_pen_tool, b_eraser_tool, b_select_tool]

        self.drawing_cells_list = []
        self.selected_tool = 0
        self.clicking = False
        self.holding_ctrl = False

        self.select_tool_start_pos = None
        self.select_tool_move_start_pos = None
        self.select_tool_cells_selected = []
        self.select_tool_rect = None

    def key_pressed(self, event):
        if event.key == pygame.K_LCTRL:
            self.holding_ctrl = True

    def mouse_pressed(self, event):
        self.clicking = True
        clicked_pos = event.pos
        self.clicked_locations.add(clicked_pos)  # add curr pos to the set

        if self.selected_tool == SELECT:
            if self.select_tool_rect and self.select_tool_rect.collidepoint(
                    clicked_pos):  # if starting to drag select box
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
        if self.selected_tool == SELECT and \
           self.select_tool_rect and \
           self.select_tool_cells_selected is None:
            self.select_tool_cells_selected = [drawing_cell
                                               for drawing_cell in self.drawing_cells_list
                                               if drawing_cell.rect.colliderect(
                                                   self.select_tool_rect)]

    def mouse_drag(self):
        if self.clicking:
            mouse_pos = pygame.mouse.get_pos()
            self.clicked_locations = self.clicked_locations.union({mouse_pos})

            if self.selected_tool == SELECT:
                if self.select_tool_cells_selected is not None:  # dragging the select box
                    self.drag_existing_select_box()
                elif self.select_tool_start_pos:  # dragging to create the select box
                    self.drag_to_create_select_box()

    def drag_existing_select_box(self):
        select_tool_move_end_pos = pygame.mouse.get_pos()
        dx = select_tool_move_end_pos[0] - self.select_tool_move_start_pos[0]
        dy = select_tool_move_end_pos[1] - self.select_tool_move_start_pos[1]
        for cell in self.select_tool_cells_selected:
            cell.move(dx, dy)
        self.select_tool_rect = self.select_tool_rect.move(dx, dy)
        self.select_tool_move_start_pos = select_tool_move_end_pos

    def drag_to_create_select_box(self):
        select_tool_end_pos = pygame.mouse.get_pos()
        left_top = (min(select_tool_end_pos[0], self.select_tool_start_pos[0]),
                    min(select_tool_end_pos[1], self.select_tool_start_pos[1]))
        width = abs(select_tool_end_pos[0] - self.select_tool_start_pos[0])
        height = abs(select_tool_end_pos[1] - self.select_tool_start_pos[1])
        self.select_tool_rect = pygame.Rect(left_top[0], left_top[1], width, height)

    def key_released(self, event):
        if event.key == pygame.K_LCTRL:
            self.holding_ctrl = False

        if event.key == pygame.K_SPACE:
            if self.holding_ctrl:
                # if there is a select box, only delete the selected drawing cells
                if self.select_tool_cells_selected is not None:
                    self.drawing_cells_list = [drawing_cell for drawing_cell in \
                                                   self.drawing_cells_list
                                               if drawing_cell not in \
                                                   self.select_tool_cells_selected]
                    self.select_tool_cells_selected = []
                else: # if there is no select box delete all drawing cells
                    self.drawing_cells_list = []

    def play_turn(self):
        if self.selected_tool != SELECT:
            self.select_tool_rect = None
            self.select_tool_cells_selected = None

        if not self.state.is_game_stopped:
            for mouse_pos in self.clicked_locations:
                if self.selected_tool == BRUSH:
                    self.drawing_cells_list.append(DrawingCell(mouse_pos))
                elif self.selected_tool == ERASER:
                    self.drawing_cells_list = [drawing_cell for drawing_cell in \
                                                   self.drawing_cells_list
                                               if not drawing_cell.rect.collidepoint(mouse_pos)]

    def draw(self):
        for cell in self.drawing_cells_list:
            cell.draw(self.screen)

        self.display_message("Tools", screen_width / 5 * 4, 30, 25)
        self.display_message(self.state.last_enemy_move_direction, screen_width / 5 * 4, 400, 40)
        pygame.draw.rect(self.screen, (180, 180, 180), (screen_width / 5 * 4 - 30, 50, 170, 100))
        for but in self.buttons:
            but.draw(self.screen)

        if self.select_tool_rect:
            border_width = 2
            pygame.draw.rect(self.screen, [255, 255, 255], self.select_tool_rect, border_width)


STATE_CLASS_MAP = {
    CaptainClient: CaptainState,
    FirstMateClient: FirstMateState,
    EngineerClient: EngineerState,
    RadioOperatorClient: RadioOperatorState
}


def play_role(network, screen, my_role):
    """
    Starts the player client of the specified role
    """
    try:
        if my_role == CAPTAIN:
            client = CaptainClient(screen, network)
        elif my_role == FIRST_MATE:
            client = FirstMateClient(screen, network)
        elif my_role == ENGINEER:
            client = EngineerClient(screen, network)
        elif my_role == RADIO_OPERATOR:
            client = RadioOperatorClient(screen, network)

        client.play()

    finally:
        network.close()


def pick_team(network, my_pick):
    """
    Sends team & role pick to server, returns True if the pick was accepted
    """
    server_response = network.send(my_pick)
    return server_response == "ok"


def start_game(network, screen, team_selector, role_selector, start_game_menu):
    """
    Responds to main menu Play button
    Validates team & role pick and starts the player client
    """
    my_pick = (my_team, my_role) = team_selector.get_value()[1], role_selector.get_value()[1]

    if pick_team(network, my_pick):  # team & role pick was accepted
        play_role(network, screen, my_role)

    else:
        # role is taken, notify user
        if not start_game_menu.get_widget("role taken"):
            start_game_menu.add_label("role taken", "role taken")


def main():
    """
    The main method of the client
    Operates the main menu and initializes the game logic
    """
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    menu_width, menu_height = 300, 400
    try:
        network = Network()
    except:
        try_again_menu = pygame_menu.Menu(menu_width,
                                          menu_height,
                                          'Cant connect to server',
                                          theme=pygame_menu.themes.THEME_BLUE)
        try_again_menu.add_button('Try again', main)
        try_again_menu.mainloop(screen)

    start_game_menu = pygame_menu.Menu(menu_width,
                                       menu_height,
                                       'Welcome',
                                       theme=pygame_menu.themes.THEME_BLUE)

    team_selector = start_game_menu.add_selector('Team :',
                                                 [('blue', BLUE_TEAM),
                                                  ('yellow', YELLOW_TEAM)])

    role_selector = start_game_menu.add_selector('Role :',
                                                 [('captain', CAPTAIN),
                                                  ('first mate', FIRST_MATE),
                                                  ('engineer', ENGINEER),
                                                  ('radio operator', RADIO_OPERATOR)])

    start_game_menu.add_button('Play',
                               start_game,
                               network,
                               screen,
                               team_selector,
                               role_selector,
                               start_game_menu)

    start_game_menu.add_button('Quit', pygame_menu.events.EXIT)

    start_game_menu.mainloop(screen)

if __name__ == '__main__':
    main()
