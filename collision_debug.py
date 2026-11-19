from pico2d import draw_rectangle

from bounding_box import BoundingBox
from lobby_map import (
    CAMPFIRE_DAMAGE_RADII, CAMPFIRE_POSITION, CANVAS_HEIGHT, COURTYARD,
    FOOT_RADIUS, FORGE_WALLS, SOLID_ELLIPSES,
)


def _image_bounds(points):
    xs, ys = zip(*points)
    return BoundingBox(min(xs), CANVAS_HEIGHT - max(ys), max(xs), CANVAS_HEIGHT - min(ys))


def _ellipse_bounds(x, y, rx, ry):
    return BoundingBox(x - rx, y - ry, x + rx, y + ry)


def _lobby_collision_boxes():
    # Represent each existing terrain edge/obstacle with an enclosing rectangle.
    edges = zip(COURTYARD, COURTYARD[1:] + COURTYARD[:1])
    bounds = [_image_bounds(edge).expanded(FOOT_RADIUS) for edge in edges]
    bounds.extend(_image_bounds(wall).expanded(FOOT_RADIUS) for wall in FORGE_WALLS)
    bounds.extend(_ellipse_bounds(x, CANVAS_HEIGHT - y, rx, ry).expanded(FOOT_RADIUS)
                  for x, y, rx, ry in SOLID_ELLIPSES)
    bounds.append(_ellipse_bounds(*CAMPFIRE_POSITION, *CAMPFIRE_DAMAGE_RADII))
    return bounds


class CollisionDebug:
    def __init__(self, player, dummy):
        self.player = player
        self.dummy = dummy
        self.lobby_boxes = _lobby_collision_boxes()

    def draw(self):
        renderer = self.player.renderer
        boxes = [*self.lobby_boxes, self.dummy.movement_box, self.dummy.hurtbox,
                 renderer.body_box(self.player), renderer.attack_box(self.player)]
        for box in boxes:
            if box is not None:
                draw_rectangle(box.left, box.bottom, box.right, box.top, 255, 0, 0)
