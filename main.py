import time

from pico2d import *
import game_world
import Player
import key_handle_events
import lobby_map
import ui
from dice_ui import DiceRollUI
from well_interaction import WellInteraction
from campfire import Campfire
from armored_wraith import ArmoredWraith
from training_dummy import TrainingDummy
from collision_debug import CollisionDebug
from collision import can_walk_in_lobby
from lobby_map import CANVAS_WIDTH, CANVAS_HEIGHT

TARGET_FPS = 60
COMBAT_STEP = 1.0 / 60.0
SHOW_COLLISION_BOXES = True


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
    world.add(ui.HealthBar(player), game_world.UI)
    world.add(ui.SwordStackBar(player, right=CANVAS_WIDTH - 32), game_world.UI)
    if dice_ui is None:
        dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
    world.add(ui.BuffStatusBar(player, duration_mask=dice_ui.cooldown_mask), game_world.UI)
    world.add(dice_ui, game_world.UI)
    if well is None:
        well = WellInteraction(player)
    world.add(well, game_world.UI)
    return world


def advance_simulation(player, dice_ui, delta_time, can_move=can_walk_in_lobby, campfire=None, dummy=None,
                       *, targets=(), enemies=()):
    enemies = tuple(enemies)
    combat_targets = (*targets, *enemies)
    if dummy is not None:
        combat_targets = (dummy, *combat_targets)

    def can_step(x, foot_y, *, ignore=None):
        return (can_move is None or can_move(x, foot_y)) and not any(
            target is not ignore and target.blocks(x, foot_y) for target in combat_targets)

    # Equipment can change while simulation time is paused in the well menu.
    dice_ui.update(0.0)
    remaining = delta_time
    if remaining > 0 and player.state == 'FLASH_STRIKE' and player.flash_path is None:
        player.resolve_flash_strike(can_move, can_step)
        # Check all targets at departure time; the remaining frames are visual recovery.
        for target in combat_targets:
            target.check_attack(player)
    while remaining > 0:
        # Bound movement during contact checks, including slow frames and speed buffs.
        step = min(remaining, campfire.SIMULATION_STEP) if campfire is not None else remaining
        if combat_targets:
            step = min(step, COMBAT_STEP)
        for slot in (dice_ui.sword, dice_ui.buff):
            if slot.roll_elapsed is not None:
                step = min(step, max(1e-9, slot.ROLL_DURATION - slot.roll_elapsed))
        # Resolve a roll at its exact time, then simulate the remainder with its new effect.
        player.update(step, can_step if combat_targets else can_move)
        for target in combat_targets:
            target.update(step)
            if player.state != 'FLASH_STRIKE':
                target.check_attack(player)
        for enemy in enemies:
            enemy.act(player, step, lambda x, y, enemy=enemy: can_step(x, y, ignore=enemy))
        dice_ui.update(step)
        if campfire is not None:
            campfire.update(step)
            campfire.apply_damage(step, player)
        remaining = max(0.0, remaining - step)


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    player = Player.player()
    player.x, player.y = lobby_map.PLAYER_START
    dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
    well = WellInteraction(player)
    campfire = Campfire()
    dummy = TrainingDummy()
    enemies = (ArmoredWraith(lobby_map.M1_TEST_POSITION),)
    world = create_lobby_world(player, dice_ui, well, campfire, dummy, enemies=enemies)
    previous_time = time.perf_counter()

    while key_handle_events.running:
        frame_start = time.perf_counter()
        delta_time = frame_start - previous_time
        previous_time = frame_start

        menu_was_open = well.menu.is_open
        key_handle_events.handle_events(player, dice_ui, well)
        if not key_handle_events.running:
            break

        # Keep the event/render loop responsive and discard simulation time spent in the menu.
        simulation_delta = 0.0 if menu_was_open or well.menu.is_open else delta_time
        advance_simulation(player, dice_ui, simulation_delta, campfire=campfire, dummy=dummy, enemies=enemies)
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
