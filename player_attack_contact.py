HIT_FLASH_DURATION = 0.045


class PlayerAttackContact:
    """Track one target's hits from the player's current swing."""

    def __init__(self):
        self.last_attack_id = None
        self.spin_hit_remaining = 0.0
        self.spin_popup_index = 0

    def update(self, delta_time):
        self.spin_hit_remaining = max(0.0, self.spin_hit_remaining - delta_time)

    def hit(self, player, hurtbox):
        spinning = player.state == 'SWORD_SPIN'
        same_attack = player.attack_id == self.last_attack_id
        if same_attack and (not spinning or self.spin_hit_remaining > 1e-9):
            return None

        attack = player.renderer.attack_box(player)
        if attack is None:
            return None
        overlaps = attack.ellipse_overlaps if spinning else attack.overlaps
        if not overlaps(hurtbox):
            return None

        damage = player.attack_power
        popup_offset = 0
        if spinning:
            if not same_attack:
                self.spin_popup_index = 0
            self.spin_hit_remaining = player.SPIN_HIT_INTERVAL
            damage *= player.SPIN_DAMAGE_MULTIPLIER
            popup_offset = (-24, 24, 0)[self.spin_popup_index % 3]
            self.spin_popup_index += 1
        elif player.state == 'FLASH_STRIKE':
            damage *= player.FLASH_STRIKE_DAMAGE_MULTIPLIER
        self.last_attack_id = player.attack_id
        if damage > 0:
            player.request_hit_stop()
        return damage, popup_offset
