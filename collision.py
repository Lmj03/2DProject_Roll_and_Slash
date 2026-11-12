from lobby_map import (
    CANVAS_HEIGHT, COURTYARD, FOOT_RADIUS, FORGE_WALLS, SOLID_ELLIPSES,
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
