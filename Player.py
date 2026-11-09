from math import sqrt

from pico2d import *
from transitions import Machine

class player:
    UP, RIGHT, DOWN, LEFT = range(4)
    KEY_INPUTS = {SDLK_UP, SDLK_RIGHT, SDLK_DOWN, SDLK_LEFT}
    ANIMATION_ROWS = {UP: 0, RIGHT: 2, DOWN: 4, LEFT: 2}
    MOVE_SPEED = 6
    DRAW_SCALE = 1.2
    FOOT_OFFSET_Y = 36  # Distance below the center of an unscaled sprite.

    def __init__(self):
        self.x = 400
        self.y = 300
        self.frame = 0
        self._attack_frames_played = 0
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
                {'trigger': 'start_attack', 'source': 'IDLE', 'dest': 'ATTACK'},
                {'trigger': 'start_attack', 'source': 'RUN', 'dest': 'ATTACK'},
                {'trigger': 'stop_attack', 'source': 'ATTACK', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            after_state_change='_reset_animation',
        )

    def _reset_animation(self):
        self.frame = 0
        self._attack_frames_played = 0
        
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
            
    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 6
            delay(0.1)
        elif self.state == 'RUN':
            step = self.MOVE_SPEED / sqrt(2) if self.move_x and self.move_y else self.MOVE_SPEED
            self.x += self.move_x * step
            self.y += self.move_y * step
            self.frame = (self.frame + 1) % 10
            delay(0.02)
        elif self.state == 'ATTACK':
            if self._attack_frames_played >= 10:
                self.stop_attack()
                self._sync_movement()
                self.attack_combo = (self.attack_combo + 1) % 3
            else:
                self.frame = self._attack_frames_played
                self._attack_frames_played += 1
                delay(0.05)
            
    def draw(self):
        self.shadow.draw(self.x, self.y - self.FOOT_OFFSET_Y, 54, 8)
        if self.state == 'IDLE':
            self._draw_frame(self.Idle_Animation, self.ANIMATION_ROWS[self.dir])
        elif self.state == 'RUN':
            self._draw_frame(self.Player_Run, self.ANIMATION_ROWS[self.dir])
        elif self.state == 'ATTACK':
            self._draw_attack()

    def _draw_attack(self):
        if self.dir == self.UP:
            self._draw_frame(self.Normal_Attack_Up, self.attack_combo)
            self._draw_frame(self.Attack_Trail_Up, self.attack_combo, cell_height=180)
        elif self.dir == self.DOWN:
            self._draw_frame(self.Normal_Attack_Down, self.attack_combo)
            self._draw_frame(self.Attack_Trail_Down, self.attack_combo, cell_height=180)
        else:
            self._draw_frame(self.Normal_Attack, self.attack_combo)
            self._draw_frame(self.Attack_Trail, self.attack_combo, cell_width=180)

    def _draw_frame(self, image, row, cell_width=100, cell_height=100):
        left = self.frame * cell_width
        bottom = row * cell_height
        draw_width = round(cell_width * self.DRAW_SCALE)
        draw_height = round(cell_height * self.DRAW_SCALE)
        draw_y = self.y + self.FOOT_OFFSET_Y * (self.DRAW_SCALE - 1)

        if self.dir == self.LEFT:
            image.clip_composite_draw(
                left, bottom, cell_width, cell_height, 0, 'h', self.x, draw_y, draw_width, draw_height)
        else:
            image.clip_draw(
                left, bottom, cell_width, cell_height, self.x, draw_y, draw_width, draw_height)
