CANVAS_WIDTH, CANVAS_HEIGHT = 1500, 700
PLAYER_START = (CANVAS_WIDTH // 2, 150)
FOOT_RADIUS = 9
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

# Name, left, top in the lobby image's top-left coordinate system.
BACKGROUND_SPRITES = (
    ('lobby_background', 0, 0),
    ('forge_floor', 0, 156),
)
# The last value is the object's footprint Y, also measured from the image top.
FORGE_OBJECTS = (
    ('forge_pillar_left', 105, 272, 507),
    ('forge_pillar_right', 357, 192, 387),
    ('forge_anvil', 271, 358, ANVIL_FOOTPRINT[1]),
)
FOREGROUND_SPRITES = (
    ('forge_roof', 0, 0),
)
