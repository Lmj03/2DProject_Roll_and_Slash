from dataclasses import dataclass
from math import cos, exp, sin, tau


class ScreenShake:
    def __init__(self):
        self.remaining = 0.0
        self._duration = 0.0
        self._strength = 0
        self._direction = (1, 0)

    def start(self, direction, strength, duration):
        self._direction = direction
        self._strength = strength
        self._duration = self.remaining = duration

    def update(self, delta_time):
        self.remaining = max(0.0, self.remaining - delta_time)

    def reset(self):
        self.remaining = 0.0

    @property
    def offset(self):
        if self.remaining <= 0:
            return (0, 0)
        fraction = self.remaining / self._duration
        phase = tau * 2.5 * (1.0 - fraction)
        along = self._strength * fraction * cos(phase)
        across = self._strength * fraction * 0.35 * sin(phase)
        dx, dy = self._direction
        return round(dx * along - dy * across), round(dy * along + dx * across)


@dataclass(frozen=True)
class RenderView:
    width: int
    height: int
    origin: tuple[int, int] = (0, 0)
    offset: tuple[int, int] = (0, 0)

    def project(self, x, y):
        left, bottom = self.origin
        dx, dy = self.offset
        return x - left + dx, y - bottom + dy


class Camera:
    def __init__(self, view_size, world_size):
        self.width, self.height = view_size
        self.max_x = max(0, world_size[0] - self.width)
        self.max_y = max(0, world_size[1] - self.height)
        self.x = self.y = 0.0

    @property
    def origin(self):
        return round(self.x), round(self.y)

    def follow(self, x, y, delta_time=0, *, snap=False):
        target_x = min(max(0, x - self.width / 2), self.max_x)
        target_y = min(max(0, y - self.height / 2), self.max_y)
        blend = 1.0 if snap else 1.0 - exp(-12 * delta_time)
        self.x += (target_x - self.x) * blend
        self.y += (target_y - self.y) * blend

    def project(self, x, y):
        left, bottom = self.origin
        return x - left, y - bottom
