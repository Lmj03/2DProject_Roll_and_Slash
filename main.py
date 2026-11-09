from pico2d import *
import Player
import key_handle_events

CANVAS_WIDTH, CANVAS_HEIGHT = 1500, 700
FOOT_RADIUS = 9

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
    (307, 431, 30, 19),    # Anvil stand
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


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    lobby = load_image('asset/lobby.png')
    player = Player.player()
    player.x, player.y = CANVAS_WIDTH // 2, 150
    
    while key_handle_events.running:
        key_handle_events.handle_events(player)
        if not key_handle_events.running:
            break

        clear_canvas()
        lobby.draw(CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2)
        player.update(can_walk_in_lobby)
        player.draw()
        update_canvas()

    close_canvas()

if __name__ == "__main__":
    main()
