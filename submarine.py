from globals import *

class Submarine:
    def __init__(self, team):
        self.mine_charge, self.torpedo_charge, self.sonar_charge, self.drone_charge, self.silance_charnge = \
            0, 0, 0, 0, 0
        self.mines = []
        self.loc = (0,0)
        self.path = [self.loc]
        self.tools = []
        self.chains = []
        self.hp = 4
        self.team = team
        self.mineAction = PowerAction("mine", "weapon", 3)
        self.torpedoAction = PowerAction("torpedo", "weapon", 3)
        self.droneAction = PowerAction("drone", "intelligence", 4)
        self.sonarAction = PowerAction("sonar", "intelligence", 3)
        self.silenceAction = PowerAction("silence", "special", 6)
        self.powerActionsList = [self.mineAction, self.droneAction, self.silenceAction, self.torpedoAction, self.sonarAction]
        self.can_move = True
        self.is_first_mate_check = True
        self.is_engineer_check = True
        self.last_move_direction = "NA"
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

    def move(self, target):
        move_d_row = target[0] - self.loc[0]
        move_d_col = target[1] - self.loc[1]
        for direction_name, direction_cords in direction_dict.items():
            if direction_cords == (move_d_row, move_d_col):
                self.last_move_direction = direction_name
                break
        else:
            print("error in Submarine.move, direction not found")

        self.loc = target
        self.path.append(target)

        self.can_move = False
        self.is_first_mate_check = False
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