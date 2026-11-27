from bounding_box import BoundingBox
from collision import _polygon_location


SIZE = 2600, 1500
ENTRY = 348, 142  # Foot position on the lower-left entrance path.

# Keep enemies in four parts of the courtyard. The first point of each loop is the spawn.
WEST_COURT = BoundingBox(375, 350, 1030, 1195)
CENTRAL_COURT = BoundingBox(1000, 240, 1720, 1160)
SOUTHEAST_COURT = BoundingBox(1690, 250, 2315, 720)
NORTHEAST_COURT = BoundingBox(1690, 700, 2340, 1180)

WRAITH_PATROLS = (
    (WEST_COURT, ((700, 420), (820, 420), (820, 500), (700, 500))),
    (WEST_COURT, ((470, 800), (590, 800), (590, 930), (470, 930))),
    (CENTRAL_COURT, ((1075, 410), (1240, 410), (1240, 490), (1075, 490))),
    (CENTRAL_COURT, ((1255, 920), (1395, 920), (1395, 1010), (1255, 1010))),
    (SOUTHEAST_COURT, ((1790, 392), (1885, 392), (1885, 485), (1790, 485))),
    (NORTHEAST_COURT, ((2070, 845), (2195, 845), (2195, 920), (2070, 920))),
)
HOUND_PATROLS = (
    (WEST_COURT, ((535, 580), (730, 580), (730, 680), (535, 680))),
    (CENTRAL_COURT, ((1200, 605), (1385, 605), (1385, 690), (1200, 690))),
    (CENTRAL_COURT, ((1495, 335), (1620, 335), (1620, 445), (1495, 445))),
    (SOUTHEAST_COURT, ((2070, 400), (2230, 400), (2230, 510), (2070, 510))),
    (NORTHEAST_COURT, ((1830, 740), (1950, 740), (1950, 850), (1830, 850))),
)
STATUE_PATROLS = (
    (WEST_COURT, ((920, 1050), (995, 1050), (995, 1155), (920, 1155))),
    (CENTRAL_COURT, ((1590, 690), (1655, 690), (1655, 780), (1590, 780))),
    (SOUTHEAST_COURT, ((1950, 600), (2040, 600), (2040, 678), (1950, 678))),
    (NORTHEAST_COURT, ((1950, 1045), (2040, 1045), (2040, 1085), (1950, 1085))),
)

# Trace the floor and the two pillars on a half-size image, using top-left coordinates.
WALKABLE = tuple((x * 2, y * 2) for x, y in (
    (149, 329), (155, 291), (179, 268), (209, 225), (254, 188),
    (291, 181), (340, 167), (412, 158), (487, 147), (569, 139),
    (648, 127), (740, 121), (838, 122), (884, 132), (936, 155),
    (980, 176), (1031, 197), (1060, 189), (1092, 160), (1142, 178),
    (1193, 193), (1193, 233), (1184, 266), (1166, 300), (1166, 418),
    (1186, 541), (1170, 579), (1136, 620), (1094, 637), (1054, 654),
    (973, 662), (885, 674), (803, 678), (747, 674), (720, 682),
    (633, 678), (539, 669), (448, 661), (408, 651), (373, 638),
    (328, 654), (283, 668), (238, 685), (191, 709), (145, 730),
    (108, 717), (91, 688), (90, 665), (100, 644), (134, 641),
    (164, 671), (201, 643), (248, 608), (305, 588), (314, 556),
    (303, 521), (277, 499), (237, 487), (193, 462), (160, 438), (146, 409),
))
PILLARS = tuple(tuple((x * 2, y * 2) for x, y in footprint) for footprint in (
    ((407, 273), (435, 257), (479, 280), (444, 301)),
    ((746, 249), (777, 233), (828, 252), (792, 278)),
))


# The cutouts match the map pixels. Sort them at the ground center of each base.
PILLAR_SPRITES = (
    ('stage_02_pillar_left.png', 790, 345, SIZE[1] - 565),
    ('stage_02_pillar_right.png', 1450, 292, SIZE[1] - 517),
)


def can_walk(x, foot_y):
    top_y = SIZE[1] - foot_y
    inside, near_edge = _polygon_location(x, top_y, WALKABLE)
    return inside and not near_edge and not any(
        any(_polygon_location(x, top_y, pillar)) for pillar in PILLARS
    )
