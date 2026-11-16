from pico2d import load_font, load_image

from collision import can_interact_with_well
from dice_ui import DiceSlot
from lobby_map import CANVAS_HEIGHT, WELL_PROMPT_POSITION


class WellInteraction:
    def __init__(self, player):
        self.player = player
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 14)
        self.hint_frame = load_image('asset/health_bar_frame.png')

    def can_interact(self):
        return self.player.state in ('IDLE', 'RUN') and can_interact_with_well(
            self.player.x, self.player.y - self.player.FOOT_OFFSET_Y,
        )

    def draw(self):
        if not self.can_interact():
            return
        x, image_y = WELL_PROMPT_POSITION
        y = CANVAS_HEIGHT - image_y
        self.hint_frame.draw(x, y, 246, 32)
        DiceSlot._draw_label(self.font, '[E] Choose stat die', x, y, (248, 237, 211))
