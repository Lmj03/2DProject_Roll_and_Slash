from pico2d import *
from transitions import Machine

class player:
    KEY_INPUTS = {
        SDLK_UP: 0,
        SDLK_RIGHT: 2,
        SDLK_DOWN: 4,
        SDLK_LEFT: 6
    }

    def __init__(self):
        self.x = 400
        self.y = 300
        self.frame = 0
        self._attack_frames_played = 0
        self._attack_key_down = False
        self.attack_combo = 0
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = 0 # 0 up, 1 up-right, 2 right, 3 down-right, 4 down, 5 down-left, 6 left, 7 up-left
        self.pressed_keys = []
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

        # Remember movement input without changing the attack's direction.
        if self.state == 'ATTACK':
            return
        self._sync_movement()

    def _sync_movement(self):
        if self.pressed_keys:
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
            if self.dir == 0:
                self.y += 6
            elif self.dir == 2:
                self.x += 6
            elif self.dir == 4:
                self.y -= 6
            elif self.dir == 6:
                self.x -= 6
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
                if self.dir in (5, 6, 7):
                    self.Normal_Attack.clip_composite_draw(
                        self.frame*100, self.attack_combo*100, 100, 100, 0, 'h', self.x, self.y)
                else:
                    self.Normal_Attack.clip_draw(
                        self.frame*100, self.attack_combo*100, 100, 100, self.x, self.y)
        
        elif self.dir < 5:
            animation.clip_draw(self.frame*100, self.dir*100, 100, 100, self.x, self.y)
        elif self.dir >= 5 and self.dir < 8:
            animation.clip_composite_draw(self.frame*100, (8-self.dir)*100, 
                                          100, 100, 0, 'h', self.x, self.y)
