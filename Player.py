from math import sqrt

from pico2d import *
from transitions import Machine

class player:
    UP, RIGHT, DOWN, LEFT = range(4)
    KEY_INPUTS = {
        SDLK_UP: UP,
        SDLK_RIGHT: RIGHT,
        SDLK_DOWN: DOWN,
        SDLK_LEFT: LEFT,
    }
    ANIMATION_ROWS = {UP: 0, RIGHT: 2, DOWN: 4, LEFT: 2}
    MOVE_SPEED = 6

    def __init__(self):
        self.x = 400
        self.y = 300
        self.frame = 0
        self._attack_frames_played = 0
        self._attack_key_down = False
        self.attack_combo = 0
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Attack_Trail = load_image('asset/attack_trail.png')
        self.Normal_Attack_Up = load_image('asset/attack_up.png')
        self.Normal_Attack_Down = load_image('asset/attack_down.png')
        self.Attack_Trail_Up = load_image('asset/attack_up_trail.png')
        self.Attack_Trail_Down = load_image('asset/attack_down_trail.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = self.UP
        self.pressed_keys = []
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
            if event.key not in self.pressed_keys:
                self.pressed_keys.append(event.key)
        elif event.key in self.pressed_keys:
            self.pressed_keys.remove(event.key)

        if self.state == 'ATTACK':
            return
        self._sync_movement()

    def _sync_movement(self):
        self.move_x = (SDLK_RIGHT in self.pressed_keys) - (SDLK_LEFT in self.pressed_keys)
        self.move_y = (SDLK_UP in self.pressed_keys) - (SDLK_DOWN in self.pressed_keys)
        if self.move_x or self.move_y:
            self.dir = self.KEY_INPUTS[self.pressed_keys[-1]]
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
        if self.state == 'IDLE':
            self._draw_animation(self.Idle_Animation)
        elif self.state == 'RUN':
            self._draw_animation(self.Player_Run)
        elif self.state == 'ATTACK':
            self._draw_animation(self.Normal_Attack)

    def _draw_animation(self, animation):
        if self.state == 'ATTACK':
            if self.dir == self.LEFT:
                self.Normal_Attack.clip_composite_draw(
                    self.frame*100, self.attack_combo*100, 100, 100, 0, 'h', self.x, self.y)
                self.Attack_Trail.clip_composite_draw(
                    self.frame*180, self.attack_combo*100, 180, 100, 0, 'h', self.x, self.y)
            elif self.dir == self.RIGHT:
                self.Normal_Attack.clip_draw(
                    self.frame*100, self.attack_combo*100, 100, 100, self.x, self.y)
                self.Attack_Trail.clip_draw(
                    self.frame*180, self.attack_combo*100, 180, 100, self.x, self.y)
            elif self.dir == self.UP:
                self.Normal_Attack_Up.clip_draw(
                    self.frame*100, self.attack_combo*100, 100, 100, self.x, self.y)
                self.Attack_Trail_Up.clip_draw(
                    self.frame*100, self.attack_combo*180, 100, 180, self.x, self.y)
            elif self.dir == self.DOWN:
                self.Normal_Attack_Down.clip_draw(
                    self.frame*100, self.attack_combo*100, 100, 100, self.x, self.y)
                self.Attack_Trail_Down.clip_draw(
                    self.frame*100, self.attack_combo*180, 100, 180, self.x, self.y)
        else:
            bottom = self.ANIMATION_ROWS[self.dir] * 100
            if self.dir == self.LEFT:
                animation.clip_composite_draw(self.frame*100, bottom, 100, 100, 0, 'h', self.x, self.y)
            else:
                animation.clip_draw(self.frame*100, bottom, 100, 100, self.x, self.y)
