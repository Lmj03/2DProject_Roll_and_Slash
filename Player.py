from math import isfinite

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_1, SDLK_6, SDLK_a
from transitions import Machine

from buffs import BuffState
import player_movement as movement
from player_rendering import DOWN_ATTACK_WIDTH_SCALE, PlayerRenderer


class player:
    UP, RIGHT, DOWN, LEFT = movement.UP, movement.RIGHT, movement.DOWN, movement.LEFT
    MOVE_SPEED = 360.0  # Pixels per second.
    MAX_MOVE_STEP = 6.0
    IDLE_FRAME_TIME = 0.1
    RUN_FRAME_TIME = 0.02
    ATTACK_FRAME_TIME = 0.05
    SWORD_SKILL_TIMINGS = {
        'QUICK_THRUST': (0.05, 6),        # Frame time in seconds, frame count.
        'HORIZONTAL_SLASH': (0.065, 6),
    }
    ATTACK_STATES = ('ATTACK', *SWORD_SKILL_TIMINGS)
    # Temporary animation preview mode. Keep enabled until removal is requested.
    ALLOW_SKILLS_WITHOUT_STACKS = True
    ANIMATION_EPSILON = 1e-9  # Tolerance for floating-point frame boundaries.
    HIT_FLASH_TIME = 0.16
    DAMAGE_POPUP_TIME = 0.65
    FOOT_OFFSET_Y = 36  # Distance below the center of an unscaled sprite.

    def __init__(self):
        self.max_hp = 100
        self.hp = self.max_hp
        self.hit_flash_remaining = 0.0
        self.damage_popups = []
        self.buffs = BuffState()
        self.base_attack_power = 50
        self.base_crit_chance = 0.30  # Probability from 0 to 1.
        self.crit_damage_multiplier = 1.50  # Total critical damage multiplier.
        self.base_defense = 50
        self.base_move_speed = self.MOVE_SPEED  # Pixels per second.
        # Skill order: thrust, sweep, dash, counter, spin, flash. Caps are provisional.
        self.sword_max_stacks = (5, 4, 3, 3, 2, 2)
        self.sword_stacks = [0] * 6
        self.buff_dice_type = 'attack'
        self.x = 400
        self.y = 300
        self.frame = 0
        self._animation_time = 0.0
        self._attack_key_down = False
        self.attack_combo = 0
        self.renderer = PlayerRenderer()
        self.dir = self.UP
        self.pressed_keys = set()
        self.move_x = 0
        self.move_y = 0
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', *self.ATTACK_STATES],
            transitions=[
                {'trigger': 'start_running', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop_running', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'start_attack', 'source': ['IDLE', 'RUN'], 'dest': 'ATTACK'},
                {'trigger': 'start_quick_thrust', 'source': ['IDLE', 'RUN'], 'dest': 'QUICK_THRUST'},
                {'trigger': 'start_horizontal_slash', 'source': ['IDLE', 'RUN'], 'dest': 'HORIZONTAL_SLASH'},
                {'trigger': 'stop_attack', 'source': list(self.ATTACK_STATES), 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            after_state_change='_reset_animation',
        )

    def take_damage(self, amount):
        """Apply already-resolved damage and return the actual HP lost."""
        if not isfinite(amount) or amount <= 0 or self.hp <= 0:
            return 0
        damage = min(self.hp, amount)
        self.hp = max(0, self.hp - damage)
        self.hit_flash_remaining = self.HIT_FLASH_TIME
        self.damage_popups.append({
            'damage': damage, 'x': self.x, 'y': self.y + 55,
            'remaining': self.DAMAGE_POPUP_TIME,
        })
        return damage

    @property
    def attack_power(self):
        return self.buffs.value('attack_power', self.base_attack_power)

    @property
    def crit_chance(self):
        return self.buffs.value('crit_chance', self.base_crit_chance)

    @property
    def defense(self):
        return self.buffs.value('defense', self.base_defense)

    @property
    def move_speed(self):
        return self.buffs.value('move_speed', self.base_move_speed)

    def _reset_animation(self):
        self.frame = 0
        self._animation_time = 0.0

    def reset_inputs(self):
        self.pressed_keys.clear()
        self._attack_key_down = False
        self._sync_movement()

    def handle_events(self, event):
        if event.type not in (SDL_KEYDOWN, SDL_KEYUP):
            return

        if event.key == SDLK_a:
            if event.type == SDL_KEYUP:
                self._attack_key_down = False
            elif not self._attack_key_down:
                self._attack_key_down = True
                if self.state in ('IDLE', 'RUN'):
                    self.start_attack()
            return

        if event.type == SDL_KEYDOWN and SDLK_1 <= event.key <= SDLK_6:
            index = event.key - SDLK_1
            skill_starters = (self.start_quick_thrust, self.start_horizontal_slash)
            if index < len(skill_starters):
                self._try_sword_skill(index, skill_starters[index])
            elif self.sword_stacks[index] > 0:
                self.sword_stacks[index] -= 1
            return

        if event.key not in movement.MOVEMENT_KEYS:
            return

        if event.type == SDL_KEYDOWN:
            self.pressed_keys.add(event.key)
        else:
            self.pressed_keys.discard(event.key)

        if self.state in self.ATTACK_STATES:
            return
        self._sync_movement()

    def _try_sword_skill(self, index, start_skill):
        if self.state not in ('IDLE', 'RUN'):
            return
        stacks = self.sword_stacks[index]
        if stacks <= 0 and not self.ALLOW_SKILLS_WITHOUT_STACKS:
            return
        start_skill()
        if stacks > 0:
            self.sword_stacks[index] -= 1

    def _sync_movement(self):
        self.move_x, self.move_y = movement.movement_axes(self.pressed_keys)
        if self.move_x or self.move_y:
            if self.move_x:
                self.dir = self.RIGHT if self.move_x > 0 else self.LEFT
            else:
                self.dir = self.UP if self.move_y > 0 else self.DOWN
            if self.state == 'IDLE':
                self.start_running()
        elif self.state == 'RUN':
            self.stop_running()

    def update(self, delta_time, can_move=None):
        if delta_time <= 0:
            return

        self.hit_flash_remaining = max(0.0, self.hit_flash_remaining - delta_time)
        for popup in self.damage_popups:
            popup['remaining'] -= delta_time
        self.damage_popups = [popup for popup in self.damage_popups if popup['remaining'] > 1e-9]

        # Split at expiry so movement uses the buff only for its actual remaining time.
        if self.buffs.active is not None:
            active_time = min(delta_time, self.buffs.active.remaining)
            self._update_motion(active_time, can_move)
            self.buffs.update(active_time)
            delta_time -= active_time
        if delta_time > 0:
            self._update_motion(delta_time, can_move)

    def _update_motion(self, delta_time, can_move):
        self._animation_time += delta_time
        if self.state in self.ATTACK_STATES:
            normal_attack = self.state == 'ATTACK'
            frame_time, frame_count = self.SWORD_SKILL_TIMINGS.get(self.state, (self.ATTACK_FRAME_TIME, 10))
            duration = frame_time * frame_count
            if self._animation_time < duration - self.ANIMATION_EPSILON:
                self.frame = int((self._animation_time + self.ANIMATION_EPSILON) / frame_time)
                return

            # Use the rest of this frame after the attack for idle or resumed movement.
            delta_time = max(0.0, self._animation_time - duration)
            self.stop_attack()
            self._sync_movement()
            if normal_attack:
                self.attack_combo = (self.attack_combo + 1) % 3
            self._animation_time = delta_time

        if self.state == 'RUN':
            self.x, self.y = movement.move_position(
                (self.x, self.y), (self.move_x, self.move_y), self.move_speed * delta_time,
                can_move=can_move, foot_offset_y=self.FOOT_OFFSET_Y, max_step=self.MAX_MOVE_STEP,
            )
            frame_time, frame_count = self.RUN_FRAME_TIME, 10
        else:
            frame_time, frame_count = self.IDLE_FRAME_TIME, 6

        self._animation_time %= frame_time * frame_count
        self.frame = int((self._animation_time + self.ANIMATION_EPSILON) / frame_time) % frame_count

    def draw(self):
        self.renderer.draw(self)
