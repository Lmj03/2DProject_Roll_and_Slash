from pico2d import load_image

from lobby_map import CAMPFIRE_POSITION


class Campfire:
    CELL_SIZE = 100
    FRAME_COUNT = 4
    FRAME_TIME = 0.12
    DRAW_SIZE = 120
    FOOT_TO_CENTER = 30

    def __init__(self):
        self.x, self.foot_y = CAMPFIRE_POSITION
        self.sheet = load_image('asset/campfire_sheet.png')
        self.elapsed = 0.0

    def update(self, delta_time):
        if delta_time > 0:
            self.elapsed = (self.elapsed + delta_time) % (self.FRAME_COUNT * self.FRAME_TIME)

    def draw(self):
        frame = int((self.elapsed + 1e-9) / self.FRAME_TIME) % self.FRAME_COUNT
        self.sheet.clip_draw(
            frame * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
            self.x, self.foot_y + self.FOOT_TO_CENTER, self.DRAW_SIZE, self.DRAW_SIZE,
        )
