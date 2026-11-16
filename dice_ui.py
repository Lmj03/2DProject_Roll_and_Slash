import random
from ctypes import byref, c_int

from pico2d import (
    SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
    SDLK_f, SDLK_r, TTF_SizeUTF8, get_canvas_height, load_font, load_image,
)


DICE_TYPES = {
    'sword': ('Sword', 'SWORD'),
    'attack': ('Attack', 'ATK'),
    'move': ('Move', 'SPEED'),
    'critical': ('Critical', 'CRIT'),
    'defense': ('Defense', 'DEF'),
}


class DiceSlot:
    WIDTH, HEIGHT = 128, 156
    CELL_SIZE = 100
    DIE_SIZE = 92
    ROLL_FRAME_TIME = 0.03
    ROLL_DURATION = 0.72

    def __init__(self, kind, left, bottom, key_name):
        self.kind = None
        self.left = left
        self.bottom = bottom
        self.key_name = key_name
        self.set_type(kind)

    def set_type(self, kind):
        if self.kind == kind:
            return
        prefix, title = DICE_TYPES[kind]
        faces = load_image(f'asset/{prefix}_Dice.png')
        animation = load_image(f'asset/{prefix}_Dice_Roll.png')
        self.faces, self.animation = faces, animation
        self.kind, self.title = kind, title
        self.face = 1
        self.roll_elapsed = None

    def roll(self):
        if self.roll_elapsed is None:
            self.roll_elapsed = 0.0

    def update(self, delta_time):
        if self.roll_elapsed is None or delta_time <= 0:
            return
        self.roll_elapsed += delta_time
        if self.roll_elapsed >= self.ROLL_DURATION - 1e-9:
            self.face = random.randint(1, 6)
            self.roll_elapsed = None
            return self.face

    def contains(self, x, y):
        return (self.left <= x < self.left + self.WIDTH
                and self.bottom <= y < self.bottom + self.HEIGHT)

    def draw(self, frame, font):
        center_x = self.left + self.WIDTH / 2
        frame.draw(center_x, self.bottom + self.HEIGHT / 2)
        self._draw_label(font, self.title, center_x, self.bottom + self.HEIGHT - 20,
                         (240, 225, 194))

        if self.roll_elapsed is None:
            image, index = self.faces, self.face - 1
            label = f'[{self.key_name}] ROLL'
            color = (248, 237, 211)
        else:
            image = self.animation
            frames = image.w // self.CELL_SIZE
            index = int(self.roll_elapsed / self.ROLL_FRAME_TIME) % frames
            label = 'ROLLING'
            color = (173, 163, 146)
        image.clip_draw(index * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
                        center_x, self.bottom + 79, self.DIE_SIZE, self.DIE_SIZE)
        self._draw_label(font, label, center_x, self.bottom + 18, color)

    @staticmethod
    def _draw_label(font, text, center_x, y, color):
        width = c_int()
        TTF_SizeUTF8(font.font, text.encode('utf-8'), byref(width), None)
        x = center_x - width.value / 2
        font.draw(x + 1, y - 1, text, (20, 14, 12))
        font.draw(x, y, text, color)


class DiceRollUI:
    GAP = 12

    def __init__(self, player, right, top):
        self.player = player
        self.frame = load_image('asset/dice_slot_frame.png')
        self.font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 14)
        bottom = top - DiceSlot.HEIGHT
        left = right - DiceSlot.WIDTH * 2 - self.GAP
        self.sword = DiceSlot('sword', left, bottom, 'R')
        self.buff = DiceSlot(player.buff_dice_type, left + DiceSlot.WIDTH + self.GAP,
                             bottom, 'F')

    def handle_event(self, event):
        if event.type in (SDL_KEYDOWN, SDL_KEYUP):
            slots = {SDLK_r: self.sword, SDLK_f: self.buff}
            slot = slots.get(event.key)
            if slot is not None:
                if event.type == SDL_KEYDOWN:
                    slot.roll()
                return True
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            y = get_canvas_height() - 1 - event.y
            for slot in (self.sword, self.buff):
                if slot.contains(event.x, y):
                    slot.roll()
                    return True
        return False

    def update(self, delta_time):
        self.buff.set_type(self.player.buff_dice_type)
        face = self.sword.update(delta_time)
        if face is not None:
            index = face - 1
            self.player.sword_stacks[index] = min(
                self.player.sword_stacks[index] + 1,
                self.player.sword_max_stacks[index],
            )
        self.buff.update(delta_time)

    def draw(self):
        self.sword.draw(self.frame, self.font)
        self.buff.draw(self.frame, self.font)
