import math
import game_file

EXPLOSION_SIZE = 2
MAX_SILENCE_LENGTH = 4

class Submarine:
    direction_dict = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}

    def __init__(self, team):
        self.mines = []
        self.loc = (0,0)
        self.path = [self.loc]
        self.tools = []
        self.chains = []
        self.hp = 4
        self.team = team
        self.mine_action = PowerAction("mine", "weapon", 3)
        self.torpedo_action = PowerAction("torpedo", "weapon", 3)
        self.drone_action = PowerAction("drone", "intelligence", 4)
        self.sonar_action = PowerAction("sonar", "intelligence", 3)
        self.silence_action = PowerAction("silence", "special", 6)
        self.power_actions_list = [self.mine_action, self.drone_action, self.silence_action, self.torpedo_action, self.sonar_action]
        self.can_move = True
        self.is_first_mate_check = True
        self.is_engineer_check = True
        self.last_move_direction = "0 - NA"
        self.chains = {"yellow": Chain("yellow"), "orange": Chain("orange"), "silver": Chain("silver")}
        self.tools = [Tool("weapon", (0,0), "W", self.chains["yellow"]),
                      Tool("special", (0,1), "W", self.chains["yellow"]),
                      Tool("intelligence", (1,2), "W", self.chains["yellow"]),
                      Tool("intelligence", (2,0), "W"),
                      Tool("radioactive", (2,1), "W"),
                      Tool("radioactive", (2, 2), "W"),
                      Tool("special", (0,3), "N", self.chains["orange"]),
                      Tool("weapon", (1,3), "N", self.chains["orange"]),
                      Tool("special", (1,5), "N", self.chains["orange"]),
                      Tool("radioactive", (2,3), "N"),
                      Tool("weapon", (2,4), "N"),
                      Tool("radioactive", (2,5), "N"),
                      Tool("intelligence", (0,6), "S", self.chains["silver"]),
                      Tool("special", (1,6), "S", self.chains["silver"]),
                      Tool("weapon", (1,8), "S", self.chains["silver"]),
                      Tool("weapon", (2,6), "S"),
                      Tool("radioactive", (2,7), "S"),
                      Tool("special", (2,8), "S"),
                      Tool("intelligence", (0, 9), "E", self.chains["orange"]),
                      Tool("special", (1, 9), "E", self.chains["silver"]),
                      Tool("weapon", (1, 11), "E", self.chains["yellow"]),
                      Tool("radioactive", (2, 9), "E"),
                      Tool("intelligence", (2, 10), "E"),
                      Tool("radioactive", (2, 11), "E")]
        self.surfacing = False

    def move(self, target):
        move_d_row = target[0] - self.loc[0]
        move_d_col = target[1] - self.loc[1]
        for direction_name, direction_cords in self.direction_dict.items():
            if direction_cords == (move_d_row, move_d_col):
                self.last_move_direction = str(int(self.last_move_direction.split(' ')[0]) + 1) + " - " + direction_name
                break
        else:
            print("error in Submarine.move, direction not found")

        self.loc = target
        self.path.append(target)

        self.can_move = False
        self.first_mate_uncheck()
        self.engineer_uncheck()

    def first_mate_uncheck(self):
        self.is_first_mate_check = False

        # if all power action's charges are maxed then the first mate automatically check
        for power_action in self.power_actions_list:
            if power_action.charge != power_action.max_charge:
                break
        else:
            self.is_first_mate_check = True

    def engineer_uncheck(self):
        self.is_engineer_check = False

    def engineer_check(self):
        self.is_engineer_check = True
        if self.is_first_mate_check:
            self.can_move = True

    def first_mate_check(self):
        self.is_first_mate_check = True
        if self.is_engineer_check:
            self.can_move = True

    def brake_tool(self, tool_to_brake):
        tool_to_brake.brake()

        if tool_to_brake.type == "radioactive":
            for tool in self.tools:
                if tool.type == "radioactive" and not tool.is_broken:
                    break
            else: # if all "radioactive" tools are broken
                self.hp -= 1
                self.fix_all_tools()

        for tool in self.tools:
            if tool.direction == tool_to_brake.direction and not tool.is_broken:
                break
        else: # if all tools in the same direction are broken
            self.hp -= 1
            self.fix_all_tools()

    def fix_all_tools(self):
        for tool in self.tools:
            tool.fix()

    def get_enemy_submarine(self, game):
        return [submarine for submarine in game.submarines if submarine is not self][0]

    def can_plant_mine(self, game):
        if self.mine_action.charge != self.mine_action.max_charge:
            return False
        for tool in self.tools:
            if tool.type == "weapon" and tool.is_broken:
                return False
        for direction_cords in self.direction_dict.values():
            new_loc = self.loc[0] + direction_cords[0], self.loc[1] + direction_cords[1]
            if game_file.Game.in_map(new_loc) and not game.board[new_loc[0]][new_loc[1]].is_island and \
                    new_loc not in self.path + self.mines:
                break
        else: # if there are no possible mine locations
            return False
        return True

    def plant_mine(self, target):
        self.mines.append(target)
        self.mine_action.charge = 0

    def can_fire_torpedo(self):
        if self.torpedo_action.charge != self.torpedo_action.max_charge:
            return False
        for tool in self.tools:
            if tool.type == "weapon" and tool.is_broken:
                return False
        return True

    def fire_torpedo(self, game, target):
        old_enemy_hp = self.get_enemy_submarine(game).hp
        self.bomb(game, target)
        self.torpedo_action.charge = 0
        return old_enemy_hp - self.get_enemy_submarine(game).hp

    def bomb(self, game, bomb_cords):
        enemy_submarine = self.get_enemy_submarine(game)
        if self.loc == bomb_cords:
            self.hp = max(self.hp -2, 0)
        elif math.hypot(self.loc[0] - bomb_cords[0], self.loc[1] - bomb_cords[1]) < EXPLOSION_SIZE:
            self.hp = max(self.hp - 1, 0)
        if enemy_submarine.loc == bomb_cords:
            enemy_submarine.hp = max(enemy_submarine.hp -2, 0)
        elif math.hypot(enemy_submarine.loc[0] - bomb_cords[0], enemy_submarine.loc[1] - bomb_cords[1]) < EXPLOSION_SIZE:
            enemy_submarine.hp = max(enemy_submarine.hp - 1, 0)

        mines_in_explosion_size = []
        for mine in self.mines[:]:
            if math.hypot(mine[0] - bomb_cords[0], mine[1] - bomb_cords[1]) < EXPLOSION_SIZE:
                mines_in_explosion_size.append(mine)
                self.mines.remove(mine)

        for mine in enemy_submarine.mines[:]:
            if math.hypot(mine[0] - bomb_cords[0], mine[1] - bomb_cords[1]) < EXPLOSION_SIZE:
                mines_in_explosion_size.append(mine)
                enemy_submarine.mines.remove(mine)

        for mine in mines_in_explosion_size:
            self.bomb(game, mine)

    def can_activate_mine(self):
        if self.mine_action.charge != self.mine_action.max_charge:
            return False
        for tool in self.tools:
            if tool.type == "weapon" and tool.is_broken:
                return False
        if not self.mines:
            return False

        return True

    def activate_mine(self, game, target):
        old_enemy_hp = self.get_enemy_submarine(game).hp
        if target in self.mines:
            self.mines.remove(target)
            self.bomb(game, target)
            self.mine_action.charge = 0
        return old_enemy_hp - self.get_enemy_submarine(game).hp

    def get_possible_silence_cords(self, game):
        possible_silence_cords = []
        for direction_cords in self.direction_dict.values():
            for i in range(MAX_SILENCE_LENGTH):
                curr_cord = direction_cords[0] * (i + 1) + self.loc[0], direction_cords[1] * (i + 1) + self.loc[1]
                if not game.in_map(curr_cord) or game.board[curr_cord[0]][curr_cord[1]].is_island or curr_cord in self.path:
                    break
                possible_silence_cords.append(curr_cord)

        return possible_silence_cords

    def can_silence(self, game):
        if self.silence_action.charge != self.silence_action.max_charge:
            return False
        for tool in self.tools:
            if tool.type == "special" and tool.is_broken:
                return False
        if not self.get_possible_silence_cords(game):
            return False
        return False

    def silence_move_to(self, target):
        direction_cords = (target[0] - self.loc[0]) // max(abs(target[0] - self.loc[0]), 1) ,\
                          (target[1] - self.loc[1]) // max(abs(target[1] - self.loc[1]), 1)

        while self.loc != target:
            self.loc = self.loc[0] + direction_cords[0], self.loc[1] + direction_cords[1]
            self.path.append(self.loc)

        self.last_move_direction = str(int(self.last_move_direction.split(' ')[0]) + 1) + " - Silence"

    def can_drone(self):
        if self.drone_action.charge != self.drone_action.max_charge:
            return False
        for tool in self.tools:
            if tool.type == "intelligence" and tool.is_broken:
                return False
        return False

    def activate_drone(self, game, target_section):
        enemy_loc = self.get_enemy_submarine(game).loc
        return target_section == game.board[enemy_loc[0]][enemy_loc[1]].section

class PowerAction:
    def __init__(self, name, type, max_charge):
        self.type = type
        self.charge = 0
        self.max_charge = max_charge
        self.name = name

    def load(self):
        self.charge = min(self.charge + 1, self.max_charge)

    def can_load(self):
        return self.charge < self.max_charge

class Tool:
    def __init__(self, type, cords, direction, chain=None):
        self.type = type
        self.cords = cords
        self.is_broken = False
        self.chain = chain
        if chain:
            chain.tools.append(self)
        self.direction = direction

    def fix(self):
        self.is_broken = False

    def brake(self):
        self.is_broken = True
        if self.chain:
            self.chain.one_fixed()

class Chain:
    def __init__(self, color):
        self.tools = []
        self.color = color

    def one_fixed(self):
        for tool in self.tools:
            if not tool.is_broken:
                break
        else:
            for tool in self.tools:
                tool.fix()
