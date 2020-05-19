import gameFile
from globals import *
import math

class Player:
    def __init__(self, team, role, submarine, can_act=False):
        self.team = team
        self.role = role
        self.online = True
        self.submarine = submarine
        self.can_act = can_act

    def disconnected(self):
        self.online = False

    def get_state(self, game):
        pass


class CaptainPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine, True)
        self.submarine.captain = self

    def get_board_str(self, game):
        board_str = ""
        for i in range(board_width):
            for j in range(board_height):
                if (i, j) == self.submarine.loc:
                    board_str += "b" # submarine location is marked b for black
                elif (i, j) in self.submarine.path:
                    board_str += "r"  # submarine past locations are marked r for red
                elif self.can_act and gameFile.Game.in_map((i, j)) and not game.board[i][j].is_island and (i, j) not in self.submarine.path and math.hypot(i - self.submarine.loc[0], j - self.submarine.loc[1]) == 1:
                    board_str += "y"  # possible move loc marked y for yellow
                else:
                    board_str += "w" # white for nothing
        return board_str

    def clicked(self, game, target):
        if gameFile.Game.in_map(target) and not game.board[target[0]][target[1]].is_island and target not in self.submarine.path and math.hypot(target[0] - self.submarine.loc[0], target[1] - self.submarine.loc[1]) == 1:
            self.can_act = False
            self.submarine.move(target)
            self.submarine.first_mate.can_act = True

    def get_state(self, game):
        return CaptainState(self, game)


class FirstMatePlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine, False)
        self.submarine.first_mate = self

    def get_powers_charges(self):
        powers_charges = []
        for powerAction in self.submarine.powerActionsList:
            powers_charges.append((powerAction.charge, powerAction.max_charge))

        return powers_charges

    def get_state(self, game):
        return FirstMateState(self, game)

    def load_power(self, power_clicked_index):
        if self.submarine.powerActionsList[power_clicked_index].can_load():
            self.submarine.powerActionsList[power_clicked_index].load()
            self.can_act = False
            self.submarine.captain.can_act = True


class CaptainState:
    def __init__(self, player, game):
        self.board_str = player.get_board_str(game)
        self.can_act = player.can_act
        self.is_game_stopped = game.is_stopped

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from (self.board_str, self.can_act, self.is_game_stopped)


class FirstMateState:
    def __init__(self, player, game):
        self.powers_charges = player.get_powers_charges()
        self.hp = player.submarine.hp
        self.can_act = player.can_act
        self.is_game_stopped = game.is_stopped

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from (self.powers_charges, self.hp, self.can_act, self.is_game_stopped)