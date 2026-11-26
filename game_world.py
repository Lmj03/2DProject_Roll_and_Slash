from camera import RenderView
from lobby_map import CANVAS_HEIGHT, CANVAS_WIDTH


BACKGROUND, OBJECTS, FOREGROUND, DEBUG, UI = range(5)


class GameWorld:
    def __init__(self):
        self.layers = [[] for _ in range(UI + 1)]

    def add(self, obj, layer, *, foot_y=None):
        self.layers[layer].append((obj, foot_y))

    def draw(self, camera=None, *, shake=(0, 0)):
        if shake != (0, 0):
            # Cover the strips exposed at screen edges while keeping the render viewport fixed.
            self._draw_layer(BACKGROUND, camera)
            if camera is None:
                camera = RenderView(CANVAS_WIDTH, CANVAS_HEIGHT, offset=shake)
            else:
                camera = RenderView(camera.width, camera.height, camera.origin, shake)
        for layer in range(UI):
            self._draw_layer(layer, camera)
        self._draw_layer(UI)

    def _draw_layer(self, layer, camera=None):
        entries = self.layers[layer]
        if layer == OBJECTS:
            # World Y increases away from the camera. Draw the farthest feet first.
            entries = sorted(entries, key=lambda entry: entry[1]() if entry[1] else 0,
                             reverse=True)
        for obj, _ in entries:
            if camera is None:
                obj.draw()
            else:
                obj.draw(camera)
