

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
        self.mineAction = PowerAction("weapon", 3)
        self.torpedoAction = PowerAction("weapon", 3)
        self.droneAction = PowerAction("intelligence", 4)
        self.sonarAction = PowerAction("intelligence", 3)
        self.silenceAction = PowerAction("special", 6)
        self.powerActionsList = [self.mineAction, self.droneAction, self.silenceAction, self.torpedoAction, self.sonarAction]
        self.captain = None
        self.first_mate = None

    def move(self, target):
        self.loc = target
        self.path.append(target)

class PowerAction:
    def __init__(self, type, max_charge):
        self.type = type
        self.charge = 0
        self.max_charge = max_charge

    def load(self):
        self.charge = min(self.charge + 1, self.max_charge)

    def can_load(self):
        return self.charge < self.max_charge