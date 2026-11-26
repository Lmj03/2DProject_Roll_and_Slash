import key_handle_events
from dice_ui import DiceRollUI
from lobby_map import CANVAS_HEIGHT, CANVAS_WIDTH, PLAYER_START
from scenes import create_lobby_scene, create_outer_fortress_scene


class SceneManager:
    def __init__(self, player):
        self.player = player
        self.player.x, self.player.y = PLAYER_START
        self.dice_ui = DiceRollUI(player, right=CANVAS_WIDTH - 32, top=CANVAS_HEIGHT - 32)
        self._scenes = {
            'lobby': create_lobby_scene(player, self.dice_ui),
            'outer_fortress': create_outer_fortress_scene(player, self.dice_ui),
        }
        self.current = self._scenes['lobby']

    def advance(self, delta_time):
        scene = self.current
        menu_was_open = scene.well is not None and scene.well.menu.is_open
        key_handle_events.handle_events(self.player, self.dice_ui, scene.well, door=scene.door)
        if not key_handle_events.running:
            return False

        if scene.door.take_request():
            self.current = self._scenes[scene.destination]
            self.current.enter(self.player)
        else:
            menu_is_open = scene.well is not None and scene.well.menu.is_open
            simulation_delta = 0.0 if menu_was_open or menu_is_open else delta_time
            scene.advance(self.player, self.dice_ui, simulation_delta)
        return True

    def draw(self):
        self.current.world.draw(self.current.camera, shake=self.player.hit_shake.offset)
