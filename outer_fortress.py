from bounding_box import BoundingBox
from collision import _polygon_location


SIZE = 2400, 1100
ENTRY = 172, 300  # World coordinates at the player's feet.
RETURN_AREA = BoundingBox(25, 258, 110, 315)
GALLERY_EXIT_AREA = BoundingBox(2138, 515, 2265, 614)
# The first point of each patrol loop is the spawn at ground level.
WEST_COURT = BoundingBox(342, 200, 1040, 736)
EAST_COURT = BoundingBox(1240, 190, 2245, 841)
STATUE_PATROL = ((1920, 670), (1920, 725), (1835, 725), (1835, 620), (1920, 620))
WRAITH_PATROLS = (
    (WEST_COURT, ((421, 458), (421, 583), (490, 583), (490, 458))),
    (WEST_COURT, ((650, 335), (880, 335), (880, 412), (650, 412))),
    (EAST_COURT, ((1590, 532), (1770, 532), (1770, 735), (1450, 735), (1450, 532))),
    (EAST_COURT, ((1360, 360), (1610, 360), (1610, 446), (1360, 446))),
    (EAST_COURT, ((2090, 350), (2150, 350), (2150, 438), (2090, 438))),
)
HOUND_PATROLS = (
    (WEST_COURT, ((771, 510), (825, 510), (825, 650), (545, 650), (545, 510))),
    (EAST_COURT, ((1870, 383), (2025, 383), (2025, 565), (1820, 565), (1820, 383))),
)
# Layer image positions are measured from the top-left of the map.
GATE_LINTEL = ('stage_01_gate_foreground.png', 950, 392)
GATE_PIERS = (
    ('stage_01_gate_left_pier.png', 927, 559, 393),
    ('stage_01_gate_right_pier.png', 1173, 569, 319),
)

# Trace the edges at half size for readability. Points follow the art from the
# left path, through the gate in the dividing wall, around the right court.
WALKABLE = tuple((x * 2, y * 2) for x, y in (
    (0, 389), (44, 383), (123, 358), (166, 328), (165, 272),
    (179, 226), (204, 205), (257, 187), (477, 183), (485, 199),
    (489, 329), (477, 347), (489, 364), (510, 368),
    (522, 359), (523, 340), (525, 319), (530, 301), (536, 284),
    (544, 267), (555, 251), (568, 232), (560, 181), (580, 156), (618, 138),
    (897, 132), (951, 142), (982, 173), (1001, 234), (1017, 266),
    (1048, 272), (1059, 247), (1080, 239), (1129, 255), (1140, 267),
    (1134, 286), (1127, 322), (1101, 374), (1075, 401), (1016, 429),
    (967, 447), (813, 452), (704, 453), (661, 439),
    (638, 420), (629, 399), (621, 383), (616, 369), (582, 355),
    (583, 374), (573, 390), (568, 409), (582, 449),
    (531, 453), (239, 450), (208, 432), (171, 407), (116, 408),
    (56, 423), (0, 424),
))


def can_walk(x, foot_y):
    inside, near_edge = _polygon_location(x, SIZE[1] - foot_y, WALKABLE)
    return inside and not near_edge
