from dataclasses import dataclass


BUFF_DURATION = 5.0
TIME_EPSILON = 1e-9


@dataclass(frozen=True)
class BuffSpec:
    attribute: str
    amount_per_face: float
    multiplicative: bool
    icon_index: int
    label: str


# Provisional balance: attack/speed/defense +5% per pip, critical chance +3 percentage points.
# Defense increases the defense stat; damage reduction is left to the combat system.
BUFF_SPECS = {
    'attack': BuffSpec('attack_power', 0.05, True, 0, 'ATK'),
    'move': BuffSpec('move_speed', 0.05, True, 1, 'SPEED'),
    'critical': BuffSpec('crit_chance', 0.03, False, 2, 'CRIT'),
    'defense': BuffSpec('defense', 0.05, True, 3, 'DEF'),
}


@dataclass
class ActiveBuff:
    kind: str
    face: int
    remaining: float = BUFF_DURATION

    @property
    def elapsed_ratio(self):
        return max(0.0, min(1.0, 1.0 - self.remaining / BUFF_DURATION))


class BuffState:
    def __init__(self):
        self.active = None

    def apply(self, kind, face):
        if kind not in BUFF_SPECS:
            raise ValueError(f'Unknown buff dice: {kind}')
        if not isinstance(face, int) or isinstance(face, bool) or not 1 <= face <= 6:
            raise ValueError('Buff dice face must be an integer from 1 to 6.')
        # One equipped buff die grants one active effect. Rerolls replace and refresh it.
        self.active = ActiveBuff(kind, face)

    def update(self, delta_time):
        if delta_time <= 0 or self.active is None:
            return
        self.active.remaining = max(0.0, self.active.remaining - delta_time)
        if self.active.remaining <= TIME_EPSILON:
            self.active = None

    def value(self, attribute, base_value):
        active = self.active
        if active is None:
            return base_value
        spec = BUFF_SPECS[active.kind]
        if spec.attribute != attribute:
            return base_value
        amount = spec.amount_per_face * active.face
        value = base_value * (1.0 + amount) if spec.multiplicative else base_value + amount
        return min(1.0, value) if attribute == 'crit_chance' else value
