from math import hypot

from pico2d import draw_circle, load_image
from sdl2 import SDL_SetTextureColorMod

from armored_wraith import ArmoredWraith
from enemy import Enemy
from player_movement import DOWN, LEFT, RIGHT, UP


class TalismanStatue(Enemy):
    MAX_HP = ArmoredWraith.MAX_HP * 2
    BODY_HALF_WIDTH = 51
    BODY_HEIGHT = 113
    FOOTPRINT_HALF_WIDTH = 27
    FOOTPRINT_HALF_HEIGHT = 14
    HEALTH_BAR_WIDTH = 73
    HEALTH_BAR_OFFSET_Y = 130
    CELL_SIZE = 150
    FEET_TO_CENTER = 57
    PATROL_SPEED = 55
    WALK_FRAME_TIME = 0.13
    ROWS = {UP: 0, DOWN: 1, LEFT: 2, RIGHT: 3}

    MIN_THROW_RANGE = 130
    MAX_THROW_RANGE = 410
    WINDUP_TIME = 0.68
    THROW_POSE_END = WINDUP_TIME + 0.28
    FLIGHT_TIME = 0.72
    IMPACT_TIME = WINDUP_TIME + FLIGHT_TIME
    AFTERMATH_TIME = 0.24
    THROW_COOLDOWN = 1.25
    LANDING_RADIUS = 36
    ROCK_DAMAGE = 20

    def __init__(self, position, *, patrol, patrol_area):
        super().__init__(position, patrol=patrol, patrol_area=patrol_area)
        self._aim = None
        self._throw_origin = position
        self.walk_sheet = load_image('asset/m2.png')
        self.throw_sheet = load_image('asset/monsters/m2_throw.png')
        self.rock_image = load_image('asset/monsters/m2_boulder.png')

    def act(self, player, delta_time, can_move):
        if delta_time <= 1e-9:
            return
        if self.hp <= 0 or self.stun_remaining > 0:
            self._attack_time = None
            self.walk_frame = 0
            return

        player_foot_y = player.y - player.FOOT_OFFSET_Y
        if player.hp <= 0:
            self._attack_time = None
        elif self._attack_time is not None:
            self._advance_throw(player, player_foot_y, delta_time)
            if self._attack_time is not None and self._attack_time < self.THROW_POSE_END:
                return
        elif self._cooldown <= 0 and self._in_patrol_area(player.x, player_foot_y):
            dx, dy = player.x - self.x, player_foot_y - self.foot_y
            if self.MIN_THROW_RANGE <= hypot(dx, dy) <= self.MAX_THROW_RANGE:
                self.facing = self._facing_toward(dx, dy)
                self._aim = player.x, player_foot_y
                self._throw_origin = self.x, self.foot_y
                self.walk_frame = 0
                self._attack_time = 0.0
                return

        self._patrol_step(delta_time, self._movement_check(player.x, player_foot_y, can_move))

    def _advance_throw(self, player, player_foot_y, delta_time):
        before = self._attack_time
        self._attack_time += delta_time
        if before < self.IMPACT_TIME <= self._attack_time:
            dx, dy = player.x - self._aim[0], player_foot_y - self._aim[1]
            if hypot(dx, dy) <= self.LANDING_RADIUS:
                # The boulder deals ground-impact damage, which cannot be parried.
                player.take_damage(self.ROCK_DAMAGE)
        if self._attack_time is not None and self._attack_time >= self.IMPACT_TIME + self.AFTERMATH_TIME:
            self._attack_time = None
            self._cooldown = self.THROW_COOLDOWN

    def draw_landing(self, camera):
        if self._attack_time is None:
            return
        x, y = camera.project(*self._aim)
        if self._attack_time < self.IMPACT_TIME:
            draw_circle(x, y, self.LANDING_RADIUS, 148, 56, 25)
            draw_circle(x, y, self.LANDING_RADIUS - 1, 246, 154, 71)
        else:
            progress = (self._attack_time - self.IMPACT_TIME) / self.AFTERMATH_TIME
            radius = round(10 + (self.LANDING_RADIUS - 10) * progress)
            draw_circle(x, y, radius, 199, 134, 79)

    def _pose(self):
        elapsed = self._attack_time
        if elapsed is None or elapsed >= self.THROW_POSE_END:
            return self.walk_sheet, self.walk_frame
        if elapsed < .24:
            return self.throw_sheet, 0
        return self.throw_sheet, 1 if elapsed < self.WINDUP_TIME else 2

    def _draw_boulder(self, camera):
        elapsed = self._attack_time
        if elapsed is None or elapsed < .24:
            return
        if elapsed < self.WINDUP_TIME:
            x, y = self._screen_position(camera, self.x, self.foot_y + 106)
        elif elapsed < self.IMPACT_TIME:
            t = (elapsed - self.WINDUP_TIME) / self.FLIGHT_TIME
            start_x, start_y = self._throw_origin
            ground_x = start_x + (self._aim[0] - start_x) * t
            ground_y = start_y + (self._aim[1] - start_y) * t
            height = (1 - t) * 106 + 250 * t * (1 - t)
            x, y = self._screen_position(camera, ground_x, ground_y + height + t * 17)
        else:
            t = (elapsed - self.IMPACT_TIME) / self.AFTERMATH_TIME
            for dx, dy in ((-29, 10), (28, 16), (4, 26), (-14, -10)):
                x, y = self._screen_position(camera, self._aim[0] + dx * t, self._aim[1] + dy * t)
                self.rock_image.draw(x, y + 4, 8, 7)
            return
        self.rock_image.draw(x, y, 42, 40)

    def draw(self, camera=None):
        if self.hp > 0:
            x, foot_y = self._screen_position(camera, self.x, self.foot_y)
            self.shadow.draw(x, foot_y, 90, 13)
            sheet, frame = self._pose()
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 140, 185, 255)
            cell = self.CELL_SIZE
            sheet.clip_draw(frame * cell, self.ROWS[self.facing] * cell, cell, cell,
                            x, foot_y + self.FEET_TO_CENTER)
            if self.stun_remaining > 0:
                SDL_SetTextureColorMod(sheet.texture, 255, 255, 255)
            self._draw_boulder(camera)
            self._draw_health_bar(x, foot_y)
        self._draw_damage_popups(camera)


class LandingWarning:
    def __init__(self, statue):
        self.statue = statue

    def draw(self, camera):
        self.statue.draw_landing(camera)
