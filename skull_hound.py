from math import ceil, hypot

from pico2d import load_image

from bounding_box import BoundingBox
from enemy import Enemy
from player_movement import DOWN, LEFT, RIGHT, UP


class SkullHound(Enemy):
    MAX_HP = 140
    BODY_HALF_WIDTH = 32
    BODY_HEIGHT = 66
    FOOTPRINT_HALF_WIDTH = 25
    FOOTPRINT_HALF_HEIGHT = 10
    HEALTH_BAR_OFFSET_Y = 82
    PATROL_SPEED = 95

    CELL_SIZE = 100
    FEET_TO_CENTER = 34
    ROWS = {UP: 0, DOWN: 1, LEFT: 2, RIGHT: 3}
    DETECTION_RANGE = 320
    POUNCE_RANGE = 295
    WINDUP_TIME = 0.46
    FLIGHT_TIME = 0.34
    LAND_TIME = WINDUP_TIME + FLIGHT_TIME
    RECOVERY_TIME = 0.24
    COOLDOWN = 0.9
    RAW_DAMAGE = 18
    JUMP_HEIGHT = 29

    def __init__(self, position, *, patrol=(), patrol_area=None):
        super().__init__(position, patrol=patrol, patrol_area=patrol_area)
        self.walk_sheet = load_image('asset/monsters/m3_walk.png')
        self.attack_sheet = load_image('asset/monsters/m3_pounce.png')
        self.walk_flash_sheet = load_image('asset/hit_flash/m3_walk.png')
        self.attack_flash_sheet = load_image('asset/hit_flash/m3_pounce.png')
        self._pounce_delta = (0.0, 0.0)

    def act(self, player, delta_time, can_move):
        if delta_time <= 1e-9 or self.hp <= 0 or self.stun_remaining > 0:
            return

        player_foot_y = player.y - player.FOOT_OFFSET_Y
        if player.hp <= 0:
            self._attack_time = None
        elif self._attack_time is not None:
            self._advance_pounce(player, delta_time, can_move)
            return
        elif self._cooldown <= 0 and self._in_patrol_area(player.x, player_foot_y):
            dx, dy = player.x - self.x, player_foot_y - self.foot_y
            distance = hypot(dx, dy)
            if 0 < distance <= self.DETECTION_RANGE:
                factor = min(1.0, self.POUNCE_RANGE / distance)
                self._pounce_delta = dx * factor, dy * factor
                self.facing = self._facing_toward(dx, dy)
                self.walk_frame = 0
                self._attack_time = 0.0
                return

        self._patrol_step(delta_time, self._movement_check(player.x, player_foot_y, can_move))

    def _advance_pounce(self, player, delta_time, can_move):
        before = self._attack_time
        self._attack_time += delta_time
        airborne_time = min(self._attack_time, self.LAND_TIME) - max(before, self.WINDUP_TIME)
        if airborne_time > 0:
            self._move_pounce(player, airborne_time, can_move)
        if self._attack_time is not None and self._attack_time >= self.LAND_TIME + self.RECOVERY_TIME:
            self._attack_time = None
            self._cooldown = self.COOLDOWN

    def _move_pounce(self, player, airborne_time, can_move):
        travel_x, travel_y = self._pounce_delta
        ratio = airborne_time / self.FLIGHT_TIME
        steps = max(1, ceil(hypot(travel_x, travel_y) * ratio / 5))
        step_x, step_y = travel_x * ratio / steps, travel_y * ratio / steps
        body = player.renderer.body_box(player)
        for _ in range(steps):
            x, y = self.x + step_x, self.foot_y + step_y
            if not self._in_patrol_area(x, y) or not can_move(x, y):
                self._attack_time = self.LAND_TIME
                return

            self.x, self.foot_y = x, y
            if body is not None and self._pounce_box().overlaps(body):
                # Land on contact. A successful parry cancels recovery and stuns in place.
                self._attack_time = self.LAND_TIME
                player.take_damage(self.RAW_DAMAGE, attacker=self, apply_defense=True)
                return

    def _pounce_box(self):
        half_width = 24 if self.facing in (UP, DOWN) else 35
        return BoundingBox(self.x - half_width, self.foot_y,
                           self.x + half_width, self.foot_y + 54)

    def attack_box(self):
        if self._attack_time is not None and self.WINDUP_TIME <= self._attack_time < self.LAND_TIME:
            return self._pounce_box()
        return None

    def _attack_pose(self):
        if self.stun_remaining > 0 and self.hp > 0:
            return 5, 0.0
        elapsed = self._attack_time
        if elapsed is None:
            return None, 0.0
        if elapsed < self.WINDUP_TIME:
            return (0 if elapsed < 0.16 else 1), 0.0
        if elapsed >= self.LAND_TIME:
            return 4, 0.0
        progress = (elapsed - self.WINDUP_TIME) / self.FLIGHT_TIME
        height = 4 * self.JUMP_HEIGHT * progress * (1 - progress)
        return (2 if progress < 0.32 else 3), height

    def draw(self, camera=None):
        if self.hp > 0 or self.hit_flash_remaining > 0:
            x, foot_y = self._screen_position(camera, self.x, self.foot_y)
            self.shadow.draw(x, foot_y, 70, 10)
            pose, height = self._attack_pose()
            if pose is None:
                sheet, flash, frame = self.walk_sheet, self.walk_flash_sheet, self.walk_frame
            else:
                sheet, flash, frame = self.attack_sheet, self.attack_flash_sheet, pose
            cell = self.CELL_SIZE
            self._draw_body(sheet, flash, frame, self.ROWS[self.facing], cell,
                            x, foot_y + self.FEET_TO_CENTER + height, cell)
            if self.hp > 0:
                self._draw_health_bar(x, foot_y + height)
        self._draw_damage_popups(camera)
