from pico2d import load_font, load_image

from bounding_box import BoundingBox
from damage_popups import add_damage_popup, draw_damage_popups, update_damage_popups
from lobby_map import FOOT_RADIUS, TRAINING_DUMMY_POSITION


class TrainingDummy:
    CELL_SIZE = 100
    DRAW_SIZE = 110
    FEET_TO_CENTER = 37
    HIT_FRAME_TIME = 0.08
    HIT_FRAME_COUNT = 3

    def __init__(self):
        self.x, self.foot_y = TRAINING_DUMMY_POSITION
        self.sheet = load_image('asset/training_dummy_sheet.png')
        self.damage_font = load_font('asset/fonts/SourceCodePro-Bold.ttf', 16)
        self.damage_popups = []
        footprint = BoundingBox(self.x - 15, self.foot_y - 8,
                               self.x + 15, self.foot_y + 8)
        self.hurtbox = BoundingBox(self.x - 24, self.foot_y + 7,
                                   self.x + 24, self.foot_y + 82)
        self.movement_box = footprint.expanded(FOOT_RADIUS)
        self._hit_time = None
        self._last_attack_id = None
        self._spin_hit_remaining = 0.0
        self._spin_popup_index = 0

    def blocks(self, x, foot_y):
        return self.movement_box.contains(x, foot_y)

    def check_attack(self, player):
        spinning = player.state == 'SWORD_SPIN'
        if player.attack_id == self._last_attack_id and (not spinning or self._spin_hit_remaining > 1e-9):
            return
        attack = player.renderer.attack_box(player)
        if attack is None:
            return
        overlaps = attack.ellipse_overlaps if spinning else attack.overlaps
        if not overlaps(self.hurtbox):
            return
        self._hit_time = 0.0
        damage = player.attack_power
        popup_x = self.x
        if spinning:
            if self._last_attack_id != player.attack_id:
                self._spin_popup_index = 0
            self._spin_hit_remaining = player.SPIN_HIT_INTERVAL
            damage *= player.SPIN_DAMAGE_MULTIPLIER
            # Stagger consecutive numbers so they remain readable while rising.
            popup_x += (-24, 24, 0)[self._spin_popup_index % 3]
            self._spin_popup_index += 1
        if player.state == 'FLASH_STRIKE':
            damage *= player.FLASH_STRIKE_DAMAGE_MULTIPLIER
        self._last_attack_id = player.attack_id
        add_damage_popup(self.damage_popups, damage, popup_x, self.hurtbox.top + 10)

    def update(self, delta_time):
        update_damage_popups(self.damage_popups, delta_time)
        self._spin_hit_remaining = max(0.0, self._spin_hit_remaining - delta_time)
        if self._hit_time is not None:
            self._hit_time += delta_time
            if self._hit_time >= self.HIT_FRAME_TIME * self.HIT_FRAME_COUNT:
                self._hit_time = None

    def draw(self):
        frame = 0 if self._hit_time is None else 1 + int(self._hit_time / self.HIT_FRAME_TIME)
        self.sheet.clip_draw(frame * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
                             self.x, self.foot_y + self.FEET_TO_CENTER, self.DRAW_SIZE, self.DRAW_SIZE)
        draw_damage_popups(self.damage_font, self.damage_popups)
