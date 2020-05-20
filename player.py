import gameFile
from globals import *
import math

class Player:
    def __init__(self, team, role, submarine):
        self.team = team
        self.role = role
        self.online = True
        self.submarine = submarine

    def disconnected(self):
        self.online = False

    def get_state(self, game):
        pass

    def is_can_act(self):
        pass


class CaptainPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)
        self.submarine.captain = self

    def is_can_act(self):
        return self.submarine.can_move

    def get_board_str(self, game):
        board_str = ""
        for i in range(board_width):
            for j in range(board_height):
                if (i, j) == self.submarine.loc:
                    board_str += "b" # submarine location is marked b for black
                elif (i, j) in self.submarine.path:
                    board_str += "r"  # submarine past locations are marked r for red
                elif self.is_can_act() and gameFile.Game.in_map((i, j)) and not game.board[i][j].is_island and (i, j) not in self.submarine.path and math.hypot(i - self.submarine.loc[0], j - self.submarine.loc[1]) == 1:
                    board_str += "y"  # possible move loc marked y for yellow
                else:
                    board_str += "w" # white for nothing
        return board_str

    def clicked(self, game, target):
        if gameFile.Game.in_map(target) and not game.board[target[0]][target[1]].is_island and target not in self.submarine.path and math.hypot(target[0] - self.submarine.loc[0], target[1] - self.submarine.loc[1]) == 1:
            self.submarine.move(target)

    def get_state(self, game):
        return CaptainState(self, game)


class FirstMatePlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)
        self.submarine.first_mate = self

    def is_can_act(self):
        return not self.submarine.is_first_mate_check

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
            self.submarine.first_mate_check()


class EngineerPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)
        self.submarine.engineer = self

    def is_can_act(self):
        return not self.submarine.is_engineer_check

    def get_state(self, game):
        return EngineerState(self, game)

    def get_tools_state(self):
        tools_state = []
        for tool in self.submarine.tools:
            if tool.is_broken:
                tools_state.append((tool.cords, "r"))
            elif self.is_can_act() and tool.direction == self.submarine.last_move_direction:
                tools_state.append((tool.cords, "y"))
        return tools_state

    def brake_tool(self, tool_to_brake_cords):
        tool_to_brake = None
        for tool in self.submarine.tools:
            if tool.cords == tool_to_brake_cords:
                tool_to_brake = tool
                break
        if tool_to_brake and not tool_to_brake.is_broken and tool_to_brake.direction == self.submarine.last_move_direction:
            self.submarine.brake_tool(tool_to_brake)
            self.submarine.engineer_check()


class State:
    def __init__(self, player, game):
        self.can_act = player.is_can_act()
        self.is_game_stopped = game.is_stopped


class CaptainState(State):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.board_str = player.get_board_str(game)

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from (self.board_str, self.can_act, self.is_game_stopped)


class FirstMateState(State):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.powers_charges = player.get_powers_charges()
        self.hp = player.submarine.hp

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from (self.powers_charges, self.hp, self.can_act, self.is_game_stopped)


class EngineerState(State):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.tools_state = player.get_tools_state()


    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from (self.tools_state, self.can_act, self.is_game_stopped)