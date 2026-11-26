from math import ceil, hypot

from pico2d import draw_rectangle, load_font, load_image
from sdl2 import SDL_SetTextureColorMod

from bounding_box import BoundingBox
from damage_popups import add_damage_popup, draw_damage_popups, update_damage_popups
from lobby_map import FOOT_RADIUS
from player_attack_contact import HIT_FLASH_DURATION, PlayerAttackContact
from player_movement import DOWN, LEFT, RIGHT, UP, move_position


class Enemy:
    """World-space hitboxes, damage handling and health display for hostile actors."""

    FOOTPRINT_HALF_WIDTH = 15
    FOOTPRINT_HALF_HEIGHT = 8
    BODY_HALF_WIDTH = 25
    BODY_HEIGHT = 88
    HEALTH_BAR_WIDTH = 56
    HEALTH_BAR_HEIGHT = 8
    HEALTH_BAR_OFFSET_Y = 99
    PATROL_SPEED = 70
    WALK_FRAME_TIME = 0.10
    WALK_FRAME_COUNT = 6
    WAYPOINT_TOLERANCE = 8

    def __init__(self, position, *, patrol=(), patrol_area=None):
        self.x, self.foot_y = position
        self._patrol = tuple(patrol)
        self._patrol_area = patrol_area
        self._patrol_index = 0
        self.facing = DOWN
        self.walk_frame = 0
        self._walk_time = 0.0
        self.hp = self.MAX_HP
        self._attack_time = None
        self._cooldown = 0.0
        self.stun_remaining = 0.0
        self.damage_popups = []
        self.hit_flash_remaining = 0.0
        self._player_contact = PlayerAttackContact()
        self.damage_font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 16)
        self.shadow = load_image('asset/player_shadow.png')

    @staticmethod
    def _screen_position(camera, x, y):
        return camera.project(x, y) if camera is not None else (x, y)

    @property
    def movement_box(self):
        if self.hp <= 0:
            return None
        half_w, half_h = self.FOOTPRINT_HALF_WIDTH, self.FOOTPRINT_HALF_HEIGHT
        footprint = BoundingBox(self.x - half_w, self.foot_y - half_h, self.x + half_w, self.foot_y + half_h)
        return footprint.expanded(FOOT_RADIUS)

    @property
    def hurtbox(self):
        if self.hp <= 0:
            return None
        half_w = self.BODY_HALF_WIDTH
        return BoundingBox(self.x - half_w, self.foot_y + 2,
                           self.x + half_w, self.foot_y + self.BODY_HEIGHT)

    def blocks(self, x, foot_y):
        box = self.movement_box
        return box is not None and box.contains(x, foot_y)

    def update(self, delta_time):
        update_damage_popups(self.damage_popups, delta_time)
        self._player_contact.update(delta_time)
        self.hit_flash_remaining = max(0.0, self.hit_flash_remaining - delta_time)
        self.stun_remaining = max(0.0, self.stun_remaining - delta_time)
        self._cooldown = max(0.0, self._cooldown - delta_time)

    def check_attack(self, player):
        box = self.hurtbox
        if box is not None:
            hit = self._player_contact.hit(player, box)
            if hit is not None:
                damage, offset, critical = hit
                self._take_damage(damage, offset, critical=critical)

    def receive_parry(self, damage, stun_duration, *, critical=False):
        self._attack_time = None
        self.stun_remaining = max(self.stun_remaining, stun_duration)
        self._take_damage(damage, 0, critical=critical)

    def _take_damage(self, damage, offset, *, critical=False):
        actual = min(self.hp, damage)
        if actual <= 0:
            return
        self.hp -= actual
        self.hit_flash_remaining = HIT_FLASH_DURATION
        popup_y = self.foot_y + self.HEALTH_BAR_OFFSET_Y + self.HEALTH_BAR_HEIGHT + 15
        add_damage_popup(self.damage_popups, actual, self.x + offset, popup_y, critical=critical)
        if self.hp <= 0:
            self._attack_time = None

    def _movement_check(self, player_x, player_foot_y, can_move):
        clearance_x = self.FOOTPRINT_HALF_WIDTH + FOOT_RADIUS
        clearance_y = self.FOOTPRINT_HALF_HEIGHT + FOOT_RADIUS

        def can_step(x, foot_y):
            clears_player = abs(x - player_x) > clearance_x or abs(foot_y - player_foot_y) > clearance_y
            return clears_player and self._in_patrol_area(x, foot_y) and can_move(x, foot_y)

        return can_step

    def _in_patrol_area(self, x, foot_y):
        return self._patrol_area is None or self._patrol_area.contains(x, foot_y)

    def _patrol_step(self, delta_time, can_step):
        for _ in self._patrol:
            target_x, target_y = self._patrol[self._patrol_index]
            dx, dy = target_x - self.x, target_y - self.foot_y
            if max(abs(dx), abs(dy)) > self.WAYPOINT_TOLERANCE:
                self.facing = self._facing_toward(dx, dy)
                if self._walk_toward(dx, dy, hypot(dx, dy), self.PATROL_SPEED, delta_time, can_step):
                    return
            # Move on when a patrol point is reached or the next step is obstructed.
            self._patrol_index = (self._patrol_index + 1) % len(self._patrol)
        self.walk_frame = 0

    def _walk_toward(self, dx, dy, distance, speed, delta_time, can_step):
        dead_zone = self.WAYPOINT_TOLERANCE
        axes = ((dx > dead_zone) - (dx < -dead_zone),
                (dy > dead_zone) - (dy < -dead_zone))
        previous = self.x, self.foot_y
        self.x, self.foot_y = move_position(previous, axes, min(distance, speed * delta_time),
                                            can_move=can_step, foot_offset_y=0, max_step=6)
        if (self.x, self.foot_y) == previous:
            self.walk_frame = 0
            return False
        self._walk_time += delta_time
        self.walk_frame = int((self._walk_time + 1e-9) / self.WALK_FRAME_TIME) % self.WALK_FRAME_COUNT
        return True

    @staticmethod
    def _facing_toward(dx, dy):
        if abs(dx) >= abs(dy):
            return RIGHT if dx >= 0 else LEFT
        return UP if dy > 0 else DOWN

    def _draw_body(self, sheet, flash_sheet, frame, row, cell, x, y, draw_size):
        flashing = self.hit_flash_remaining > 0
        image = flash_sheet if flashing else sheet
        tinted = not flashing and self.stun_remaining > 0
        if tinted:
            SDL_SetTextureColorMod(image.texture, 140, 185, 255)
        image.clip_draw(frame * cell, row * cell, cell, cell, x, y, draw_size, draw_size)
        if tinted:
            SDL_SetTextureColorMod(image.texture, 255, 255, 255)

    def _draw_health_bar(self, x, foot_y):
        left = round(x) - self.HEALTH_BAR_WIDTH // 2
        right = left + self.HEALTH_BAR_WIDTH - 1
        bottom = round(foot_y) + self.HEALTH_BAR_OFFSET_Y
        top = bottom + self.HEALTH_BAR_HEIGHT - 1
        fill_width = ceil((self.HEALTH_BAR_WIDTH - 2) * min(self.hp, self.MAX_HP) / self.MAX_HP)

        draw_rectangle(left, bottom, right, top, 40, 24, 21, filled=True)
        draw_rectangle(left, bottom, right, top, 126, 94, 72)
        draw_rectangle(left + 1, bottom + 1, left + fill_width, top - 1, 195, 56, 43, filled=True)

    def _draw_damage_popups(self, camera):
        draw_damage_popups(self.damage_font, self.damage_popups, camera=camera)
