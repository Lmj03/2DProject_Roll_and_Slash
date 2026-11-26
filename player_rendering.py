from dataclasses import dataclass
from json import load
from pathlib import Path

from pico2d import load_font, load_image
from sdl2 import SDL_SetTextureColorMod

from bounding_box import BoundingBox
from damage_popups import draw_damage_popups
from player_movement import DOWN, FACING_AXES, LEFT, RIGHT, UP


# Down attack poses are wider than the matching idle and run sprites.
DOWN_ATTACK_WIDTH_SCALE = 0.86
ASSET_DIR = Path(__file__).resolve().parent / 'asset'
SPIN_SHEET_PATH = 'asset/skills/sword_spin/sword_spin_sheet.png'


@dataclass(frozen=True)
class SpriteFrame:
    image: object
    row: int = 0
    width: int = 100
    height: int = 100
    width_scale: float = 1.0
    mirror_left: bool = True
    offset: tuple = (0, 0)
    column: int | None = None


class PlayerRenderer:
    DRAW_SCALE = 1.2
    DASH_CHOP_TRAIL_ADVANCE = 20  # Display pixels.
    FLASH_TRAIL_CELL = (320, 64)
    FLASH_TRAIL_HEIGHT = 80  # Display pixels.
    FLASH_BODY_COLUMNS = (2, 3, 4, 0)
    PARRY_COLUMNS = {'PARRY': (0, 1, 2, 2, 0), 'PARRY_COUNTER': (3, 4, 5, 6, 7)}
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
        self.flash_trail = load_image('asset/skills/flash_strike/flash_lightning_sheet.png')
        with (ASSET_DIR / 'player_body_bounds.json').open(encoding='utf-8') as bounds_file:
            self._bounds_by_path = load(bounds_file)
        with (ASSET_DIR / 'player_attack_bounds.json').open(encoding='utf-8') as bounds_file:
            attack_bounds = load(bounds_file)
        self._spin_attack_bounds = attack_bounds.pop(SPIN_SHEET_PATH)[0][0]
        self._bounds_by_path.update(attack_bounds)
        self._bounds_by_image = {}
        self.spin_sheet = self._load_sprite(SPIN_SHEET_PATH)
        self.idle = self._load_sprite('asset/Player_Idle.png')
        self.run = self._load_sprite('asset/Run.png')
        self.attack_sheets = {
            UP: (self._load_sprite('asset/attack_up.png'), self._load_sprite('asset/attack_up_trail.png')),
            DOWN: (self._load_sprite('asset/attack_down.png'), self._load_sprite('asset/attack_down_trail.png')),
            RIGHT: (self._load_sprite('asset/attack_sheet.png'), self._load_sprite('asset/attack_trail.png')),
        }
        self.sword_skill_sheets = {
            'QUICK_THRUST': self._load_sword_skill_sheets('quick_thrust'),
            'HORIZONTAL_SLASH': self._load_sword_skill_sheets('horizontal_slash'),
            'DASH_CHOP': self._load_sword_skill_sheets('dash_chop'),
        }
        self.parry_sheets = self._load_sword_skill_sheets('parry')

    def _load_sprite(self, path):
        image = load_image(path)
        if path in self._bounds_by_path:
            self._bounds_by_image[image] = self._bounds_by_path[path]
        return image

    def _load_sword_skill_sheets(self, skill):
        sheets = {}
        for direction, name in ((UP, 'up'), (DOWN, 'down'), (LEFT, 'left'), (RIGHT, 'right')):
            width, height = self._trail_cell_size(direction, skill)
            path = f'asset/skills/{skill}/{skill}_{name}'
            sheets[direction] = (
                self._load_sprite(f'{path}_motion_100x100.png'),
                self._load_sprite(f'{path}_fx_{width}x{height}.png'),
            )
        return sheets

    @staticmethod
    def _trail_cell_size(direction, skill=None):
        vertical = direction in (UP, DOWN)
        if skill == 'horizontal_slash':
            return (200, 270) if vertical else (360, 150)
        return (100, 180) if vertical else (180, 100)

    def draw(self, player, camera=None):
        if player.flash_path is not None:
            self._draw_flash_trail(player, camera)
        self._draw_shadow(player, camera)
        self._draw_frame(player, self._body_frame(player), tint_on_hit=True, camera=camera)
        trail = self._trail_frame(player)
        if trail is not None:
            self._draw_frame(player, trail, tint_on_hit=False, camera=camera)
        draw_damage_popups(self.damage_font, player.damage_popups, player.DAMAGE_POPUP_TIME, camera=camera)

    def _draw_flash_trail(self, player, camera=None):
        path = player.flash_path
        if path.length <= 0:
            return
        width, height = self.FLASH_TRAIL_CELL
        x, y = path.center
        if camera is not None:
            x, y = camera.project(x, y)
        self.flash_trail.clip_composite_draw(player.frame * width, 0, width, height,
                                             path.angle, '', x, y, max(1, round(path.length)),
                                             self.FLASH_TRAIL_HEIGHT)

    def _draw_shadow(self, player, camera=None):
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
        if camera is not None:
            x, y = camera.project(x, y)
        self.shadow.draw(x, y, 54, 8)

    def _body_frame(self, player):
        if player.state == 'SWORD_SPIN':
            return SpriteFrame(self.spin_sheet, width=180, height=180, mirror_left=False)
        if player.state == 'FLASH_STRIKE':
            motion, _ = self.sword_skill_sheets['QUICK_THRUST'][player.dir]
            return SpriteFrame(motion, mirror_left=False, column=self.FLASH_BODY_COLUMNS[player.frame])
        if player.state == 'ATTACK':
            direction = RIGHT if player.dir == LEFT else player.dir
            motion, _ = self.attack_sheets[direction]
            scale = DOWN_ATTACK_WIDTH_SCALE if direction == DOWN else 1
            return SpriteFrame(motion, row=player.attack_combo, width_scale=scale)
        if player.state in self.PARRY_COLUMNS:
            motion, _ = self.parry_sheets[player.dir]
            return SpriteFrame(motion, mirror_left=False, column=self.PARRY_COLUMNS[player.state][player.frame])
        if player.state in self.sword_skill_sheets:
            motion, _ = self.sword_skill_sheets[player.state][player.dir]
            return SpriteFrame(motion, mirror_left=False)
        image = self.run if player.state == 'RUN' else self.idle
        return SpriteFrame(image, row=self.ANIMATION_ROWS[player.dir])

    def _trail_frame(self, player):
        width, height = self._trail_cell_size(player.dir, player.state.lower())
        if player.state == 'ATTACK':
            direction = RIGHT if player.dir == LEFT else player.dir
            _, trail = self.attack_sheets[direction]
            scale = DOWN_ATTACK_WIDTH_SCALE if direction == DOWN else 1
            return SpriteFrame(trail, row=player.attack_combo, width=width, height=height,
                               width_scale=scale)
        if player.state in self.PARRY_COLUMNS:
            _, trail = self.parry_sheets[player.dir]
            column = self.PARRY_COLUMNS[player.state][player.frame]
            return SpriteFrame(trail, width=width, height=height, mirror_left=False, column=column)
        if player.state not in self.sword_skill_sheets:
            return None
        _, trail = self.sword_skill_sheets[player.state][player.dir]
        offset = (0, 0)
        if player.state == 'HORIZONTAL_SLASH':
            offset = self.HORIZONTAL_SLASH_TRAIL_OFFSETS.get(player.dir, (0, 0))
        elif player.state == 'DASH_CHOP' and 4 <= player.frame <= 6:
            dx, dy = FACING_AXES[player.dir]
            distance = self.DASH_CHOP_TRAIL_ADVANCE / self.DRAW_SCALE
            offset = (dx * distance, dy * distance)
        return SpriteFrame(trail, width=width, height=height, mirror_left=False, offset=offset)

    def _placement(self, player, sprite):
        offset_x, offset_y = sprite.offset
        x = player.x + offset_x * self.DRAW_SCALE
        y = player.y + player.FOOT_OFFSET_Y * (self.DRAW_SCALE - 1) + offset_y * self.DRAW_SCALE
        w = round(sprite.width * self.DRAW_SCALE * sprite.width_scale)
        h = round(sprite.height * self.DRAW_SCALE)
        mirror = sprite.mirror_left and player.dir == LEFT
        return x, y, w, h, mirror

    def _world_bounds(self, player, sprite, local=None):
        if local is None:
            column = player.frame if sprite.column is None else sprite.column
            local = self._bounds_by_image[sprite.image][sprite.row][column]
        if local is None:
            return None
        left, bottom, right, top = local
        x, y, w, h, mirror = self._placement(player, sprite)
        if mirror:
            left, right = sprite.width - right, sprite.width - left
        origin_x, origin_y = x - w / 2, y - h / 2
        sx, sy = w / sprite.width, h / sprite.height
        return BoundingBox(origin_x + left * sx, origin_y + bottom * sy,
                           origin_x + right * sx, origin_y + top * sy)

    def body_box(self, player):
        return self._world_bounds(player, self._body_frame(player))

    def attack_box(self, player):
        # The counter is applied to the intercepted attacker at contact time.
        if player.state in self.PARRY_COLUMNS:
            return None
        if player.state == 'FLASH_STRIKE':
            return player.flash_path.attack_box() if player.flash_path is not None else None
        if player.state == 'SWORD_SPIN':
            return self._world_bounds(player, self._body_frame(player), self._spin_attack_bounds)
        # Dash streaks show movement. The final downward strike is the damaging frame.
        if player.state == 'DASH_CHOP' and player.frame != 5:
            return None
        trail = self._trail_frame(player)
        return self._world_bounds(player, trail) if trail is not None else None

    def _draw_frame(self, player, sprite, *, tint_on_hit, camera=None):
        column = player.frame if sprite.column is None else sprite.column
        left = column * sprite.width
        bottom = sprite.row * sprite.height
        x, y, w, h, mirror = self._placement(player, sprite)
        if camera is not None:
            x, y = camera.project(x, y)
        hit_flash = tint_on_hit and player.hit_flash_remaining > 0
        if hit_flash:
            SDL_SetTextureColorMod(sprite.image.texture, 255, 80, 80)
        if mirror:
            sprite.image.clip_composite_draw(left, bottom, sprite.width, sprite.height, 0, 'h', x, y, w, h)
        else:
            sprite.image.clip_draw(left, bottom, sprite.width, sprite.height, x, y, w, h)
        if hit_flash:
            SDL_SetTextureColorMod(sprite.image.texture, 255, 255, 255)
