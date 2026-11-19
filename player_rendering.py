from pico2d import load_font, load_image
from sdl2 import SDL_SetTextureColorMod

from player_movement import DOWN, FACING_AXES, LEFT, RIGHT, UP


# Down attack poses are wider than the matching idle and run sprites.
DOWN_ATTACK_WIDTH_SCALE = 0.86


class PlayerRenderer:
    DRAW_SCALE = 1.2
    DAMAGE_POPUP_RISE = 24
    DASH_CHOP_TRAIL_ADVANCE = 20  # Display pixels.
    ANIMATION_ROWS = {UP: 0, RIGHT: 2, DOWN: 4, LEFT: 2}
    # Offsets in source pixels, using Pico2d's bottom-left coordinates.
    HORIZONTAL_SLASH_TRAIL_OFFSETS = {DOWN: (0, -18), LEFT: (-18, 0), RIGHT: (18, 0)}
    # (x offset, depth below cell center) in original sprite pixels, indexed by combo and frame.
    ATTACK_SHADOW_CONTACTS = {
        RIGHT: (
            ((-6, 34), (-10, 34), (-8, 32), (-15, 34), (-7, 32),
             (-11, 34), (-8, 34), (-7, 32), (-4, 32), (-2, 32)),
            ((-10, 28), (-4, 30), (-2, 30), (-2, 30), (2, 30),
             (6, 32), (6, 30), (6, 30), (5, 32), (7, 32)),
            ((-4, 30), (-17, 32), (-14, 36), (-10, 36), (-8, 38),
             (-4, 40), (-8, 32), (-8, 20), (-8, 22), (-12, 22)),
        ),
        UP: (
            ((3, 36), (-2, 36), (1, 36), (4, 36), (6, 44),
             (10, 42), (-9, 38), (-6, 36), (-1, 36), (2, 36)),
            ((-13, 36), (-5, 38), (-2, 36), (-2, 36), (5, 36),
             (6, 46), (8, 46), (6, 44), (8, 44), (4, 44)),
            ((3, 36), (1, 36), (3, 36), (1, 44), (3, 44),
             (3, 44), (5, 44), (-4, 36), (-13, 36), (-11, 36)),
        ),
        DOWN: (
            ((2, 38), (4, 38), (4, 38), (3, 38), (4, 38),
             (4, 38), (5, 38), (5, 38), (5, 38), (5, 38)),
            ((2, 38), (1, 38), (5, 36), (4, 36), (4, 38),
             (4, 38), (3, 36), (4, 46), (4, 46), (5, 46)),
            ((-3, 36), (-4, 36), (-2, 38), (-3, 44), (-4, 44),
             (-4, 46), (-1, 40), (1, 32), (3, 34), (4, 32)),
        ),
    }

    def __init__(self):
        self.damage_font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 16)
        self.shadow = load_image('asset/player_shadow.png')
        self.idle = load_image('asset/Player_Idle.png')
        self.run = load_image('asset/Run.png')
        self.attack_sheets = {
            UP: (load_image('asset/attack_up.png'), load_image('asset/attack_up_trail.png')),
            DOWN: (load_image('asset/attack_down.png'), load_image('asset/attack_down_trail.png')),
            RIGHT: (load_image('asset/attack_sheet.png'), load_image('asset/attack_trail.png')),
        }
        self.sword_skill_sheets = {
            'QUICK_THRUST': self._load_sword_skill_sheets('quick_thrust'),
            'HORIZONTAL_SLASH': self._load_sword_skill_sheets('horizontal_slash'),
            'DASH_CHOP': self._load_sword_skill_sheets('dash_chop'),
        }

    def _load_sword_skill_sheets(self, skill):
        sheets = {}
        for direction, name in ((UP, 'up'), (DOWN, 'down'), (LEFT, 'left'), (RIGHT, 'right')):
            width, height = self._trail_cell_size(direction)
            path = f'asset/skills/{skill}/{skill}_{name}'
            sheets[direction] = (
                load_image(f'{path}_motion_100x100.png'),
                load_image(f'{path}_fx_{width}x{height}.png'),
            )
        return sheets

    @staticmethod
    def _trail_cell_size(direction):
        return (100, 180) if direction in (UP, DOWN) else (180, 100)

    def draw(self, player):
        self._draw_shadow(player)
        if player.state in ('IDLE', 'RUN'):
            image = self.idle if player.state == 'IDLE' else self.run
            self._draw_frame(player, image, self.ANIMATION_ROWS[player.dir])
        elif player.state == 'ATTACK':
            self._draw_attack(player)
        elif player.state in self.sword_skill_sheets:
            self._draw_sword_skill(player)
        self._draw_damage_popups(player)

    def _draw_damage_popups(self, player):
        for popup in player.damage_popups:
            progress = 1.0 - popup['remaining'] / player.DAMAGE_POPUP_TIME
            text = f"-{popup['damage']:g}"
            x = popup['x'] - len(text) * 5
            y = popup['y'] + self.DAMAGE_POPUP_RISE * progress
            self.damage_font.draw(x + 1, y - 1, text, (35, 7, 5))
            self.damage_font.draw(x, y, text, (255, 95, 64))

    def _draw_shadow(self, player):
        x = player.x
        y = player.y - player.FOOT_OFFSET_Y
        if player.state == 'ATTACK':
            direction = RIGHT if player.dir == LEFT else player.dir
            offset_x, depth = self.ATTACK_SHADOW_CONTACTS[direction][player.attack_combo][player.frame]
            if player.dir == LEFT:
                offset_x = -offset_x
            elif direction == DOWN:
                offset_x *= DOWN_ATTACK_WIDTH_SCALE
            x += offset_x * self.DRAW_SCALE
            y += (player.FOOT_OFFSET_Y - depth) * self.DRAW_SCALE
        self.shadow.draw(x, y, 54, 8)

    def _draw_attack(self, player):
        direction = RIGHT if player.dir == LEFT else player.dir
        motion, trail = self.attack_sheets[direction]
        cell_width, cell_height = self._trail_cell_size(direction)
        width_scale = DOWN_ATTACK_WIDTH_SCALE if direction == DOWN else 1
        self._draw_frame(player, motion, player.attack_combo, width_scale=width_scale)
        self._draw_frame(player, trail, player.attack_combo, cell_width, cell_height,
                         width_scale=width_scale, tint_on_hit=False)

    def _draw_sword_skill(self, player):
        motion, trail = self.sword_skill_sheets[player.state][player.dir]
        cell_width, cell_height = self._trail_cell_size(player.dir)
        offset = (0, 0)
        if player.state == 'HORIZONTAL_SLASH':
            offset = self.HORIZONTAL_SLASH_TRAIL_OFFSETS.get(player.dir, (0, 0))
        elif player.state == 'DASH_CHOP' and 4 <= player.frame <= 6:
            # Move the descending trail and impact, after the charging frames.
            dx, dy = FACING_AXES[player.dir]
            distance = self.DASH_CHOP_TRAIL_ADVANCE / self.DRAW_SCALE
            offset = (dx * distance, dy * distance)
        # These skills have separate left-facing sheets.
        self._draw_frame(player, motion, 0, mirror_left=False)
        self._draw_frame(player, trail, 0, cell_width, cell_height, mirror_left=False,
                         offset=offset, tint_on_hit=False)

    def _draw_frame(self, player, image, row, cell_width=100, cell_height=100, *, width_scale=1,
                    mirror_left=True, offset=(0, 0), tint_on_hit=True):
        left = player.frame * cell_width
        bottom = row * cell_height
        draw_width = round(cell_width * self.DRAW_SCALE * width_scale)
        draw_height = round(cell_height * self.DRAW_SCALE)
        offset_x, offset_y = offset
        draw_x = player.x + offset_x * self.DRAW_SCALE
        draw_y = player.y + player.FOOT_OFFSET_Y * (self.DRAW_SCALE - 1) + offset_y * self.DRAW_SCALE

        hit_flash = tint_on_hit and player.hit_flash_remaining > 0
        if hit_flash:
            SDL_SetTextureColorMod(image.texture, 255, 80, 80)
        if mirror_left and player.dir == LEFT:
            image.clip_composite_draw(
                left, bottom, cell_width, cell_height, 0, 'h', draw_x, draw_y, draw_width, draw_height)
        else:
            image.clip_draw(left, bottom, cell_width, cell_height, draw_x, draw_y, draw_width, draw_height)
        if hit_flash:
            SDL_SetTextureColorMod(image.texture, 255, 255, 255)
