from enum import IntEnum


class ActionType:
    SURFACE = 0
    TORPEDO = 1
    PLANT_MINE = 2
    ACTIVATE_MINE = 3
    DRONE = 4
    SONAR = 5
    SILENCE = 6
    MAP = [('surface', SURFACE),
           ('torpedo', TORPEDO),
           ('plant mine', PLANT_MINE),
           ('activate mine', ACTIVATE_MINE),
           ('drone', DRONE),
           ('sonar', SONAR),
           ('silence', SILENCE)]

class Color:
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    RED = (255,0,0)
    YELLOW = (255,255,0)
    GREEN = (0,255,0)

class PlayerRole(IntEnum):
    CAPTAIN = 0
    FIRST_MATE = 1
    ENGINEER = 2
    RADIO_OPERATOR = 3

class Team(IntEnum):
    BLUE = 0
    YELLOW = 1

class DrawingTool(IntEnum):
    BRUSH = 0
    ERASER = 1
    SELECT = 2

