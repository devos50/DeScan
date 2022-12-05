"""
This module contains the implementation of a Skip Graph.
Paper: https://dl.acm.org/doi/pdf/10.1145/1290672.1290674
"""
from enum import IntEnum


class Direction(IntEnum):
    LEFT = 0
    RIGHT = 1


LEFT = Direction.LEFT
RIGHT = Direction.RIGHT
