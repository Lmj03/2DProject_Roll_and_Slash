from ctypes import byref, c_int
from math import ceil

from buffs import BUFF_SPECS

from pico2d import TTF_SizeUTF8, load_font, load_image
from sdl2 import SDL_SetTextureColorMod


class HealthBar:
    SCALE = 1.2
    FILL_OFFSET_X = 5
    FILL_RIGHT_INSET = 1
    FILL_OFFSET_Y = 11

    def __init__(self, player, left=32, bottom=32):
        self.player = player
        self.left = left
        self.bottom = bottom
        self.frame = load_image('asset/health_bar_frame.png')
        self.fill = load_image('asset/health_bar_fill.png')
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', round(14 * self.SCALE))

    def draw(self):
        frame_width = round(self.frame.w * self.SCALE)
        frame_height = round(self.frame.h * self.SCALE)
        self.frame.draw(self.left + frame_width / 2, self.bottom + frame_height / 2,
                        frame_width, frame_height)

        max_hp = max(0, self.player.max_hp)
        hp = max(0, min(self.player.hp, max_hp))
        ratio = hp / max_hp if max_hp else 0
        fill_left = self.left + round(self.FILL_OFFSET_X * self.SCALE)
        fill_bottom = self.bottom + round(self.FILL_OFFSET_Y * self.SCALE)
        fill_width = round((self.frame.w - self.FILL_OFFSET_X - self.FILL_RIGHT_INSET) * self.SCALE)
        fill_height = round(self.fill.h * self.SCALE)
        width = round(self.fill.w * ratio)
        draw_width = round(fill_width * ratio)
        if width:
            self.fill.clip_draw(
                0, 0, width, self.fill.h,
                fill_left + draw_width / 2,
                fill_bottom + fill_height / 2,
                draw_width, fill_height,
            )

        text = f'{hp:g} / {max_hp:g}'
        text_width = c_int()
        TTF_SizeUTF8(self.font.font, text.encode('utf-8'), byref(text_width), None)
        x = fill_left + (fill_width - text_width.value) / 2
        y = fill_bottom + fill_height / 2
        self.font.draw(x + 1, y - 1, text, (25, 17, 15))
        self.font.draw(x, y, text, (248, 237, 211))


class SwordStackBar:
    CELL_SIZE = 100
    DRAW_SIZE = 80
    GAP = 6
    EMPTY_BRIGHTNESS = 96

    def __init__(self, player, right, bottom=32):
        self.player = player
        self.right = right
        self.bottom = bottom
        self.sheet = load_image('asset/sword_stack_sheet.png')
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 12)

    def draw(self):
        count = len(self.player.sword_max_stacks)
        total_width = count * self.DRAW_SIZE + (count - 1) * self.GAP
        left = self.right - total_width

        for index, maximum in enumerate(self.player.sword_max_stacks):
            maximum = max(0, maximum)
            stacks = max(0, min(self.player.sword_stacks[index], maximum))
            brightness = 255 if stacks else self.EMPTY_BRIGHTNESS
            center_x = left + index * (self.DRAW_SIZE + self.GAP) + self.DRAW_SIZE / 2
            center_y = self.bottom + self.DRAW_SIZE / 2

            SDL_SetTextureColorMod(self.sheet.texture, brightness, brightness, brightness)
            self.sheet.clip_draw(
                index * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
                center_x, center_y, self.DRAW_SIZE, self.DRAW_SIZE,
            )
            SDL_SetTextureColorMod(self.sheet.texture, 255, 255, 255)

            text = f'{stacks} / {maximum}'
            text_width = c_int()
            TTF_SizeUTF8(self.font.font, text.encode('utf-8'), byref(text_width), None)
            x = center_x - text_width.value / 2
            y = self.bottom + self.DRAW_SIZE * 0.19
            color = (248, 237, 211) if stacks else (155, 150, 143)
            self.font.draw(x + 1, y - 1, text, (18, 14, 12))
            self.font.draw(x, y, text, color)


class BuffStatusBar:
    CELL_SIZE = 100
    DRAW_SIZE = 48

    def __init__(self, player, left=32, bottom=94):
        self.player = player
        self.left = left
        self.bottom = bottom
        self.sheet = load_image('asset/buff_status_sheet.png')
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 12)

    def draw(self):
        active = self.player.buffs.active
        if active is None:
            return
        spec = BUFF_SPECS[active.kind]
        center_x = self.left + self.DRAW_SIZE / 2
        center_y = self.bottom + self.DRAW_SIZE / 2
        self.sheet.clip_draw(
            spec.icon_index * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
            center_x, center_y, self.DRAW_SIZE, self.DRAW_SIZE,
        )
        amount = spec.amount_per_face * active.face * 100
        unit = '%' if spec.multiplicative else '%p'
        text_left = self.left + self.DRAW_SIZE + 8
        self._draw_text(f'{spec.label} +{amount:g}{unit}', text_left, self.bottom + 33)
        seconds = ceil(active.remaining * 10) / 10
        self._draw_text(f'{seconds:.1f}s', text_left, self.bottom + 13)

    def _draw_text(self, text, x, y):
        self.font.draw(x + 1, y - 1, text, (20, 14, 12))
        self.font.draw(x, y, text, (248, 237, 211))
