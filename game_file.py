import config
import player
import submarine
import time
from common import PlayerRole, Team


class Game:
    def __init__(self):
        self.players = []
        self.submarines = [submarine.Submarine(Team.BLUE), submarine.Submarine(Team.YELLOW)]
        self.board = []
        self.is_stopped = False
        self.power_in_action = None
        for row in range(config.BOARD_HEIGHT):
            curr_row = []
            for col in  range(config.BOARD_WIDTH):
                new_cell = Cell(row,col, self.is_island_in_alpha_map(row, col))
                curr_row.append(new_cell)
            self.board.append(curr_row)

    def add_new_player(self, new_player_team, new_player_role):
        new_player = None
        if new_player_role == PlayerRole.CAPTAIN:
            new_player = player.CaptainPlayer(new_player_team, new_player_role, self.submarines[new_player_team])
        elif new_player_role == PlayerRole.FIRST_MATE:
            new_player = player.FirstMatePlayer(new_player_team, new_player_role, self.submarines[new_player_team])
        elif new_player_role == PlayerRole.ENGINEER:
            new_player = player.EngineerPlayer(new_player_team, new_player_role, self.submarines[new_player_team])
        elif new_player_role == PlayerRole.RADIO_OPERATOR:
            new_player = player.RadioOperatorPlayer(new_player_team, new_player_role, self.submarines[new_player_team])

        self.players.append(new_player)
        return new_player

    @staticmethod
    def is_island_in_alpha_map(row, col):
        return (row, col) in [(1,2), (1,6), (1,12), (1,13), (2,2), (2,8), (2,12), (3,8), (6,1), (7,1), (6,3), (7,3), (8,3), (6,6), (7,6), (8,7), (6,8), (8,11), (8,12), (8,13), (12,0), (10,3), (11,2), (13,2), (14,3), (11,7), (13,6), (13,8), (11,11), (12,12), (13,13)]

    @staticmethod
    def in_map(loc):
        return loc[0] < config.BOARD_HEIGHT and loc[1] < config.BOARD_WIDTH

    @staticmethod
    def reverse_team(team):
        return Team.BLUE if team == Team.YELLOW else Team.YELLOW
class Power:
    def __init__(self, activated_captain, is_need_to_act_captain_show_stop_menu=True,
                 is_need_to_act_captain_can_resume=True):
        self.activated_captain = activated_captain

        self.need_to_act_team = activated_captain.team
        self.is_need_to_act_captain_show_stop_menu = is_need_to_act_captain_show_stop_menu
        self.is_need_to_act_captain_can_resume = is_need_to_act_captain_can_resume
        self.activated_captain_msg = ""
        self.other_captain_msg = "waiting for other captain"

    @staticmethod
    def resume(game):
        game.is_stopped = False


class Surface(Power):
    def __init__(self, activated_captain):
        super().__init__(activated_captain)
        self.surface_section = Cell.get_cords_section(*activated_captain.submarine.path[-1])

        self.activated_captain.submarine.path = [self.activated_captain.submarine.path[-1]]
        self.activated_captain.submarine.fix_all_tools()
        self.activated_captain.submarine.surfacing = time.time()

        self.need_to_act_team = Game.reverse_team(self.need_to_act_team)
        self.is_need_to_act_captain_show_stop_menu = False
        self.is_need_to_act_captain_can_resume = True
        self.activated_captain_msg = "waiting for other captain"
        self.other_captain_msg = f"enemy surface in section {self.surface_section}"



class Cell:
    def __init__(self, row, col, is_island=False):
        self.row = row
        self.col = col
        self.is_island = is_island
        self.mines = []
        self.section = self.get_cords_section(self.row, self.col)

    @staticmethod
    def get_cords_section(row, col):
        return (1+ col % 5) + 3 * (row % 5)