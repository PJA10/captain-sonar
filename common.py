from enum import IntEnum

class Color:
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    RED = (255,0,0)
    YELLOW = (255,255,0)

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
