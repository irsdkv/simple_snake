import enum
import math
import copy
from typing import List, Dict


class Position:
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y
        self._x_init = x
        self._y_init = y

    def __iter__(self):
        return iter((self._x, self._y))

    def __str__(self):
        return str(self._x) + ", " + str(self._y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):
        return self.x < other.x and self.y < other.y

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __mod__(self, other):
        return Position(self.x % other.x, self.y % other.y)

    def tolist(self):
        return [self.x, self.y]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y

    def move(self, x=0, y=0, angle_rad=None, from_initial=True):
        if not from_initial:
            self._x += x
            self._y += y
        else:
            self._x = self._x_init + x
            self._y = self._y_init + y
        if angle_rad:
            self.rotate(angle_rad, from_initial)

    def rotate(self, angle_rad: float, from_initial=True):
        if not from_initial:
            self.x, self.y = self.rotate_z(self.x, self.y, angle_rad)
        else:
            self.x, self.y = self.rotate_z(self._x_init, self._y_init, angle_rad)

    @staticmethod
    def rotate_z(x, y, angle, center=(0, 0, 0)):
        cx, cy, cz = center
        x = x - cx
        y = y - cy
        d = math.hypot(y, x)
        theta = math.atan2(y, x) + angle
        x = cx + d * math.cos(theta)
        y = cy + d * math.sin(theta)
        return round(x), round(y)


class Direction(enum.IntEnum):
    UP = 0,
    DOWN = 1,
    LEFT = 2,
    RIGHT = 3

    @staticmethod
    def increments(direction=None):
        if direction is None:
            return {Direction.UP: Position(0, 1), Direction.DOWN: Position(0, -1),
                    Direction.LEFT: Position(-1, 0), Direction.RIGHT: Position(1, 0)}

        if direction == Direction.UP:
            return Position(0, 1)
        if direction == Direction.DOWN:
            return Position(0, -1)
        if direction == Direction.LEFT:
            return Position(-1, 0)
        if direction == Direction.RIGHT:
            return Position(1, 0)

        raise Exception("invalid argument")


class SnakeBody:
    SPAWN_DEFAULT = [Position(10, 8), Position(10, 7), Position(10, 6), Position(10, 5), Position(10, 4)]

    def __init__(self, self_bite_callback_, x_max=25, y_max=25, spawn_direction=Direction.UP, transparent_walls=True,
                 wall_bite_callback=None):
        self._max = Position(x_max, y_max)
        self._is_wall_impenetrable = not transparent_walls
        self._body: List[Position] = []
        self._turns: Dict[Position, Direction] = {}
        self._fed_poses: List[Position] = []
        self._turned = False
        self._spawn_direction = spawn_direction
        self._tail_direction: Direction = self._spawn_direction
        self._head_direction: Direction = self._spawn_direction
        self._self_bite_callback = self_bite_callback_
        self._wall_bite_callback = wall_bite_callback

    def turn(self, direction: Direction):
        if self._head_direction == direction:
            return
        if self._head_direction == Direction.UP and direction == Direction.DOWN:
            return
        if self._head_direction == Direction.RIGHT and direction == Direction.LEFT:
            return
        if self._head_direction == Direction.DOWN and direction == Direction.UP:
            return
        if self._head_direction == Direction.LEFT and direction == Direction.RIGHT:
            return
        self._turns[self._body[0]] = direction

    @property
    def body(self) -> List[Position]:
        return self._body

    @property
    def transparent_walls(self):
        return not self._is_wall_impenetrable

    @transparent_walls.setter
    def transparent_walls(self, transparent_walls):
        self._is_wall_impenetrable = not transparent_walls

    def body_list(self):
        list_ = []
        for segment in self._body:
            list_.append(segment.tolist())
        return list_

    def move(self):
        if self._body[-1] in self._fed_poses:
            self._fed_poses.pop(self._fed_poses.index(self._body[-1]))
            tail_inc = self._body[-1] - Direction.increments()[self._tail_direction]
            self._body.append(tail_inc)

        current_direction = self._tail_direction
        for idx, segment in enumerate(reversed(self._body)):
            if segment in self._turns.keys():
                current_direction = self._turns[segment]

                if segment == self._body[-1]:
                    self._tail_direction = self._turns.pop(segment)

            segment_updated = segment + Direction.increments()[current_direction]

            if not self._is_wall_impenetrable:
                segment_updated = segment_updated % self._max
            elif not (segment_updated < self._max) or \
                    segment_updated < Position(self._max.x, 0) or \
                    segment_updated < Position(0, self._max.y):
                self._wall_bite_callback(self, segment_updated)
                return

            if idx == (len(self._body) - 1) and segment_updated in self._body:
                self._self_bite_callback(self, segment_updated)
                return

            self._body[-1-idx] = segment_updated

        self._head_direction = current_direction

    def feed(self):
        self._fed_poses.append(self._body[0])

    def spawn(self, initial_points=None, initial_direction=None):
        if initial_direction is None:
            initial_direction = self._spawn_direction
        else:
            self._spawn_direction = initial_direction
        if initial_points is None:
            initial_points = self.SPAWN_DEFAULT
        self._body = copy.copy(initial_points)
        self._turns = {}
        self._tail_direction = initial_direction
        self._head_direction = initial_direction
        self._fed_poses = []

    @property
    def head(self):
        return self._body[0]
