import time

from pico2d import *
import game_world
import Player
import key_handle_events
import lobby_map
import ui
from dice_ui import DiceRollUI
from well_interaction import WellInteraction
from collision import can_walk_in_lobby
from lobby_map import CANVAS_WIDTH, CANVAS_HEIGHT

TARGET_FPS = 60


class LobbySprite:
    def __init__(self, name, left, top):
        self.image = load_image(f'asset/lobby_layers/{name}.png')
        self.x = left + self.image.w / 2
        self.y = CANVAS_HEIGHT - top - self.image.h / 2

    def draw(self):
        self.image.draw(self.x, self.y)


def create_lobby_world(player, dice_ui=None, well=None):
    world = game_world.GameWorld()
    for name, left, top in lobby_map.BACKGROUND_SPRITES:
        world.add(LobbySprite(name, left, top), game_world.BACKGROUND)

    # Sprite offsets use image coordinates. Depth uses the footprint in world coordinates.
    for name, left, top, depth in lobby_map.FORGE_OBJECTS:
        world.add(LobbySprite(name, left, top), game_world.OBJECTS,
                  foot_y=lambda depth=depth: CANVAS_HEIGHT - depth)
    world.add(player, game_world.OBJECTS, foot_y=lambda: player.y - player.FOOT_OFFSET_Y)

    for name, left, top in lobby_map.FOREGROUND_SPRITES:
        world.add(LobbySprite(name, left, top), game_world.FOREGROUND)
    world.add(ui.HealthBar(player), game_world.UI)
    world.add(ui.SwordStackBar(player, right=CANVAS_WIDTH - 32), game_world.UI)
    if dice_ui is None:
        dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
    world.add(dice_ui, game_world.UI)
    if well is None:
        well = WellInteraction(player)
    world.add(well, game_world.UI)
    return world


def advance_simulation(player, dice_ui, delta_time, can_move=can_walk_in_lobby):
    # Equipment can change while simulation time is paused in the well menu.
    dice_ui.update(0.0)
    remaining = delta_time
    while remaining > 0:
        step = remaining
        for slot in (dice_ui.sword, dice_ui.buff):
            if slot.roll_elapsed is not None:
                step = min(step, max(1e-9, slot.ROLL_DURATION - slot.roll_elapsed))
        # Resolve a roll at its exact time, then simulate the remainder with its new effect.
        player.update(step, can_move)
        dice_ui.update(step)
        remaining = max(0.0, remaining - step)


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    player = Player.player()
    player.x, player.y = lobby_map.PLAYER_START
    dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
    well = WellInteraction(player)
    world = create_lobby_world(player, dice_ui, well)
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
        advance_simulation(player, dice_ui, simulation_delta)
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
