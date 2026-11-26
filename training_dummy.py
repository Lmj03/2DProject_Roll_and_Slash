from pico2d import load_font, load_image

from bounding_box import BoundingBox
from damage_popups import add_damage_popup, draw_damage_popups, update_damage_popups
from lobby_map import FOOT_RADIUS, TRAINING_DUMMY_POSITION
from player_attack_contact import HIT_FLASH_DURATION, PlayerAttackContact


class TrainingDummy:
    CELL_SIZE = 100
    DRAW_SIZE = 110
    FEET_TO_CENTER = 37
    HIT_FRAME_TIME = 0.08
    HIT_FRAME_COUNT = 3

    def __init__(self):
        self.x, self.foot_y = TRAINING_DUMMY_POSITION
        self.sheet = load_image('asset/training_dummy_sheet.png')
        self.flash_sheet = load_image('asset/hit_flash/training_dummy_sheet.png')
        self.damage_font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 16)
        self.damage_popups = []
        footprint = BoundingBox(self.x - 15, self.foot_y - 8,
                               self.x + 15, self.foot_y + 8)
        self.hurtbox = BoundingBox(self.x - 24, self.foot_y + 7,
                                   self.x + 24, self.foot_y + 82)
        self.movement_box = footprint.expanded(FOOT_RADIUS)
        self._hit_time = None
        self.hit_flash_remaining = 0.0
        self.stun_remaining = 0.0
        self._player_contact = PlayerAttackContact()

    def blocks(self, x, foot_y):
        return self.movement_box.contains(x, foot_y)

    def check_attack(self, player):
        hit = self._player_contact.hit(player, self.hurtbox)
        if hit is not None:
            damage, offset, critical = hit
            self._show_hit(damage, self.x + offset, critical=critical)

    def receive_parry(self, damage, stun_duration, *, critical=False):
        self.stun_remaining = max(self.stun_remaining, stun_duration)
        self._show_hit(damage, self.x, critical=critical)

    def _show_hit(self, damage, popup_x, *, critical=False):
        self._hit_time = 0.0
        self.hit_flash_remaining = HIT_FLASH_DURATION
        add_damage_popup(self.damage_popups, damage, popup_x, self.hurtbox.top + 10, critical=critical)

    def update(self, delta_time):
        update_damage_popups(self.damage_popups, delta_time)
        self._player_contact.update(delta_time)
        self.hit_flash_remaining = max(0.0, self.hit_flash_remaining - delta_time)
        self.stun_remaining = max(0.0, self.stun_remaining - delta_time)
        if self._hit_time is not None:
            self._hit_time += delta_time
            if self._hit_time >= self.HIT_FRAME_TIME * self.HIT_FRAME_COUNT:
                self._hit_time = None

    def draw(self, camera=None):
        frame = 0 if self._hit_time is None else 1 + int(self._hit_time / self.HIT_FRAME_TIME)
        if frame == 0 and self.stun_remaining > 0:
            frame = self.HIT_FRAME_COUNT
        sheet = self.flash_sheet if self.hit_flash_remaining > 0 else self.sheet
        x, y = self.x, self.foot_y + self.FEET_TO_CENTER
        if camera is not None:
            x, y = camera.project(x, y)
        sheet.clip_draw(frame * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
                        x, y, self.DRAW_SIZE, self.DRAW_SIZE)
        draw_damage_popups(self.damage_font, self.damage_popups, camera=camera)
