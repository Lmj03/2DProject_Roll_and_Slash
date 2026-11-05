from pico2d import *
from transitions import Machine
import math

class player:
    KEY_DIRECTIONS = {
        SDLK_UP: 0,
        SDLK_RIGHT: 2,
        SDLK_DOWN: 4,
        SDLK_LEFT: 6,
    }

    def __init__(self):
        self.x = 400
        self.y = 300
        self.frame = 0
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = 0 # 0 up, 1 up-right, 2 right, 3 down-right, 4 down, 5 down-left, 6 left, 7 up-left
        self.pressed_keys = []
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN'],
            transitions=[
                {'trigger': 'start_running', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop_running', 'source': 'RUN', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            after_state_change='_reset_animation',
        )

    def _reset_animation(self):
        self.frame = 0
        
    def handle_events(self, event):
        if (event.type not in (SDL_KEYDOWN, SDL_KEYUP) or
                event.key not in self.KEY_DIRECTIONS):
            return
        
        if event.type == SDL_KEYDOWN:
            if event.key not in self.pressed_keys:
                self.pressed_keys.append(event.key)
        elif event.key in self.pressed_keys:
            self.pressed_keys.remove(event.key)

        if self.pressed_keys:
            self.dir = self.KEY_DIRECTIONS[self.pressed_keys[-1]]
            if self.state == 'IDLE':
                self.start_running()
        elif self.state == 'RUN':
            self.stop_running()
            
    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 6
            delay(0.1)
        elif self.state == 'RUN':
            if self.dir == 0:
                self.y += 5
            elif self.dir == 2:
                self.x += 5
            elif self.dir == 4:
                self.y -= 5
            elif self.dir == 6:
                self.x -= 5
            self.frame = (self.frame + 1) % 10
            delay(0.02)
            
    def draw(self):
        if self.state == 'IDLE':
            self._draw_animation(self.Idle_Animation)
        elif self.state == 'RUN':
            self._draw_animation(self.Player_Run)

    def _draw_animation(self, animation):
        if self.dir < 5:
            animation.clip_draw(self.frame*100, self.dir*100, 100, 100, self.x, self.y)
        else:
            animation.clip_composite_draw(self.frame*100, (self.dir-5)*100, 100, 100, math.radians(180), 'v', self.x, self.y)
