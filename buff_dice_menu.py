from pico2d import draw_rectangle, load_font, load_image

from dice_ui import DiceSlot
from lobby_map import CANVAS_WIDTH, CANVAS_HEIGHT


class BuffDiceMenu:
    KINDS = ('attack', 'move', 'critical', 'defense')
    WIDTH, HEIGHT = 640, 300
    GAP = 12

    def __init__(self, player):
        self.player = player
        self.is_open = False
        self.focus = 0
        self.left = (CANVAS_WIDTH - self.WIDTH) / 2
        self.bottom = (CANVAS_HEIGHT - self.HEIGHT) / 2
        self.frame = load_image('asset/dice_slot_frame.png')
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 14)
        width = len(self.KINDS) * DiceSlot.WIDTH + (len(self.KINDS) - 1) * self.GAP
        left = (CANVAS_WIDTH - width) / 2
        self.options = [
            DiceSlot(kind, left + index * (DiceSlot.WIDTH + self.GAP), self.bottom + 68,
                     str(index + 1))
            for index, kind in enumerate(self.KINDS)
        ]

    def draw(self):
        if not self.is_open:
            return
        right, top = self.left + self.WIDTH, self.bottom + self.HEIGHT
        draw_rectangle(self.left, self.bottom, right, top, 30, 24, 22, filled=True)
        draw_rectangle(self.left, self.bottom, right, top, 172, 125, 68)
        draw_rectangle(self.left + 3, self.bottom + 3, right - 3, top - 3, 83, 58, 37)
        DiceSlot._draw_label(self.font, 'CHOOSE STAT DIE', CANVAS_WIDTH / 2, top - 32,
                             (248, 237, 211))
        for index, slot in enumerate(self.options):
            footer = 'EQUIPPED' if slot.kind == self.player.buff_dice_type else 'SELECT'
            slot.draw(self.frame, self.font, footer=footer)
            if index == self.focus:
                draw_rectangle(slot.left - 2, slot.bottom - 2,
                               slot.left + slot.WIDTH + 2, slot.bottom + slot.HEIGHT + 2,
                               248, 207, 130)
        DiceSlot._draw_label(self.font, '[1-4] Choose   Enter Equip   Esc Close',
                             CANVAS_WIDTH / 2, self.bottom + 28, (200, 188, 168))
