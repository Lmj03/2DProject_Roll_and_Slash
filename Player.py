from pico2d import *
import key_handle_events

class Player:
    def __init__(self):
        self.x = 400
        self.y = 300
        self.image = load_image('asset/player.png')
        self.dir = 0
        self.speed = 5