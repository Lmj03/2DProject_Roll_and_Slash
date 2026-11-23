import time

from pico2d import clear_canvas, close_canvas, open_canvas, update_canvas

import Player
from lobby_map import CANVAS_HEIGHT, CANVAS_WIDTH
from scene_manager import SceneManager


TARGET_FPS = 60


def main():
    open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        manager = SceneManager(Player.player())
        previous_time = time.perf_counter()

        while True:
            frame_start = time.perf_counter()
            delta_time = frame_start - previous_time
            previous_time = frame_start

            if not manager.advance(delta_time):
                break
            clear_canvas()
            manager.draw()
            update_canvas()

            remaining_time = 1.0 / TARGET_FPS - (time.perf_counter() - frame_start)
            if remaining_time > 0:
                time.sleep(remaining_time)
    finally:
        close_canvas()


if __name__ == "__main__":
    main()
