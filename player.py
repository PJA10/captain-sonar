import gameFile
from globals import *
import math

class Player:
    def __init__(self, team, role, submarine, can_act):
        self.team = team
        self.role = role
        self.online = True
        self.submarine = submarine
        self.can_act = can_act

    def disconnected(self):
        self.online = False


class CaptainPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine, True)


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
            #self.can_act = False
            self.submarine.move(target)

class FirstMatePlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine, False)
        self.powers_charges = []


