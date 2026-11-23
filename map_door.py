from pico2d import SDL_KEYDOWN, SDLK_e, load_font, load_image

from dice_ui import DiceSlot


class MapDoor:
    def __init__(self, player, area, label, camera=None):
        self.player = player
        self.area = area
        self.label = label
        self.camera = camera
        self.requested = False
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 14)
        self.frame = load_image('asset/health_bar_frame.png')

    def can_enter(self):
        player = self.player
        return player.hp > 0 and player.state in ('IDLE', 'RUN') and self.area.contains(
            player.x, player.y - player.FOOT_OFFSET_Y,
        )

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_e and self.can_enter():
            self.requested = True
            return True
        return False

    def take_request(self):
        requested, self.requested = self.requested, False
        return requested

    def draw(self):
        if self.can_enter():
            x, y = self.player.x, self.player.y + 63
            if self.camera is not None:
                x, y = self.camera.project(x, y)
                x = min(max(125, x), self.camera.width - 125)
                y = min(y, self.camera.height - 20)
            self.frame.draw(x, y, 246, 32)
            DiceSlot._draw_label(self.font, self.label, x, y, (248, 237, 211))
