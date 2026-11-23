from math import hypot

from pico2d import load_font, load_image
from sdl2 import SDL_SetTextureColorMod

from bounding_box import BoundingBox
from damage_popups import add_damage_popup, draw_damage_popups, update_damage_popups
from lobby_map import FOOT_RADIUS
from player_attack_contact import PlayerAttackContact
from player_movement import DOWN, LEFT, RIGHT, UP, move_position


class ArmoredWraith:
    CELL_SIZE = 100
    DRAW_SCALE = 1.2
    FEET_TO_CENTER = 44
    FRAME_COUNT = 6
    WALK_FRAME_TIME = 0.10
    # Wind-up varies per frame. The fourth frame is the hit; the fifth is the fading trail.
    ATTACK_FRAME_ENDS = (0.10, 0.20, 0.35, 0.45, 0.55, 0.65)
    HIT_FRAME = 3
    ATTACK_COOLDOWN = 0.45
    ATTACK_DAMAGE = 12
    MAX_HP = 200
    AGGRO_RADIUS = 190
    MOVE_SPEED = 100

    ROWS = {UP: 0, DOWN: 1, LEFT: 2, RIGHT: 3}
    # Fourth-frame alpha bounds in each trail cell, in Pico2d's bottom-left coordinates.
    TRAIL_BOUNDS = {
        UP: (6, 114, 94, 164),
        DOWN: (6, 14, 94, 72),
        LEFT: (8, 12, 66, 84),
        RIGHT: (116, 12, 172, 84),
    }

    def __init__(self, position):
        self.x, self.foot_y = position
        self.hp = self.MAX_HP
        self.facing = DOWN
        self.walk_frame = 0
        self._walk_time = 0.0
        self._attack_time = None
        self._attack_hit = False
        self._cooldown = 0.0
        self.stun_remaining = 0.0
        self.damage_popups = []
        self._player_contact = PlayerAttackContact()

        self.walk_sheet = load_image('asset/m1.png')
        self.attack_sheet = load_image('asset/m1_attack.png')
        self.vertical_trail = load_image('asset/m1_attack_udtrail.png')
        self.horizontal_trail = load_image('asset/m1_attack_lrtrail.png')
        self.damage_font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 16)
        self.shadow = load_image('asset/player_shadow.png')

    @property
    def _sprite_y(self):
        return self.foot_y + self.FEET_TO_CENTER

    @property
    def movement_box(self):
        if self.hp <= 0:
            return None
        footprint = BoundingBox(self.x - 15, self.foot_y - 8, self.x + 15, self.foot_y + 8)
        return footprint.expanded(FOOT_RADIUS)

    @property
    def hurtbox(self):
        if self.hp <= 0:
            return None
        return BoundingBox(self.x - 25, self.foot_y + 2, self.x + 25, self.foot_y + 88)

    def blocks(self, x, foot_y):
        box = self.movement_box
        return box is not None and box.contains(x, foot_y)

    def update(self, delta_time):
        update_damage_popups(self.damage_popups, delta_time)
        self._player_contact.update(delta_time)
        self.stun_remaining = max(0.0, self.stun_remaining - delta_time)
        self._cooldown = max(0.0, self._cooldown - delta_time)

    def check_attack(self, player):
        box = self.hurtbox
        if box is not None:
            hit = self._player_contact.hit(player, box)
            if hit is not None:
                damage, offset = hit
                self._take_damage(damage, offset)

    def receive_parry(self, damage, stun_duration):
        self._attack_time = None
        self.stun_remaining = max(self.stun_remaining, stun_duration)
        self._take_damage(damage, 0)

    def _take_damage(self, damage, offset):
        actual = min(self.hp, damage)
        if actual <= 0:
            return
        self.hp -= actual
        add_damage_popup(self.damage_popups, actual, self.x + offset, self.foot_y + 98)
        if self.hp <= 0:
            self._attack_time = None

    def act(self, player, delta_time, can_move):
        if delta_time <= 1e-9:
            return
        if self.hp <= 0 or player.hp <= 0 or self.stun_remaining > 0:
            self._attack_time = None
            return

        body = player.renderer.body_box(player)
        if self._attack_time is not None:
            self._advance_attack(player, body, delta_time)
            return

        player_foot_y = player.y - player.FOOT_OFFSET_Y
        dx, dy = player.x - self.x, player_foot_y - self.foot_y
        distance = hypot(dx, dy)
        if distance > self.AGGRO_RADIUS or body is None:
            self.walk_frame = 0
            return

        self.facing = self._facing_toward(dx, dy)
        # Use a small inset when deciding to swing, so the target is in reach before the wind-up.
        if self._swing_bounds().expanded(-8).overlaps(body):
            self.walk_frame = 0
            if self._cooldown <= 0:
                self._attack_time = 0.0
                self._attack_hit = False
            return

        def can_step(x, foot_y):
            clears_player = abs(x - player.x) > 24 or abs(foot_y - player_foot_y) > 17
            return clears_player and can_move(x, foot_y)

        axes = ((dx > 8) - (dx < -8), (dy > 8) - (dy < -8))
        previous = self.x, self.foot_y
        self.x, self.foot_y = move_position(previous, axes, min(distance, self.MOVE_SPEED * delta_time),
                                               can_move=can_step, foot_offset_y=0, max_step=6)
        if (self.x, self.foot_y) == previous:
            self.walk_frame = 0
        else:
            self._walk_time += delta_time
            self.walk_frame = int((self._walk_time + 1e-9) / self.WALK_FRAME_TIME) % self.FRAME_COUNT

    @staticmethod
    def _facing_toward(dx, dy):
        if abs(dx) >= abs(dy):
            return RIGHT if dx >= 0 else LEFT
        return UP if dy > 0 else DOWN

    def _advance_attack(self, player, body, delta_time):
        self._attack_time += delta_time
        if self._attack_time >= self.ATTACK_FRAME_ENDS[-1] - 1e-9:
            self._attack_time = None
            self._cooldown = self.ATTACK_COOLDOWN
            return

        attack = self.attack_box()
        if not self._attack_hit and attack is not None and body is not None and attack.overlaps(body):
            self._attack_hit = True
            player.take_damage(self.ATTACK_DAMAGE, attacker=self)

    def _attack_frame(self):
        return sum(self._attack_time + 1e-9 >= end for end in self.ATTACK_FRAME_ENDS[:-1])

    def _trail_cell(self):
        if self.facing in (UP, DOWN):
            return self.vertical_trail, self.ROWS[self.facing], 100, 180
        return self.horizontal_trail, self.ROWS[self.facing] - 2, 180, 100

    def _swing_bounds(self):
        _, _, width, height = self._trail_cell()
        left, bottom, right, top = self.TRAIL_BOUNDS[self.facing]
        scale = self.DRAW_SCALE
        x = self.x - width * scale / 2
        y = self._sprite_y - height * scale / 2
        return BoundingBox(x + left * scale, y + bottom * scale, x + right * scale, y + top * scale)

    def attack_box(self):
        if self._attack_time is not None and self._attack_frame() == self.HIT_FRAME:
            return self._swing_bounds()
        return None

    def draw(self):
        if self.hp > 0:
            self.shadow.draw(self.x, self.foot_y, 49, 8)
            attacking = self._attack_time is not None
            sheet = self.attack_sheet if attacking else self.walk_sheet
            frame = self._attack_frame() if attacking else self.walk_frame
            cell = self.CELL_SIZE
            draw_size = round(cell * self.DRAW_SCALE)
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 140, 185, 255)
            sheet.clip_draw(frame * cell, self.ROWS[self.facing] * cell, cell, cell,
                            self.x, self._sprite_y, draw_size, draw_size)
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 255, 255, 255)
            if attacking and frame in (self.HIT_FRAME, self.HIT_FRAME + 1):
                trail, row, width, height = self._trail_cell()
                trail.clip_draw(frame * width, row * height, width, height, self.x, self._sprite_y,
                                round(width * self.DRAW_SCALE), round(height * self.DRAW_SCALE))
        draw_damage_popups(self.damage_font, self.damage_popups)
