from collision import can_walk_in_lobby


COMBAT_STEP = 1.0 / 60.0


def advance_simulation(player, dice_ui, delta_time, can_move=can_walk_in_lobby, campfire=None, dummy=None,
                       *, targets=(), enemies=()):
    enemies = tuple(enemies)
    combat_targets = (*targets, *enemies)
    if dummy is not None:
        combat_targets = (dummy, *combat_targets)

    def can_step(x, foot_y, *, ignore=None):
        return (can_move is None or can_move(x, foot_y)) and not any(
            target is not ignore and target.blocks(x, foot_y) for target in combat_targets)

    # Equipment can change while simulation time is paused in the well menu.
    dice_ui.update(0.0)
    remaining = delta_time
    while remaining > 0:
        if player.hit_stop_remaining > 0:
            paused = min(remaining, player.hit_stop_remaining)
            player.hit_stop_remaining -= paused
            remaining -= paused
            # Input and the dice HUD remain responsive while combat is frozen.
            dice_ui.update(paused)
            continue
        if player.state == 'FLASH_STRIKE' and player.flash_path is None:
            player.resolve_flash_strike(can_move, can_step)
            for target in combat_targets:
                target.check_attack(player)
            if player.hit_stop_remaining > 0:
                continue
        # Bound movement during contact checks, including slow frames and speed buffs.
        step = min(remaining, campfire.SIMULATION_STEP) if campfire is not None else remaining
        if combat_targets:
            step = min(step, COMBAT_STEP)
        for slot in (dice_ui.sword, dice_ui.buff):
            if slot.roll_elapsed is not None:
                step = min(step, max(1e-9, slot.ROLL_DURATION - slot.roll_elapsed))
        # Resolve a roll at its exact time, then simulate the remainder with its new effect.
        player.update(step, can_step if combat_targets else can_move)
        for target in combat_targets:
            target.update(step)
            if player.state != 'FLASH_STRIKE':
                target.check_attack(player)
        for enemy in enemies:
            enemy.act(player, step, lambda x, y, enemy=enemy: can_step(x, y, ignore=enemy))
        dice_ui.update(step)
        if campfire is not None:
            campfire.update(step)
            campfire.apply_damage(step, player)
        remaining = max(0.0, remaining - step)
