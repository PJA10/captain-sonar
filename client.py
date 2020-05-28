import math
import sys
import pygame
import pygame_menu

from player import CaptainState, FirstMateState, EngineerState, RadioOperatorState
from network import Network
from common import Color, PlayerRole, Team, DrawingTool, ActionType
from config import BOARD_HEIGHT, BOARD_WIDTH


# globals
SCREEN_HEIGHT = 720
SCREEN_WIDTH = 1280

MAX_ALPHA = 255
LEFT_MOUSE_BUTTON = 1

POWER_ROWS = 2
POWER_COLS = 3

TOOL_ROWS = 3
TOOL_COLS = 12

MY_THEME = pygame_menu.themes.THEME_SOLARIZED.copy()
MY_THEME.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD




class DrawingCell:
    """
    This class implements a drawing cell for the radio operator client
    """
    def __init__(self, pos, color=(128, 30, 30)):
        self.size = 12
        self.color = color
        self.subsurface = pygame.Surface((self.size, self.size))
        self.subsurface.fill(self.color)
        self.pos = (pos[0] - self.size // 2, pos[1] - self.size // 2)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)

    def draw(self, win):
        win.blit(self.subsurface, self.pos)

    def move(self, dx, dy):
        """
        Add to the cell pos the given dx, dy
        """
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)


