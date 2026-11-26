from pico2d import *

running = True

Player_dir = 0 # 

def handle_events(player, dice_ui=None, well=None, *, doors=()):
    global running
    events = get_events()
    door_requested = False
    for event in events:
        if event.type == SDL_QUIT:
            running = False
            break
        elif well is not None and well.handle_event(event):
            pass
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
            break
        elif door_requested or any(door.handle_event(event) for door in doors):
            door_requested = True
        elif dice_ui is None or not dice_ui.handle_event(event):
            player.handle_events(event)