from collections.abc import Callable
from dataclasses import dataclass

from pico2d import load_image

import game_world
import lobby_map
import outer_fortress
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
from talisman_statue import LandingWarning, TalismanStatue
from training_dummy import TrainingDummy
from well_interaction import WellInteraction


SHOW_COLLISION_BOXES = False


class LobbySprite:
    def __init__(self, name, left, top):
        self.image = load_image(f'asset/lobby_layers/{name}.png')
        self.x = left + self.image.w / 2
        self.y = CANVAS_HEIGHT - top - self.image.h / 2

    def draw(self):
        self.image.draw(self.x, self.y)


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
    door: MapDoor
    arrival: tuple
    facing: int
    destination: str
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
        if self.camera is not None:
            self.camera.follow(player.x, player.y, snap=True)

    def advance(self, player, dice_ui, delta_time):
        flash_pending = player.state == 'FLASH_STRIKE' and player.flash_path is None
        advance_simulation(player, dice_ui, delta_time, self.can_move, self.campfire,
                           self.dummy, enemies=self.enemies)
        if self.camera is not None:
            self.camera.follow(player.x, player.y, delta_time, snap=flash_pending and delta_time > 0)


def create_outer_fortress_scene(player, dice_ui):
    world = game_world.GameWorld()
    camera = Camera((CANVAS_WIDTH, CANVAS_HEIGHT), outer_fortress.SIZE)
    door = MapDoor(player, outer_fortress.RETURN_AREA, '[E] Return to Lobby', camera)
    wraiths = tuple(ArmoredWraith(route[0], patrol=route, patrol_area=area)
                    for area, route in outer_fortress.WRAITH_PATROLS)
    route = outer_fortress.STATUE_PATROL
    statue = TalismanStatue(route[0], patrol=route, patrol_area=outer_fortress.EAST_COURT)
    enemies = (*wraiths, statue)
    world.add(outer_fortress.Background(), game_world.BACKGROUND)
    world.add(LandingWarning(statue), game_world.BACKGROUND)
    for enemy in enemies:
        world.add(enemy, game_world.OBJECTS, foot_y=lambda enemy=enemy: enemy.foot_y)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)
    for name, left, top, foot_y in outer_fortress.GATE_PIERS:
        world.add(outer_fortress.GateWallSprite(name, left, top), game_world.OBJECTS,
                  foot_y=lambda y=foot_y: y)
    lintel = outer_fortress.GateWallSprite(*outer_fortress.GATE_LINTEL)
    world.add(lintel, game_world.FOREGROUND)
    add_hud(world, player, dice_ui)
    world.add(door, game_world.UI)
    return Scene(world, door, outer_fortress.ENTRY, player.RIGHT, destination='lobby',
                 enemies=enemies, can_move=outer_fortress.can_walk, camera=camera)


def create_lobby_scene(player, dice_ui):
    well = WellInteraction(player)
    campfire = Campfire()
    dummy = TrainingDummy()
    world = create_lobby_world(player, dice_ui, well, campfire, dummy)
    door = MapDoor(player, BoundingBox(*lobby_map.NORTH_DOOR_AREA), '[E] Enter Outer Fortress')
    world.add(door, game_world.UI)
    return Scene(world, door, lobby_map.NORTH_DOOR_RETURN, player.DOWN, destination='outer_fortress',
                 well=well, campfire=campfire, dummy=dummy)
