

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

    def move(self, game, target):
        self.loc = target
        self.path.append(target)
        if len(self.path) == 4:
            game.stopped = True
