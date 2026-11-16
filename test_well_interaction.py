import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pico2d import (
    SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT,
    SDLK_1, SDLK_a, SDLK_e, SDLK_ESCAPE, SDLK_f, SDLK_LEFT, SDLK_r, SDLK_RETURN,
    SDLK_RIGHT,
)

import Player
import buff_dice_menu
import collision
import dice_ui
import key_handle_events
import main
import well_interaction


def key(code):
    return SimpleNamespace(type=SDL_KEYDOWN, key=code)


class WellInteractionTests(unittest.TestCase):
    def setUp(self):
        # UI construction is exercised without requiring a window or GPU.
        self.patches = [patch.object(Player, 'load_image', return_value=None)]
        for module in (dice_ui, buff_dice_menu, well_interaction):
            self.patches.extend((patch.object(module, 'load_image', return_value=None),
                                 patch.object(module, 'load_font', return_value=None)))
        self.patches.extend((patch.object(buff_dice_menu, 'get_canvas_height', return_value=700),
                             patch.object(key_handle_events, 'running', True)))
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)
        self.player = Player.player()
        self.player.x, self.player.y = 1095, 226
        self.dice = dice_ui.DiceRollUI(self.player, 1468, 668)
        self.well = well_interaction.WellInteraction(self.player)

    def dispatch(self, *events):
        with patch.object(key_handle_events, 'get_events', return_value=events):
            key_handle_events.handle_events(self.player, self.dice, self.well)

    def open_menu(self):
        self.dispatch(key(SDLK_e))
        self.assertTrue(self.well.menu.is_open)

    def test_range_uses_walkable_ground_around_the_well(self):
        self.assertTrue(collision.can_interact_with_well(1095, 190))
        self.assertTrue(collision.can_interact_with_well(1270, 316))
        for point in ((750, 114), (1095, 316), (1300, 316), (-10, -10)):
            with self.subTest(point=point):
                self.assertFalse(collision.can_interact_with_well(*point))

    def test_far_player_cannot_open_menu(self):
        self.player.x = 750
        self.dispatch(key(SDLK_e))
        self.assertFalse(self.well.menu.is_open)

    def test_attack_must_finish_before_interaction(self):
        self.player.start_attack()
        self.dispatch(key(SDLK_e))
        self.assertFalse(self.well.menu.is_open)

    def test_opening_clears_held_movement_and_attack_input(self):
        self.player.handle_events(key(SDLK_RIGHT))
        self.player._attack_key_down = True
        self.open_menu()
        self.assertEqual(self.player.state, 'IDLE')
        self.assertEqual(self.player.pressed_keys, set())
        self.assertEqual((self.player.move_x, self.player.move_y), (0, 0))
        self.assertFalse(self.player._attack_key_down)

    def test_navigation_wraps_without_equipping_until_confirmed(self):
        self.open_menu()
        self.dispatch(key(SDLK_LEFT))
        self.assertEqual(self.well.menu.focus, 3)
        self.assertEqual(self.player.buff_dice_type, 'attack')
        self.dispatch(key(SDLK_RIGHT))
        self.assertEqual(self.well.menu.focus, 0)
        self.dispatch(key(SDLK_1 + 1))
        self.assertEqual(self.well.menu.focus, 1)

    def test_all_four_choices_update_only_the_stat_die(self):
        for index, kind in enumerate(self.well.menu.KINDS):
            with self.subTest(kind=kind):
                self.open_menu()
                self.dice.sword.roll()
                self.dice.sword.update(.15)
                elapsed = self.dice.sword.roll_elapsed
                self.dice.buff.roll()
                self.dispatch(key(SDLK_1 + index), key(SDLK_RETURN))
                self.dice.update(0)
                self.assertFalse(self.well.menu.is_open)
                self.assertEqual(self.player.buff_dice_type, kind)
                self.assertEqual(self.dice.buff.kind, kind)
                self.assertEqual(self.dice.sword.kind, 'sword')
                self.assertEqual(self.dice.sword.roll_elapsed, elapsed)
                self.assertEqual(self.player.sword_stacks, [0] * 6)

    def test_cancel_keeps_equipment_and_escape_does_not_quit(self):
        self.player.buff_dice_type = 'defense'
        self.open_menu()
        self.assertEqual(self.well.menu.focus, 3)
        self.dispatch(key(SDLK_1), key(SDLK_ESCAPE))
        self.assertEqual(self.player.buff_dice_type, 'defense')
        self.assertFalse(self.well.menu.is_open)
        self.assertTrue(key_handle_events.running)
        self.open_menu()
        self.assertEqual(self.well.menu.focus, 3)

    def test_mouse_selection_converts_top_origin_coordinates(self):
        self.open_menu()
        option = self.well.menu.options[2]
        self.dispatch(SimpleNamespace(type=SDL_MOUSEBUTTONDOWN, button=SDL_BUTTON_LEFT,
                                      x=int(option.left + 64), y=699 - int(option.bottom + 78)))
        self.dice.update(0)
        self.assertEqual(self.dice.buff.kind, 'critical')
        self.assertFalse(self.well.menu.is_open)

    def test_menu_consumes_game_inputs_and_outside_clicks(self):
        self.open_menu()
        self.dispatch(key(SDLK_RIGHT), key(SDLK_a), key(SDLK_r), key(SDLK_f),
                      SimpleNamespace(type=SDL_MOUSEBUTTONDOWN, button=SDL_BUTTON_LEFT, x=20, y=20))
        self.assertTrue(self.well.menu.is_open)
        self.assertEqual(self.player.state, 'IDLE')
        self.assertEqual(self.player.pressed_keys, set())
        self.assertIsNone(self.dice.sword.roll_elapsed)
        self.assertIsNone(self.dice.buff.roll_elapsed)

    def test_window_quit_is_honored_even_with_the_menu_open(self):
        self.open_menu()
        self.dispatch(key(SDLK_1 + 3), SimpleNamespace(type=SDL_QUIT), key(SDLK_RETURN))
        self.assertFalse(key_handle_events.running)
        self.assertEqual(self.player.buff_dice_type, 'attack')

    def test_main_loop_freezes_roll_time_and_does_not_catch_up_after_close(self):
        clock = SimpleNamespace(now=0.0)
        clock.perf_counter = lambda: clock.now
        clock.sleep = lambda seconds: setattr(clock, 'now', clock.now + seconds)
        objects, elapsed = {}, []
        events = iter([[key(SDLK_f)], [key(SDLK_e)], *([[]] * 10),
                       [key(SDLK_ESCAPE)], [], [], [SimpleNamespace(type=SDL_QUIT)]])

        def create_world(player, dice, well):
            player.x, player.y = 1095, 226
            objects.update(player=player, dice=dice, well=well)
            return SimpleNamespace(draw=lambda: None)

        def present():
            elapsed.append(objects['dice'].buff.roll_elapsed)
            clock.now += .1

        with patch.multiple(main, time=clock, open_canvas=lambda *args: None,
                            close_canvas=lambda: None, clear_canvas=lambda: None,
                            update_canvas=present, create_lobby_world=create_world), \
                patch.object(key_handle_events, 'get_events', side_effect=lambda: next(events)):
            main.main()
        self.assertEqual(elapsed[:13], [0.0] * 13)
        self.assertAlmostEqual(elapsed[13], .1)
        self.assertAlmostEqual(elapsed[14], .2)


if __name__ == '__main__':
    unittest.main()
