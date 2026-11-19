BACKGROUND, OBJECTS, FOREGROUND, DEBUG, UI = range(5)


class GameWorld:
    def __init__(self):
        self.layers = [[] for _ in range(UI + 1)]

    def add(self, obj, layer, *, foot_y=None):
        self.layers[layer].append((obj, foot_y))

    def draw(self):
        for layer, entries in enumerate(self.layers):
            if layer == OBJECTS:
                # World Y increases away from the camera. Draw the farthest feet first.
                entries = sorted(entries, key=lambda entry: entry[1]() if entry[1] else 0,
                                 reverse=True)
            for obj, _ in entries:
                obj.draw()
