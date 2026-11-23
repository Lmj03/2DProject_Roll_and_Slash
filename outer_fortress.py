from pico2d import load_image

from bounding_box import BoundingBox
from collision import _polygon_location


SIZE = 2400, 1100
ENTRY = 172, 300  # World coordinates at the player's feet.
RETURN_AREA = BoundingBox(25, 258, 110, 315)
ENEMY_STARTS = ((771, 510), (1590, 532), (1870, 383))

# Trace the edges at half size for readability. Points follow the art from the
# left path, through the gate in the dividing wall, around the right court.
WALKABLE = tuple((x * 2, y * 2) for x, y in (
    (0, 389), (44, 383), (123, 358), (166, 328), (165, 272),
    (179, 226), (204, 205), (257, 187), (477, 183), (485, 199),
    (489, 333), (496, 351), (517, 366),
    (543, 346), (566, 324), (594, 303),
    (589, 273), (572, 230), (560, 181), (580, 156), (618, 138),
    (897, 132), (951, 142), (982, 173), (1001, 234), (1017, 266),
    (1056, 289), (1127, 322), (1101, 374), (1075, 401), (1016, 429),
    (967, 447), (813, 452), (704, 453), (661, 439),
    (633, 409), (615, 376), (605, 353), (590, 336),
    (568, 351), (549, 368), (553, 389), (568, 420), (582, 449),
    (531, 453), (239, 450), (208, 432), (171, 407), (116, 408),
    (56, 423), (0, 424),
))


def can_walk(x, foot_y):
    inside, near_edge = _polygon_location(x, SIZE[1] - foot_y, WALKABLE)
    return inside and not near_edge


class Background:
    def __init__(self):
        self.image = load_image('asset/maps/stage_01_outer_fortress.png')
        if (self.image.w, self.image.h) != SIZE:
            raise ValueError('The outer fortress map must be 2400 by 1100 pixels.')

    def draw(self, camera):
        left, bottom = camera.origin
        self.image.clip_draw(left, bottom, camera.width, camera.height,
                             camera.width / 2, camera.height / 2)


class GateForeground:
    # The gate lintel and the adjacent wall hide sprites passing beneath them.
    IMAGE_LEFT, IMAGE_TOP = 1030, 470

    def __init__(self):
        self.image = load_image('asset/maps/stage_01_gate_foreground.png')

    def draw(self, camera):
        x = self.IMAGE_LEFT + self.image.w / 2
        y = SIZE[1] - self.IMAGE_TOP - self.image.h / 2
        self.image.draw(*camera.project(x, y))
