from pico2d import *
# 공격은 9, 구르기는 5, 점프는 7, 걷기는 8, 달리기는 6프레임
# 공격 프레임은 3~6프레임의 크기는 200x200임.
open_canvas()
character = load_image('asset/roll_dice2.png')
face = load_image('asset/blue_faces.png')
    

def roll_dice():
    count = 0
    frame = 0
    while count < 21:
        clear_canvas()
        if count < 20 and count > 1:
            character.clip_draw(frame*100,0,100,100,400,300)
            frame += 1
            count += 1
            if frame % 5 == 0:
                frame = 1
        else:
            frame = 0
            character.clip_draw(frame*100, 0, 100, 100,
            400, 300)
            count += 1
        update_canvas()
        delay(0.03)
    face.clip_draw(0, 0, 100, 100, 400, 300, 83,83)
    update_canvas()
    delay(0.5)
while True:
    roll_dice()