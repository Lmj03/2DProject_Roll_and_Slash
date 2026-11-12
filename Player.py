from math import ceil, sqrt

from pico2d import *
from transitions import Machine

# Down attack poses are wider than the matching idle and run sprites.
DOWN_ATTACK_WIDTH_SCALE = 0.86

class player:
    UP, RIGHT, DOWN, LEFT = range(4)
    KEY_INPUTS = {SDLK_UP, SDLK_RIGHT, SDLK_DOWN, SDLK_LEFT}
    ANIMATION_ROWS = {UP: 0, RIGHT: 2, DOWN: 4, LEFT: 2}
    MOVE_SPEED = 300.0  # Pixels per second, formerly 6 pixels every 0.02 seconds.
    MAX_MOVE_STEP = 6.0
    IDLE_FRAME_TIME = 0.1
    RUN_FRAME_TIME = 0.02
    ATTACK_FRAME_TIME = 0.05
    ANIMATION_EPSILON = 1e-9  # Tolerance for floating-point frame boundaries.
    DRAW_SCALE = 1.2
    FOOT_OFFSET_Y = 36  # Distance below the center of an unscaled sprite.
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
        self.x = 400
        self.y = 300
        self.frame = 0
        self._animation_time = 0.0
        self._attack_key_down = False
        self.attack_combo = 0
        self.shadow = load_image('asset/player_shadow.png')
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Attack_Trail = load_image('asset/attack_trail.png')
        self.Normal_Attack_Up = load_image('asset/attack_up.png')
        self.Normal_Attack_Down = load_image('asset/attack_down.png')
        self.Attack_Trail_Up = load_image('asset/attack_up_trail.png')
        self.Attack_Trail_Down = load_image('asset/attack_down_trail.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = self.UP
        self.pressed_keys = set()
        self.move_x = 0
        self.move_y = 0
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN','ATTACK'],
            transitions=[
                {'trigger': 'start_running', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop_running', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'start_attack', 'source': ['IDLE', 'RUN'], 'dest': 'ATTACK'},
                {'trigger': 'stop_attack', 'source': 'ATTACK', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            after_state_change='_reset_animation',
        )

    def _reset_animation(self):
        self.frame = 0
        self._animation_time = 0.0
        
    def handle_events(self, event):
        if event.type not in (SDL_KEYDOWN, SDL_KEYUP):
            return

        if event.key == SDLK_a:
            if event.type == SDL_KEYUP:
                self._attack_key_down = False
            elif not self._attack_key_down:
                self._attack_key_down = True
                if self.state in ('IDLE', 'RUN'):
                    self.start_attack()
            return

        if event.key not in self.KEY_INPUTS:
            return
        
        if event.type == SDL_KEYDOWN:
            self.pressed_keys.add(event.key)
        else:
            self.pressed_keys.discard(event.key)

        if self.state == 'ATTACK':
            return
        self._sync_movement()

    def _sync_movement(self):
        self.move_x = (SDLK_RIGHT in self.pressed_keys) - (SDLK_LEFT in self.pressed_keys)
        self.move_y = (SDLK_UP in self.pressed_keys) - (SDLK_DOWN in self.pressed_keys)
        if self.move_x or self.move_y:
            if self.move_x:
                self.dir = self.RIGHT if self.move_x > 0 else self.LEFT
            else:
                self.dir = self.UP if self.move_y > 0 else self.DOWN
            if self.state == 'IDLE':
                self.start_running()
        elif self.state == 'RUN':
            self.stop_running()
            
    def update(self, delta_time, can_move=None):
        if delta_time <= 0:
            return

        self._animation_time += delta_time
        if self.state == 'ATTACK':
            duration = self.ATTACK_FRAME_TIME * 10
            if self._animation_time < duration - self.ANIMATION_EPSILON:
                self.frame = int((self._animation_time + self.ANIMATION_EPSILON)
                                 / self.ATTACK_FRAME_TIME)
                return

            # Use the rest of this frame after the attack for idle or resumed movement.
            delta_time = max(0.0, self._animation_time - duration)
            self.stop_attack()
            self._sync_movement()
            self.attack_combo = (self.attack_combo + 1) % 3
            self._animation_time = delta_time

        if self.state == 'RUN':
            self._move(delta_time, can_move)
            frame_time, frame_count = self.RUN_FRAME_TIME, 10
        else:
            frame_time, frame_count = self.IDLE_FRAME_TIME, 6

        self._animation_time %= frame_time * frame_count
        self.frame = int((self._animation_time + self.ANIMATION_EPSILON) / frame_time) % frame_count

    def _move(self, delta_time, can_move):
        distance = self.MOVE_SPEED * delta_time
        # Test the whole path in small steps so a slow frame cannot skip a wall.
        steps = max(1, ceil(distance / self.MAX_MOVE_STEP))
        step = distance / steps
        if self.move_x and self.move_y:
            step /= sqrt(2)

        for _ in range(steps):
            old_x, old_y = self.x, self.y
            next_x = self.x + self.move_x * step
            next_y = self.y + self.move_y * step
            if can_move is None or can_move(next_x, self.y - self.FOOT_OFFSET_Y):
                self.x = next_x
            if can_move is None or can_move(self.x, next_y - self.FOOT_OFFSET_Y):
                self.y = next_y
            if self.x == old_x and self.y == old_y:
                break
            
    def draw(self):
        self._draw_shadow()
        if self.state == 'IDLE':
            self._draw_frame(self.Idle_Animation, self.ANIMATION_ROWS[self.dir])
        elif self.state == 'RUN':
            self._draw_frame(self.Player_Run, self.ANIMATION_ROWS[self.dir])
        elif self.state == 'ATTACK':
            self._draw_attack()

    def _draw_shadow(self):
        x = self.x
        y = self.y - self.FOOT_OFFSET_Y
        if self.state == 'ATTACK':
            direction = self.RIGHT if self.dir == self.LEFT else self.dir
            offset_x, depth = self.ATTACK_SHADOW_CONTACTS[direction][self.attack_combo][self.frame]
            if self.dir == self.LEFT:
                offset_x = -offset_x
            elif direction == self.DOWN:
                offset_x *= DOWN_ATTACK_WIDTH_SCALE
            x += offset_x * self.DRAW_SCALE
            y += (self.FOOT_OFFSET_Y - depth) * self.DRAW_SCALE
        self.shadow.draw(x, y, 54, 8)

    def _draw_attack(self):
        if self.dir == self.UP:
            self._draw_frame(self.Normal_Attack_Up, self.attack_combo)
            self._draw_frame(self.Attack_Trail_Up, self.attack_combo, cell_height=180)
        elif self.dir == self.DOWN:
            self._draw_frame(self.Normal_Attack_Down, self.attack_combo,
                             width_scale=DOWN_ATTACK_WIDTH_SCALE)
            self._draw_frame(self.Attack_Trail_Down, self.attack_combo, cell_height=180,
                             width_scale=DOWN_ATTACK_WIDTH_SCALE)
        else:
            self._draw_frame(self.Normal_Attack, self.attack_combo)
            self._draw_frame(self.Attack_Trail, self.attack_combo, cell_width=180)

    def _draw_frame(self, image, row, cell_width=100, cell_height=100, *, width_scale=1):
        left = self.frame * cell_width
        bottom = row * cell_height
        draw_width = round(cell_width * self.DRAW_SCALE * width_scale)
        draw_height = round(cell_height * self.DRAW_SCALE)
        draw_y = self.y + self.FOOT_OFFSET_Y * (self.DRAW_SCALE - 1)

        if self.dir == self.LEFT:
            image.clip_composite_draw(
                left, bottom, cell_width, cell_height, 0, 'h', self.x, draw_y, draw_width, draw_height)
        else:
            image.clip_draw(
                left, bottom, cell_width, cell_height, self.x, draw_y, draw_width, draw_height)