class Button:
    """
    This class implements a button together with it's graphic attributes
    """
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
            self.subsurface.set_alpha(MAX_ALPHA)
        else:
            self.subsurface.set_alpha(MAX_ALPHA // 2)

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

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON:
                    self.mouse_pressed(event)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == LEFT_MOUSE_BUTTON:
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
        self.screen.fill(Color.BLACK)
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
        text_surface = font.render(text, True, Color.WHITE)
        return text_surface, text_surface.get_rect()

    def display_message(self, text, x=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT / 2, size=100,
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
        background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
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
        self.stop_button = pygame.Rect(4 * SCREEN_WIDTH // 5,
                                       SCREEN_HEIGHT // 2,
                                       SCREEN_HEIGHT // 5,
                                       SCREEN_HEIGHT // 5)
        self.resume_button = pygame.Rect(SCREEN_WIDTH // 2,
                                         4 * SCREEN_HEIGHT // 5,
                                         SCREEN_HEIGHT // 6,
                                         SCREEN_HEIGHT // 6)
        self.show_stop_menu_screen = False
        self.stop_screen_menu = pygame_menu.Menu(SCREEN_HEIGHT,
                                            SCREEN_WIDTH,
                                            'Stop',
                                            theme=MY_THEME)
        action_type_selector = self.stop_screen_menu.add_selector('Activate :',
                                                             [('surface', ActionType.SURFACE),
                                                              ('torpedo', ActionType.TORPEDO),
                                                              ('plant mine', ActionType.PLANT_MINE),
                                                              ('activate mine', ActionType.ACTIVATE_MINE),
                                                              ('drone', ActionType.DRONE),
                                                              ('sonar', ActionType.SONAR),
                                                              ('silence', ActionType.SILENCE)])
        self.stop_screen_menu.add_button('submit', self.submit_action_type_clicked, action_type_selector)
        self.stop_screen_menu.add_button('resume', self.resume_game_clicked)


    def play_turn(self):
        target_clicked = self.detect_target_clicked()
        if target_clicked:
            self.update_state(self.send_action_to_server("captain clicked loc", target_clicked))

    def play_outside_of_turn(self):
        if self.state.is_game_stopped:
            self.show_stop_menu_screen = False

        if not self.state.is_game_stopped \
           and PlayerClient.is_rect_clicked(self.stop_button, self.clicked_locations):
            self.update_state(self.network.send("captain stop"))
            self.show_stop_menu_screen = True
        elif self.state.is_game_stopped and PlayerClient.is_rect_clicked(self.resume_button, self.clicked_locations):
            self.resume_game_clicked()



    def draw(self):
        # draw stop button
        pygame.draw.rect(self.screen, Color.BLACK, self.stop_button)
        self.display_message("stop",
                             self.stop_button.x + self.stop_button.width // 2,
                             self.stop_button.y + self.stop_button.height // 2,
                             self.stop_button.width // 3)

        self.draw_captain_board()

    def draw_stop_screen(self):
        if self.show_stop_menu_screen:
            self.stop_screen_menu.enable()
            self.stop_screen_menu.mainloop(self.screen, bgfun=self.update_stop_screen)

        else:
            self.screen.fill(Color.BLACK)
            self.display_message(self.state.msg, size=50)
            if self.state.can_resume:
                pygame.draw.rect(self.screen, Color.BLACK, self.resume_button)
                self.display_message("resume",
                                     self.resume_button.x + self.resume_button.width // 2,
                                     self.resume_button.y + self.resume_button.height // 2,
                                     self.resume_button.width // 3)

    def update_stop_screen(self):
        if not self.state.is_game_stopped:
            self.stop_screen_menu.disable()

    def submit_action_type_clicked(self, action_type_selector):
        action_type_selected = action_type_selector.get_value()[1]
        if action_type_selected == ActionType.SURFACE:
            self.update_state(self.network.send("captain surface"))
            self.stop_screen_menu.disable()

    def resume_game_clicked(self):
        self.update_state(self.network.send("captain resume"))


    def detect_target_clicked(self):
        """
        Check if one of the target circles (optional step) was clicked
        If so, return the coordinates of the circle
        Otherwise return None
        """
        for clicked_x, clicked_y in self.clicked_locations:
            for i in range(BOARD_HEIGHT):
                for j in range(BOARD_WIDTH):
                    # params of the (i, j) circle in the board
                    (circle_x, circle_y), circle_radius = self.get_board_circle_params(i, j)

                    # if clicked location is in the (i, j) circle and the circle is yellow
                    if math.hypot(circle_x - clicked_x, circle_y - clicked_y) < circle_radius:
                        if self.state.board_str[BOARD_HEIGHT * i + j] == "y":
                            return (i, j)
        return None

    def draw_captain_board(self):
        """
        Draws the captain board according to the current state
        """
        for i in range(BOARD_HEIGHT):
            for j in range(BOARD_WIDTH):
                char = self.state.board_str[i * BOARD_HEIGHT + j]
                circle_params = self.get_board_circle_params(i, j)

                if char:
                    if char == "r":
                        color = Color.RED
                        pygame.draw.circle(self.screen, color, *circle_params)
                    elif char == "b":
                        color = Color.BLACK
                        pygame.draw.circle(self.screen, color, *circle_params)
                    elif char == "y":
                        color = Color.YELLOW
                        pygame.draw.circle(self.screen, color, *circle_params)

    @staticmethod
    def get_board_circle_params(i, j):
        """
        Gets grid coordinates i, j and returns circle params of the board circle
        """
        x = int(0.0984375 * SCREEN_WIDTH + 0.040390625 * SCREEN_WIDTH * j)
        y = int(0.13625 * SCREEN_HEIGHT + 0.056125 * SCREEN_HEIGHT * i)
        radius = int(0.00576923077 * (SCREEN_HEIGHT + SCREEN_WIDTH))
        return (x, y), radius


class FirstMateClient(PlayerClient):
    """
    This class implements all client logic of the First Mate player
    """
    image_filename = 'img/FirstMateCard.jpeg'

    def __init__(self, screen, network):
        super().__init__(screen, network)
        self.powers_rects = [pygame.Rect([143 + 394 * j, 173 + 265 * i, 232, 165])
                             for i in range(POWER_ROWS)
                             for j in range(POWER_COLS)]

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
                pygame.draw.arc(self.screen, Color.RED, rect, start_angle - ((k + 1) * one_arch_angle),
                                start_angle - (k * one_arch_angle), arch_border_width)

            if self.state.can_act and power_charge[0] < power_charge[1]:
                pygame.draw.arc(self.screen, Color.YELLOW, rect,
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
                             for i in range(TOOL_COLS)]
                            for j in range(TOOL_ROWS)]

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
                self.draw_engineer_tool(Color.RED, tool[0])
            elif tool[1] == "y":
                self.draw_engineer_tool(Color.YELLOW, tool[0])

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
        b_pen_tool = Button(SCREEN_WIDTH / 5 * 4, 60,
                            button_size, button_size, "img/brush.png", True)
        b_eraser_tool = Button(SCREEN_WIDTH / 5 * 4 + button_size + 20, 60,
                               button_size, button_size, "img/eraser.png", False)
        b_select_tool = Button(SCREEN_WIDTH / 5 * 4, 60 + button_size + 20,
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

        if self.selected_tool == DrawingTool.SELECT:
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
        if self.selected_tool == DrawingTool.SELECT and \
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

            if self.selected_tool == DrawingTool.SELECT:
                if self.select_tool_cells_selected is not None:  # dragging the select box
                    self.drag_existing_select_box()
                elif self.select_tool_start_pos:  # dragging to create the select box
                    self.drag_to_create_select_box()

    def drag_existing_select_box(self):
        """
        Drag the select box on the screen.
        Additionally every drawing cell that was in the select box when it was created will be dragged as will
        """
        select_tool_move_end_pos = pygame.mouse.get_pos()
        dx = select_tool_move_end_pos[0] - self.select_tool_move_start_pos[0]
        dy = select_tool_move_end_pos[1] - self.select_tool_move_start_pos[1]
        for cell in self.select_tool_cells_selected: # move all the selected drawing cells
            cell.move(dx, dy)
        self.select_tool_rect = self.select_tool_rect.move(dx, dy) # move the select box itself
        self.select_tool_move_start_pos = select_tool_move_end_pos

    def drag_to_create_select_box(self):
        """
        Create/resize the select box to be from the mouse position when it was first clicked to the the current mouse position
        """
        select_tool_end_pos = pygame.mouse.get_pos()
        # the top_left_box_position have the minimum x and y between the start and end positions of the current dragging
        top_left_box_position = (min(select_tool_end_pos[0], self.select_tool_start_pos[0]),
                    min(select_tool_end_pos[1], self.select_tool_start_pos[1]))
        
        # the width and height of the box are the difference between the start and end positions of the current dragging
        width = abs(select_tool_end_pos[0] - self.select_tool_start_pos[0])
        height = abs(select_tool_end_pos[1] - self.select_tool_start_pos[1])
        self.select_tool_rect = pygame.Rect(top_left_box_position[0], top_left_box_position[1], width, height)

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
        if self.selected_tool != DrawingTool.SELECT:
            self.select_tool_rect = None
            self.select_tool_cells_selected = None

        if not self.state.is_game_stopped:
            for mouse_pos in self.clicked_locations:
                if self.selected_tool == DrawingTool.BRUSH:
                    self.drawing_cells_list.append(DrawingCell(mouse_pos))
                elif self.selected_tool == DrawingTool.ERASER:
                    self.drawing_cells_list = [drawing_cell for drawing_cell in \
                                                   self.drawing_cells_list
                                               if not drawing_cell.rect.collidepoint(mouse_pos)]

    def draw(self):
        for cell in self.drawing_cells_list:
            cell.draw(self.screen)

        self.display_message("Tools", SCREEN_WIDTH / 5 * 4, 30, 25)
        self.display_message(self.state.last_enemy_move_direction, SCREEN_WIDTH / 5 * 4, 400, 40)
        pygame.draw.rect(self.screen, (180, 180, 180), (SCREEN_WIDTH / 5 * 4 - 30, 50, 170, 100))
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
        if my_role == PlayerRole.CAPTAIN:
            client = CaptainClient(screen, network)
        elif my_role == PlayerRole.FIRST_MATE:
            client = FirstMateClient(screen, network)
        elif my_role == PlayerRole.ENGINEER:
            client = EngineerClient(screen, network)
        elif my_role == PlayerRole.RADIO_OPERATOR:
            client = RadioOperatorClient(screen, network)

        client.play()

    except Exception as e:
        raise e

    finally:
        network.close()
        pygame.quit()


def start_game(network, screen, team_selector, role_selector, start_game_menu):
    """
    Starts the game.
    Sends team & role pick to server,
    Initializes the player client if role approved
    """
    role_pick = (my_team, my_role) = team_selector.get_value()[1], role_selector.get_value()[1]

    # send role pick to the server
    server_response = network.send(role_pick)

    if server_response == "role accepted":   # role was accepted, play as the role
        play_role(network, screen, my_role)

    elif server_response == "role taken":    # role is taken, notify user
        if not start_game_menu.get_widget("role taken"):
            start_game_menu.add_label("role taken", "role taken")


def main():
    """
    The main method of the client
    Operates the main menu and initializes the game logic
    """
    pygame.init()
    logo_file = 'img/captain_sonar_logo.png'
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    icon_image = pygame.transform.scale(pygame.image.load(logo_file), (32, 32))
    pygame.display.set_icon(icon_image)

    try:
        network = Network()
    except:
        try_again_menu = pygame_menu.Menu(SCREEN_HEIGHT,
                                          SCREEN_WIDTH,
                                          'Cant connect to server',
                                          theme=MY_THEME)
        try_again_menu.add_button('Try again', main)
        try_again_menu.mainloop(screen)

    start_game_menu = pygame_menu.Menu(SCREEN_HEIGHT,
                                       SCREEN_WIDTH,
                                       'Welcome',
                                       theme=MY_THEME)
    start_game_menu.add_image(logo_file, scale=(0.8, 0.8), margin=(0,50))
    team_selector = start_game_menu.add_selector('Team :',
                                                 [('blue', Team.BLUE),
                                                  ('yellow', Team.YELLOW)])

    role_selector = start_game_menu.add_selector('Role :',
                                                 [('captain', PlayerRole.CAPTAIN),
                                                  ('first mate', PlayerRole.FIRST_MATE),
                                                  ('engineer', PlayerRole.ENGINEER),
                                                  ('radio operator', PlayerRole.RADIO_OPERATOR)])

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
