from pico2d import *

running = True

Player_dir = 0 # 

def handle_events(player, dice_ui=None):
    global running
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif dice_ui is None or not dice_ui.handle_event(event):
            player.handle_events(event)