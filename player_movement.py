from math import ceil, sqrt

from pico2d import SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT, SDLK_UP


UP, RIGHT, DOWN, LEFT = range(4)
FACING_AXES = {UP: (0, 1), RIGHT: (1, 0), DOWN: (0, -1), LEFT: (-1, 0)}
MOVEMENT_KEYS = frozenset({SDLK_UP, SDLK_RIGHT, SDLK_DOWN, SDLK_LEFT})


def movement_axes(pressed_keys):
    move_x = (SDLK_RIGHT in pressed_keys) - (SDLK_LEFT in pressed_keys)
    move_y = (SDLK_UP in pressed_keys) - (SDLK_DOWN in pressed_keys)
    return move_x, move_y


def move_position(position, axes, distance, *, can_move, foot_offset_y, max_step):
    x, y = position
    move_x, move_y = axes
    # Check the path in small steps so a slow frame cannot skip a wall.
    steps = max(1, ceil(distance / max_step))
    step = distance / steps
    if move_x and move_y:
        step /= sqrt(2)

    for _ in range(steps):
        old_x, old_y = x, y
        next_x = x + move_x * step
        next_y = y + move_y * step
        if can_move is None or can_move(next_x, y - foot_offset_y):
            x = next_x
        if can_move is None or can_move(x, next_y - foot_offset_y):
            y = next_y
        if x == old_x and y == old_y:
            break
    return x, y
