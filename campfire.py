from pico2d import load_image

from collision import touches_campfire

from lobby_map import CAMPFIRE_POSITION


class Campfire:
    CELL_SIZE = 100
    FRAME_COUNT = 4
    FRAME_TIME = 0.12
    DRAW_SIZE = 120
    FOOT_TO_CENTER = 30
    DAMAGE = 5  # Fixed hazard damage for checking HP loss, independent of defense.
    DAMAGE_INTERVAL = 0.5
    SIMULATION_STEP = 1.0 / 60.0

    def __init__(self):
        self.x, self.foot_y = CAMPFIRE_POSITION
        self.sheet = load_image('asset/campfire_sheet.png')
        self.elapsed = 0.0
        self.damage_cooldown = 0.0

    def update(self, delta_time):
        if delta_time > 0:
            self.elapsed = (self.elapsed + delta_time) % (self.FRAME_COUNT * self.FRAME_TIME)

    def apply_damage(self, delta_time, player):
        if delta_time <= 0:
            return
        touching = touches_campfire(
            player.x, player.y - player.FOOT_OFFSET_Y, (self.x, self.foot_y),
        )
        if not touching or player.hp <= 0:
            self.damage_cooldown = max(0.0, self.damage_cooldown - delta_time)
            return

        # First contact hits immediately; subsequent hits follow a timer, not render frames.
        remaining = delta_time
        while self.damage_cooldown <= remaining + 1e-9:
            remaining = max(0.0, remaining - self.damage_cooldown)
            player.take_damage(self.DAMAGE)
            self.damage_cooldown = self.DAMAGE_INTERVAL
            if player.hp <= 0:
                break
        self.damage_cooldown = max(0.0, self.damage_cooldown - remaining)

    def draw(self, camera=None):
        frame = int((self.elapsed + 1e-9) / self.FRAME_TIME) % self.FRAME_COUNT
        x, y = self.x, self.foot_y + self.FOOT_TO_CENTER
        if camera is not None:
            x, y = camera.project(x, y)
        self.sheet.clip_draw(
            frame * self.CELL_SIZE, 0, self.CELL_SIZE, self.CELL_SIZE,
            x, y, self.DRAW_SIZE, self.DRAW_SIZE,
        )
