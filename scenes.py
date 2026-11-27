from collections.abc import Callable
from dataclasses import dataclass

from pico2d import load_image

import game_world
import lobby_map
import outer_fortress
import talisman_gallery
import ui
from armored_wraith import ArmoredWraith
from bounding_box import BoundingBox
from camera import Camera
from campfire import Campfire
from collision import can_walk_in_lobby
from collision_debug import CollisionDebug
from dice_ui import DiceRollUI
from lobby_map import CANVAS_HEIGHT, CANVAS_WIDTH
from map_door import MapDoor
from simulation import advance_simulation
from skull_hound import SkullHound
from talisman_statue import LandingWarning, TalismanStatue
from training_dummy import TrainingDummy
from well_interaction import WellInteraction


SHOW_COLLISION_BOXES = False


class MapBackground:
    def __init__(self, filename, size):
        self.image = load_image(f'asset/maps/{filename}')
        if (self.image.w, self.image.h) != size:
            raise ValueError(f'{filename} must be {size[0]} by {size[1]} pixels.')

    def draw(self, camera):
        left, bottom = camera.origin
        x, y = camera.project(left + camera.width / 2, bottom + camera.height / 2)
        self.image.clip_draw(left, bottom, camera.width, camera.height, x, y)


class MapObjectSprite:
    def __init__(self, name, left, top, map_height):
        self.image = load_image(f'asset/maps/{name}')
        self.x = left + self.image.w / 2
        self.y = map_height - top - self.image.h / 2

    def draw(self, camera):
        self.image.draw(*camera.project(self.x, self.y))


class LobbySprite:
    def __init__(self, name, left, top):
        self.image = load_image(f'asset/lobby_layers/{name}.png')
        self.x = left + self.image.w / 2
        self.y = CANVAS_HEIGHT - top - self.image.h / 2

    def draw(self, camera=None):
        x, y = self.x, self.y
        if camera is not None:
            x, y = camera.project(x, y)
        self.image.draw(x, y)


def create_lobby_world(player, dice_ui=None, well=None, campfire=None, dummy=None, *, enemies=()):
    world = game_world.GameWorld()
    for name, left, top in lobby_map.BACKGROUND_SPRITES:
        world.add(LobbySprite(name, left, top), game_world.BACKGROUND)

    # Sprite offsets use image coordinates. Depth uses the footprint in world coordinates.
    for name, left, top, depth in lobby_map.FORGE_OBJECTS:
        world.add(LobbySprite(name, left, top), game_world.OBJECTS,
                  foot_y=lambda depth=depth: CANVAS_HEIGHT - depth)
    if campfire is None:
        campfire = Campfire()
    world.add(campfire, game_world.OBJECTS, foot_y=lambda: campfire.foot_y)
    if dummy is None:
        dummy = TrainingDummy()
    world.add(dummy, game_world.OBJECTS, foot_y=lambda: dummy.foot_y)
    enemies = tuple(enemies)
    for enemy in enemies:
        world.add(enemy, game_world.OBJECTS, foot_y=lambda enemy=enemy: enemy.foot_y)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)

    for name, left, top in lobby_map.FOREGROUND_SPRITES:
        world.add(LobbySprite(name, left, top), game_world.FOREGROUND)
    if SHOW_COLLISION_BOXES:
        world.add(CollisionDebug(player, dummy, enemies), game_world.DEBUG)
    if dice_ui is None:
        dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
    add_hud(world, player, dice_ui)
    if well is None:
        well = WellInteraction(player)
    world.add(well, game_world.UI)
    return world


def add_hud(world, player, dice_ui):
    world.add(ui.HealthBar(player), game_world.UI)
    world.add(ui.SwordStackBar(player, right=CANVAS_WIDTH - 32), game_world.UI)
    world.add(ui.BuffStatusBar(player, duration_mask=dice_ui.cooldown_mask), game_world.UI)
    world.add(dice_ui, game_world.UI)


@dataclass
class Scene:
    world: game_world.GameWorld
    arrival: tuple
    facing: int
    doors: tuple[MapDoor, ...] = ()
    enemies: tuple = ()
    can_move: Callable[[float, float], bool] = can_walk_in_lobby
    camera: Camera | None = None
    well: WellInteraction | None = None
    campfire: Campfire | None = None
    dummy: TrainingDummy | None = None

    def enter(self, player):
        player.reset_inputs()
        player.dir = self.facing
        player.x, foot_y = self.arrival
        player.y = foot_y + player.FOOT_OFFSET_Y
        player.damage_popups.clear()
        player.hit_stop_remaining = 0.0
        player.hit_shake.reset()
        if self.camera is not None:
            self.camera.follow(player.x, player.y, snap=True)

    def advance(self, player, dice_ui, delta_time):
        player.hit_shake.update(delta_time)
        flash_pending = player.state == 'FLASH_STRIKE' and player.flash_path is None
        advance_simulation(player, dice_ui, delta_time, self.can_move, self.campfire,
                           self.dummy, enemies=self.enemies)
        if self.camera is not None:
            self.camera.follow(player.x, player.y, delta_time, snap=flash_pending and delta_time > 0)


