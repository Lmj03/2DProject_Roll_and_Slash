import time

from pico2d import *
import game_world
import Player
import key_handle_events
import lobby_map
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


def create_lobby_world(player):
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
    return world


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    player = Player.player()
    player.x, player.y = lobby_map.PLAYER_START
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
