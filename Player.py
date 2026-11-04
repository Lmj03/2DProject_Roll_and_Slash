from pico2d import *
import key_handle_events

class player:
    def __init__(self):
        self.x = 400
        self.y = 300
        self.frame = 0
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = 0 # 0 up, 1 up-right, 2 right, 3 down-right, 4 down, 5 down-left, 6 left, 7 up-left
        self.state = 0 # 0 idle , 1 run , 2 attack
        
    def handle_events(self, event):
        if (event.type not in (SDL_KEYDOWN, SDL_KEYUP) or
                event.key not in (SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN)):
            return
        
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_RIGHT:
                self.dir = 2
                self.state = 1
            elif event.key == SDLK_DOWN:
                self.dir = 4
                self.state = 1
            elif event.key == SDLK_LEFT:
                self.dir = 6
                self.state = 1
            elif event.key == SDLK_UP:
                self.dir = 0
                self.state = 1
        if event.type == SDL_KEYUP:
            if event.key in (SDLK_RIGHT, SDLK_DOWN, SDLK_LEFT, SDLK_UP):
                self.state = 0
                self.frame = 0
            
    def update(self):
        if self.state == 0:
            self.frame = (self.frame + 1) % 6
            delay(0.1)
        elif self.state == 1:
            if self.dir == 0:
                self.y += 5
            elif self.dir == 2:
                self.x += 5
            elif self.dir == 4:
                self.y -= 5
            elif self.dir == 6:
                self.x -= 5
            self.frame = (self.frame + 1) % 10
            delay(0.03)
            
    def draw(self):
        if self.state == 0:
            if self.dir < 5:
                self.Idle_Animation.clip_draw(self.frame*100, self.dir*100, 100, 100, self.x, self.y)
            else:
                self.Idle_Animation.clip_composite_draw(self.frame*100, (self.dir-5)*100, 100, 100, math.radians(180), 'v', self.x, self.y)
        elif self.state == 1:
            if self.dir < 5:
                self.Player_Run.clip_draw(self.frame*100, self.dir*100, 100, 100, self.x, self.y)
            else:
                self.Player_Run.clip_composite_draw(self.frame*100, (self.dir-5)*100, 100, 100, math.radians(180), 'v', self.x, self.y)
        
                
    
            