def create_outer_fortress_scene(player, dice_ui):
    world = game_world.GameWorld()
    camera = Camera((CANVAS_WIDTH, CANVAS_HEIGHT), outer_fortress.SIZE)
    return_door = MapDoor(player, outer_fortress.RETURN_AREA, '[E] Return to Lobby',
                          destination='lobby', camera=camera)
    wraiths = tuple(ArmoredWraith(route[0], patrol=route, patrol_area=area)
                    for area, route in outer_fortress.WRAITH_PATROLS)
    hounds = tuple(SkullHound(route[0], patrol=route, patrol_area=area)
                   for area, route in outer_fortress.HOUND_PATROLS)
    route = outer_fortress.STATUE_PATROL
    statue = TalismanStatue(route[0], patrol=route, patrol_area=outer_fortress.EAST_COURT)
    enemies = (*wraiths, *hounds, statue)

    def gallery_lock_label():
        remaining = sum(enemy.hp > 0 for enemy in enemies)
        if remaining == 1:
            return '1 enemy remaining'
        if remaining:
            return f'{remaining} enemies remaining'
        return None

    gallery_door = MapDoor(player, outer_fortress.GALLERY_EXIT_AREA, '[E] Enter Talisman Gallery',
                           destination='talisman_gallery', camera=camera, locked_label=gallery_lock_label)
    world.add(MapBackground('stage_01_outer_fortress.png', outer_fortress.SIZE), game_world.BACKGROUND)
    world.add(LandingWarning(statue), game_world.BACKGROUND)
    for enemy in enemies:
        world.add(enemy, game_world.OBJECTS, foot_y=lambda enemy=enemy: enemy.foot_y)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)
    for name, left, top, foot_y in outer_fortress.GATE_PIERS:
        pier = MapObjectSprite(name, left, top, outer_fortress.SIZE[1])
        world.add(pier, game_world.OBJECTS, foot_y=lambda y=foot_y: y)
    lintel = MapObjectSprite(*outer_fortress.GATE_LINTEL, outer_fortress.SIZE[1])
    world.add(lintel, game_world.FOREGROUND)
    add_hud(world, player, dice_ui)
    world.add(return_door, game_world.UI)
    world.add(gallery_door, game_world.UI)
    return Scene(world, outer_fortress.ENTRY, player.RIGHT, doors=(return_door, gallery_door),
                 enemies=enemies, can_move=outer_fortress.can_walk, camera=camera)


def create_talisman_gallery_scene(player, dice_ui):
    world = game_world.GameWorld()
    camera = Camera((CANVAS_WIDTH, CANVAS_HEIGHT), talisman_gallery.SIZE)
    wraiths = tuple(ArmoredWraith(route[0], patrol=route, patrol_area=area)
                    for area, route in talisman_gallery.WRAITH_PATROLS)
    hounds = tuple(SkullHound(route[0], patrol=route, patrol_area=area)
                   for area, route in talisman_gallery.HOUND_PATROLS)
    statues = tuple(TalismanStatue(route[0], patrol=route, patrol_area=area)
                    for area, route in talisman_gallery.STATUE_PATROLS)
    enemies = (*wraiths, *hounds, *statues)

    world.add(MapBackground('stage_02_talisman_gallery.png', talisman_gallery.SIZE), game_world.BACKGROUND)
    for statue in statues:
        world.add(LandingWarning(statue), game_world.BACKGROUND)
    for enemy in enemies:
        world.add(enemy, game_world.OBJECTS, foot_y=lambda enemy=enemy: enemy.foot_y)
    for name, left, top, foot_y in talisman_gallery.PILLAR_SPRITES:
        pillar = MapObjectSprite(name, left, top, talisman_gallery.SIZE[1])
        world.add(pillar, game_world.OBJECTS, foot_y=lambda y=foot_y: y)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)
    add_hud(world, player, dice_ui)
    return Scene(world, talisman_gallery.ENTRY, player.RIGHT,
                 enemies=enemies, can_move=talisman_gallery.can_walk, camera=camera)


def create_lobby_scene(player, dice_ui):
    well = WellInteraction(player)
    campfire = Campfire()
    dummy = TrainingDummy()
    world = create_lobby_world(player, dice_ui, well, campfire, dummy)
    door = MapDoor(player, BoundingBox(*lobby_map.NORTH_DOOR_AREA), '[E] Enter Outer Fortress',
                   destination='outer_fortress')
    world.add(door, game_world.UI)
    return Scene(world, lobby_map.NORTH_DOOR_RETURN, player.DOWN, doors=(door,),
                 well=well, campfire=campfire, dummy=dummy)
