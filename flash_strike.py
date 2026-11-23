from dataclasses import dataclass
from math import atan2, ceil, hypot

from bounding_box import BoundingBox


@dataclass(frozen=True)
class FlashPath:
    start: tuple
    end: tuple
    half_width: float

    @property
    def length(self):
        return hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])

    @property
    def angle(self):
        return atan2(self.end[1] - self.start[1], self.end[0] - self.start[0])

    @property
    def center(self):
        return ((self.start[0] + self.end[0]) / 2, (self.start[1] + self.end[1]) / 2)

    def attack_box(self):
        x0, y0 = self.start
        x1, y1 = self.end
        if x0 != x1:
            return BoundingBox(min(x0, x1), y0 - self.half_width, max(x0, x1), y0 + self.half_width)
        if y0 != y1:
            return BoundingBox(x0 - self.half_width, min(y0, y1), x0 + self.half_width, max(y0, y1))
        return None


def find_flash_landing(position, axes, distance, *, can_travel, can_land, foot_offset_y):
    """Follow a cardinal line through targets until terrain blocks it, then land on clear ground."""
    x, y = position
    dx, dy = axes
    landing = position
    steps = max(1, ceil(distance / 4))
    for i in range(1, steps + 1):
        travel = i * distance / steps
        next_x, next_y = x + dx * travel, y + dy * travel
        feet = next_y - foot_offset_y
        if can_travel is not None and not can_travel(next_x, feet):
            break
        if can_land(next_x, feet):
            landing = next_x, next_y
    return landing
