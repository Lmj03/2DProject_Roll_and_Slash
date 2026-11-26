from pico2d import SDL_KEYDOWN, SDLK_e, load_font, load_image

from dice_ui import DiceSlot


class MapDoor:
    def __init__(self, player, area, label, *, destination, camera=None, locked_label=None):
        self.player = player
        self.area = area
        self.label = label
        self.camera = camera
        self.destination = destination
        self.locked_label = locked_label
        self.requested = False
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 14)
        self.frame = load_image('asset/health_bar_frame.png')

    def _player_at_door(self):
        player = self.player
        return player.hp > 0 and player.state in ('IDLE', 'RUN') and self.area.contains(
            player.x, player.y - player.FOOT_OFFSET_Y,
        )

    def _lock_message(self):
        return self.locked_label() if self.locked_label is not None else None

    def can_enter(self):
        return self._player_at_door() and self._lock_message() is None

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_e and self.can_enter():
            self.requested = True
            return True
        return False

    def take_request(self):
        requested, self.requested = self.requested, False
        return requested

    def draw(self):
        if self._player_at_door():
            lock_message = self._lock_message()
            x, y = self.player.x, self.player.y + 63
            if self.camera is not None:
                x, y = self.camera.project(x, y)
                x = min(max(125, x), self.camera.width - 125)
                y = min(y, self.camera.height - 20)
            self.frame.draw(x, y, 246, 32)
            label = self.label if lock_message is None else lock_message
            color = (248, 237, 211) if lock_message is None else (232, 158, 126)
            DiceSlot._draw_label(self.font, label, x, y, color)
