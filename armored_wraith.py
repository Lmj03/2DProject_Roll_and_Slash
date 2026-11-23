from math import hypot

from pico2d import load_image
from sdl2 import SDL_SetTextureColorMod

from bounding_box import BoundingBox
from enemy import Enemy
from player_movement import DOWN, LEFT, RIGHT, UP, move_position


class ArmoredWraith(Enemy):
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
    PATROL_SPEED = 70
    WAYPOINT_TOLERANCE = 8

    ROWS = {UP: 0, DOWN: 1, LEFT: 2, RIGHT: 3}
    # Fourth-frame alpha bounds in each trail cell, in Pico2d's bottom-left coordinates.
    TRAIL_BOUNDS = {
        UP: (6, 114, 94, 164),
        DOWN: (6, 14, 94, 72),
        LEFT: (8, 12, 66, 84),
        RIGHT: (116, 12, 172, 84),
    }

    def __init__(self, position, *, patrol=(), patrol_area=None):
        super().__init__(position)
        self._patrol = tuple(patrol)
        self._patrol_area = patrol_area
        self._patrol_index = 0
        self.facing = DOWN
        self.walk_frame = 0
        self._walk_time = 0.0
        self._attack_hit = False

        self.walk_sheet = load_image('asset/m1.png')
        self.attack_sheet = load_image('asset/m1_attack.png')
        self.vertical_trail = load_image('asset/m1_attack_udtrail.png')
        self.horizontal_trail = load_image('asset/m1_attack_lrtrail.png')

    @property
    def _sprite_y(self):
        return self.foot_y + self.FEET_TO_CENTER

    def act(self, player, delta_time, can_move):
        if delta_time <= 1e-9:
            return
        if self.hp <= 0 or self.stun_remaining > 0:
            self._attack_time = None
            return

        body = player.renderer.body_box(player) if player.hp > 0 else None
        if body is None:
            self._attack_time = None
        elif self._attack_time is not None:
            self._advance_attack(player, body, delta_time)
            return

        player_foot_y = player.y - player.FOOT_OFFSET_Y
        dx, dy = player.x - self.x, player_foot_y - self.foot_y
        distance = hypot(dx, dy)
        def can_step(x, foot_y):
            clears_player = abs(x - player.x) > 24 or abs(foot_y - player_foot_y) > 17
            return clears_player and self._in_patrol_area(x, foot_y) and can_move(x, foot_y)

        if body is None or distance > self.AGGRO_RADIUS or not self._in_patrol_area(player.x, player_foot_y):
            self._patrol_step(delta_time, can_step)
            return

        self.facing = self._facing_toward(dx, dy)
        # Use a small inset when deciding to swing, so the target is in reach before the wind-up.
        if self._swing_bounds().expanded(-8).overlaps(body):
            self.walk_frame = 0
            if self._cooldown <= 0:
                self._attack_time = 0.0
                self._attack_hit = False
            return

        self._walk_toward(dx, dy, distance, self.MOVE_SPEED, delta_time, can_step)

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
        self.walk_frame = int((self._walk_time + 1e-9) / self.WALK_FRAME_TIME) % self.FRAME_COUNT
        return True

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

    def draw(self, camera=None):
        if self.hp > 0:
            x, y, foot_y = self.x, self._sprite_y, self.foot_y
            if camera is not None:
                x, y = camera.project(x, y)
                _, foot_y = camera.project(self.x, foot_y)
            self.shadow.draw(x, foot_y, 49, 8)
            attacking = self._attack_time is not None
            sheet = self.attack_sheet if attacking else self.walk_sheet
            frame = self._attack_frame() if attacking else self.walk_frame
            cell = self.CELL_SIZE
            draw_size = round(cell * self.DRAW_SCALE)
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 140, 185, 255)
            sheet.clip_draw(frame * cell, self.ROWS[self.facing] * cell, cell, cell,
                            x, y, draw_size, draw_size)
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 255, 255, 255)
            if attacking and frame in (self.HIT_FRAME, self.HIT_FRAME + 1):
                trail, row, width, height = self._trail_cell()
                trail.clip_draw(frame * width, row * height, width, height, x, y,
                                round(width * self.DRAW_SCALE), round(height * self.DRAW_SCALE))
            self._draw_health_bar(x, foot_y)
        self._draw_damage_popups(camera)
