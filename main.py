import time

from pico2d import *
import game_world
import Player
import key_handle_events

CANVAS_WIDTH, CANVAS_HEIGHT = 1500, 700
FOOT_RADIUS = 9
TARGET_FPS = 60
ANVIL_FOOTPRINT = (307, 431, 30, 19)

# Collision shapes use the lobby image's top-left coordinate system.
COURTYARD = (
    (0, 248), (650, 248), (660, 190), (840, 190), (850, 248),
    (1128, 248), (1215, 282), (1380, 295), (1462, 320), (1462, 374),
    (1405, 443), (1368, 492), (1310, 561), (1248, 618),
    (881, 618), (862, 694), (637, 694), (618, 618),
    (237, 618), (175, 562), (100, 538), (0, 482),
)
FORGE_WALLS = (
    ((0, 238), (171, 238), (181, 479), (175, 514), (143, 532), (0, 455)),
    ((161, 238), (411, 238), (419, 378), (406, 395), (383, 406),
     (357, 388), (357, 372), (211, 440), (176, 463)),
)
# Center x, center y, horizontal radius, vertical radius.
SOLID_ELLIPSES = (
    (1095, 384, 149, 94),  # Well
    ANVIL_FOOTPRINT,       # Anvil stand
    (197, 485, 18, 24),    # Barrel by the forge entrance
)


def _polygon_location(x, y, polygon):
    inside = False
    near_edge = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = bx - ax, by - ay
        if (ay > y) != (by > y) and x < ax + (y - ay) * dx / dy:
            inside = not inside

        projection = ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, projection))
        distance_sq = (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2
        near_edge = near_edge or distance_sq <= FOOT_RADIUS ** 2
    return inside, near_edge


def can_walk_in_lobby(x, foot_y):
    y = CANVAS_HEIGHT - foot_y
    inside, near_edge = _polygon_location(x, y, COURTYARD)
    if not inside or near_edge:
        return False

    for wall in FORGE_WALLS:
        if any(_polygon_location(x, y, wall)):
            return False

    return not any(
        ((x - cx) / (rx + FOOT_RADIUS)) ** 2 + ((y - cy) / (ry + FOOT_RADIUS)) ** 2 <= 1
        for cx, cy, rx, ry in SOLID_ELLIPSES
    )


class LobbySprite:
    def __init__(self, name, left, top):
        self.image = load_image(f'asset/lobby_layers/{name}.png')
        self.x = left + self.image.w / 2
        self.y = CANVAS_HEIGHT - top - self.image.h / 2

    def draw(self):
        self.image.draw(self.x, self.y)


def create_lobby_world(player):
    world = game_world.GameWorld()
    world.add(LobbySprite('lobby_background', 0, 0), game_world.BACKGROUND)
    world.add(LobbySprite('forge_floor', 0, 156), game_world.BACKGROUND)

    # Sprite offsets use image coordinates. Depth uses the footprint in world coordinates.
    forge_objects = (
        ('forge_pillar_left', 105, 272, 507),
        ('forge_pillar_right', 357, 192, 387),
        ('forge_anvil', 271, 358, ANVIL_FOOTPRINT[1]),
    )
    for name, left, top, depth in forge_objects:
        world.add(LobbySprite(name, left, top), game_world.OBJECTS,
                  foot_y=lambda depth=depth: CANVAS_HEIGHT - depth)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)

    world.add(LobbySprite('forge_roof', 0, 0), game_world.FOREGROUND)
    return world


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    player = Player.player()
    player.x, player.y = CANVAS_WIDTH // 2, 150
    world = create_lobby_world(player)
    previous_time = time.perf_counter()

    while key_handle_events.running:
        frame_start = time.perf_counter()
        delta_time = frame_start - previous_time
        previous_time = frame_start

        key_handle_events.handle_events(player)
        if not key_handle_events.running:
            break

        player.update(delta_time, can_walk_in_lobby)
        clear_canvas()
        world.draw()
        update_canvas()

        # Pace rendering while the next delta includes both work and sleep time.
        remaining_time = 1.0 / TARGET_FPS - (time.perf_counter() - frame_start)
        if remaining_time > 0:
            time.sleep(remaining_time)

    close_canvas()


if __name__ == "__main__":
    main()
