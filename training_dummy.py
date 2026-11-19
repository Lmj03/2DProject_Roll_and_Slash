from pico2d import load_image

from bounding_box import BoundingBox
from lobby_map import FOOT_RADIUS, TRAINING_DUMMY_POSITION


class TrainingDummy:
    CELL_SIZE = 100
    DRAW_SIZE = 110
    FEET_TO_CENTER = 37
    HIT_FRAME_TIME = 0.08
    HIT_FRAME_COUNT = 3

    def __init__(self):
        self.x, self.foot_y = TRAINING_DUMMY_POSITION
        self.sheet = load_image('asset/training_dummy_sheet.png')
        footprint = BoundingBox(self.x - 15, self.foot_y - 8,
                               self.x + 15, self.foot_y + 8)
        self.hurtbox = BoundingBox(self.x - 24, self.foot_y + 7,
                                   self.x + 24, self.foot_y + 82)
        self.movement_box = footprint.expanded(FOOT_RADIUS)
        self._hit_time = None

    def blocks(self, x, foot_y):
        return self.movement_box.contains(x, foot_y)

    def receive_hit(self):
        self._hit_time = 0.0

    def update(self, delta_time):
        if self._hit_time is not None:
            self._hit_time += delta_time
            if self._hit_time >= self.HIT_FRAME_TIME * self.HIT_FRAME_COUNT:
                self._hit_time = None

    def draw(self):
        frame = 0 if self._hit_time is None else 1 + int(self._hit_time / self.HIT_FRAME_TIME)
        self.sheet.clip_draw(frame * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
                             self.x, self.foot_y + self.FEET_TO_CENTER, self.DRAW_SIZE, self.DRAW_SIZE)
