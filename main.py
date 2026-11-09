from pico2d import *
import Player
import key_handle_events

def main():
    canvas_width, canvas_height = 1500, 700
    open_canvas(canvas_width, canvas_height)
    lobby = load_image('asset/lobby.png')
    player = Player.player()
    player.x, player.y = canvas_width // 2, 150
    
    while key_handle_events.running:
        key_handle_events.handle_events(player)
        if not key_handle_events.running:
            break

        clear_canvas()
        lobby.draw(canvas_width // 2, canvas_height // 2)
        player.update()
        player.draw()
        update_canvas()

    close_canvas()

if __name__ == "__main__":
    main()
