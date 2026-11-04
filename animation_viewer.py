from pico2d import *
# 공격은 9, 구르기는 5, 점프는 7, 걷기는 8, 달리기는 6프레임
# 공격 프레임은 3~6프레임의 크기는 200x200임.
counts = 0
frame = 0
running = True
def load_images():
    global move_dice_roll, move_dice, attack_dice_roll, attack_dice, defense_dice_roll, defense_dice, critical_dice_roll, critical_dice, sword_dice_roll, sword_dice, runs
    move_dice_roll = load_image('asset/Move_Dice_Roll.png')
    move_dice = load_image('asset/Move_Dice.png')
    attack_dice_roll = load_image('asset/Attack_Dice_Roll.png')
    attack_dice = load_image('asset/Attack_Dice.png')
    defense_dice_roll = load_image('asset/Defense_Dice_Roll.png')
    defense_dice = load_image('asset/Defense_Dice.png')
    critical_dice_roll = load_image('asset/Critical_Dice_Roll.png')
    critical_dice = load_image('asset/Critical_Dice.png')
    sword_dice_roll = load_image('asset/Sword_Dice_Roll.png')
    sword_dice = load_image('asset/Sword_Dice.png')
    runs = load_image('asset/Run.png')


def Animaiton_viewer():
    global counts, frame
    while running:
        handle_events()
        if running == False:
            break
        clear_canvas()
        if counts == 20:
            show_faces()
            counts = 0
            frame = 0
            update_canvas()
            delay(0.5)
        else:
            Move_Dice_roll(counts, frame)
            Attack_Dice_roll(counts, frame)
            Defense_Dice_roll(counts, frame)
            Critical_Dice_roll(counts, frame)
            Sword_Dice_roll(counts, frame)
            update_canvas()
            frame = (frame + 1) % 6
            counts += 1
            delay(0.03)
        

def Run_Animation_viewer():
    pass

def Move_Dice_roll(counts, frame):
    if counts < 20 and counts > 1:
        move_dice_roll.clip_draw(frame*100, 0, 100, 100, 200, 500)
    else:
        move_dice_roll.clip_draw(frame*100, 0, 100, 100, 200, 500)

def Attack_Dice_roll(counts, frame):
    if counts < 20 and counts > 1:
        attack_dice_roll.clip_draw(frame*100, 0, 100, 100, 400, 500)
    else:
        attack_dice_roll.clip_draw(frame*100, 0, 100, 100, 400, 500)

def Defense_Dice_roll(counts, frame):
    if counts < 20 and counts > 1:
        defense_dice_roll.clip_draw(frame*100, 0, 100, 100, 600, 500)
    else:
        defense_dice_roll.clip_draw(frame*100, 0, 100, 100, 600, 500)
    
def Critical_Dice_roll(counts, frame):
    if counts < 20 and counts > 1:
        critical_dice_roll.clip_draw(frame*100, 0, 100, 100, 400, 400)
    else:
        critical_dice_roll.clip_draw(frame*100, 0, 100, 100, 400, 400)
    
def Sword_Dice_roll(counts, frame):
    if counts < 20 and counts > 1:
        sword_dice_roll.clip_draw(frame*100, 0, 100, 100, 200, 400)
    else:
        sword_dice_roll.clip_draw(frame*100, 0, 100, 100, 200, 400)
    
def show_faces():
    move_dice.clip_draw(0, 0, 100, 100, 200, 500, 83,83)
    attack_dice.clip_draw(0, 0, 100, 100, 400, 500, 73,73)
    defense_dice.clip_draw(0, 0, 100, 100, 600, 500, 83,83)
    critical_dice.clip_draw(0, 0, 100, 100, 400, 400, 83,83)
    sword_dice.clip_draw(0, 0, 100, 100, 200, 400, 83,83)

def handle_events():
    global running
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False

def run(counts, frame):
    if counts < 5:
        runs.clip_draw(frame*100, counts*100, 100, 100, 400, 300)
    else:
        runs.clip_composite_draw(frame*100, (counts-5)*100, 100, 100, math.radians(180), 'v', 400, 300)
            
open_canvas()
load_images()
Animaiton_viewer()
