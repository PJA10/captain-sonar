import math
import time
import config
from game_file import Game, PlantMine


class Player:
    def __init__(self, team, role, submarine):
        self.team = team
        self.role = role
        self.online = True
        self.submarine = submarine

    def disconnected(self):
        self.online = False

    def clicked(self, game, target):
        pass

    def get_state(self, game):
        pass

    def can_act(self, game):
        pass


class CaptainPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)

    def can_act(self, game):
        return self.submarine.can_move or (game.power_in_action and game.power_in_action.need_to_act_team == self.team
                                           and game.power_in_action.is_need_to_act_captain_show_board)

    def get_board_string(self, game):
        board_str = ""
        for i in range(config.BOARD_WIDTH):
            for j in range(config.BOARD_HEIGHT):
                if (i, j) == self.submarine.loc:
                    board_str += "b" # submarine location is marked b for black
                elif (i, j) in self.submarine.path:
                    board_str += "r"  # submarine past locations are marked r for red
                elif (i, j) in self.submarine.mines:
                    board_str += "g"  # submarine mines are marked g for green
                elif self.can_act(game) and Game.in_map((i, j)) and not game.board[i][j].is_island and (i, j) not in self.submarine.path and math.hypot(i - self.submarine.loc[0], j - self.submarine.loc[1]) == 1:
                    board_str += "y"  # possible move loc marked y for yellow
                else:
                    board_str += "w" # white for nothing
        return board_str

    def clicked(self, game, target):
        if game.power_in_action and game.power_in_action.need_to_act_team == self.team and \
                game.power_in_action.is_need_to_act_captain_show_board:
            game.power_in_action.board_target_clicked(game, target)
        else:
            self.move_submarine_to(game, target)

    def move_submarine_to(self, game, target):
        if Game.in_map(target) and not game.board[target[0]][target[1]].is_island and target not in self.submarine.path + self.submarine.mines and math.hypot(target[0] - self.submarine.loc[0], target[1] - self.submarine.loc[1]) == 1:
            self.submarine.move(target)

    def get_state(self, game):
        return CaptainState.from_player(self, game)




class FirstMatePlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)

    def can_act(self, game):
        return not self.submarine.is_first_mate_check

    def get_powers_charges(self):
        powers_charges = []
        for power_action in self.submarine.power_actions_list:
            powers_charges.append((power_action.charge, power_action.max_charge))
        return powers_charges

    def clicked(self, game, power_clicked_index):
        self.load_power(power_clicked_index)

    def get_state(self, game):
        return FirstMateState.from_player(self, game)

    def load_power(self, power_clicked_index):
        if self.submarine.power_actions_list[power_clicked_index].can_load():
            self.submarine.power_actions_list[power_clicked_index].load()
            self.submarine.first_mate_check()


class EngineerPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)

    def can_act(self, game):
        return not self.submarine.is_engineer_check

    def get_state(self, game):
        return EngineerState.from_player(self, game)

    def get_tools_state(self, game):
        tools_state = []
        for tool in self.submarine.tools:
            if tool.is_broken:
                tools_state.append((tool.cords, "r"))
            elif self.can_act(game) and tool.direction == self.submarine.last_move_direction:
                tools_state.append((tool.cords, "y"))
        return tools_state

    def clicked(self, game, tool_to_brake_cords):
        self.brake_tool(tool_to_brake_cords)

    def brake_tool(self, tool_to_brake_cords):
        tool_to_brake = None
        for tool in self.submarine.tools:
            if tool.cords == tool_to_brake_cords:
                tool_to_brake = tool
                break
        if tool_to_brake and not tool_to_brake.is_broken and tool_to_brake.direction == self.submarine.last_move_direction:
            self.submarine.brake_tool(tool_to_brake)
            self.submarine.engineer_check()


class RadioOperatorPlayer(Player):
    def __init__(self, team, role, submarine):
        super().__init__(team, role, submarine)
        self.submarine.engineer = self

    def can_act(self, game):
        return True

    def get_state(self, game):
        return RadioOperatorState.from_player(self, game)


class State:
    def __init__(self, can_act, is_game_stopped):
        self.can_act = can_act
        self.is_game_stopped = is_game_stopped

    @classmethod
    def from_player(cls, player, game):
        return cls(player.can_act(game), game.is_stopped or bool(player.submarine.surfacing))

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __iter__(self):
        yield from self.__dict__.values()


class CaptainState(State):
    def __init__(self, can_act, is_game_stopped, board_str, power_in_action=None):
        super().__init__(can_act, is_game_stopped)
        self.board_str = board_str
        self.power_in_action = power_in_action

    @classmethod
    def from_player(cls, player, game):
        state = State.from_player(player, game)
        return cls(state.can_act, state.is_game_stopped, player.get_board_string(game), game.power_in_action)


class FirstMateState(State):
    def __init__(self, can_act, is_game_stopped, powers_charges, hp):
        super().__init__(can_act, is_game_stopped)
        self.powers_charges = powers_charges
        self.hp = hp

    @classmethod
    def from_player(cls, player, game):
        state = State.from_player(player, game)
        return cls(state.can_act, state.is_game_stopped, player.get_powers_charges(), player.submarine.hp)


class EngineerState(State):
    def __init__(self, can_act, is_game_stopped, tools_state):
        super().__init__(can_act, is_game_stopped)
        self.tools_state = tools_state

    @classmethod
    def from_player(cls, player, game):
        state = State.from_player(player, game)
        return cls(state.can_act, state.is_game_stopped, player.get_tools_state(game))
    

class RadioOperatorState(State):
    def __init__(self, can_act, is_game_stopped, last_enemy_move_direction):
        super().__init__(can_act, is_game_stopped)
        self.last_enemy_move_direction = last_enemy_move_direction

    @classmethod
    def from_player(cls, player, game):
        state = State.from_player(player, game)
        enemy_submarine = player.submarine.get_enemy_submarine(game)
        last_enemy_move_direction = f"{len(enemy_submarine.path)}. " + enemy_submarine.last_move_direction
        return cls(state.can_act, state.is_game_stopped, last_enemy_move_direction)
