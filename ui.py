from ctypes import byref, c_int

from pico2d import TTF_SizeUTF8, load_font, load_image


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
