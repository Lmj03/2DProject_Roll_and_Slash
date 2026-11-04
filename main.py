from pico2d import *
import Player
import key_handle_events

def main():
    open_canvas()
    player = Player.player()
    
    while key_handle_events.running:
        key_handle_events.handle_events(player)
        if not key_handle_events.running:
            break

        clear_canvas()
        player.update()
        player.draw()
        update_canvas()

    close_canvas()

if __name__ == "__main__":
    main()