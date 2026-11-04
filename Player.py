from pico2d import *
import key_handle_events

class Player:
    def __init__(self):
        self.x = 400
        self.y = 300
        self.Normal_Attack = load_image('asset/attack_sheet.png')
        self.Idle_Animation = load_image('asset/Player_Idle.png')
        self.Player_Run = load_image('asset/Run.png')
        self.dir = 0 # 0 , 1 , 2 , 3 오른쪽 하 왼쪽 위  순서
        
    def handle_events(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_RIGHT:
                self.dir = 0
            elif event.key == SDLK_DOWN:
                self.dir = 1
            elif event.key == SDLK_LEFT:
                self.dir = 2
            elif event.key == SDLK_UP:
                self.dir = 3
                
    
            