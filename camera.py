from math import exp


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
