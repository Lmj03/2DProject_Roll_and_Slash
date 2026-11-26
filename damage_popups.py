POPUP_DURATION = 0.65
POPUP_RISE = 24


def format_health_value(value):
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def add_damage_popup(popups, damage, x, y, duration=POPUP_DURATION, *, critical=False):
    popups.append({'damage': damage, 'x': x, 'y': y, 'remaining': duration, 'critical': critical})


def update_damage_popups(popups, delta_time):
    for popup in popups:
        popup['remaining'] -= delta_time
    popups[:] = [popup for popup in popups if popup['remaining'] > 1e-9]


def draw_damage_popups(font, popups, duration=POPUP_DURATION, *, camera=None):
    for popup in popups:
        progress = 1.0 - popup['remaining'] / duration
        critical = popup.get('critical', False)
        text = f"-{format_health_value(popup['damage'])}" + ('!' if critical else '')
        x = popup['x'] - len(text) * 5
        y = popup['y'] + POPUP_RISE * progress
        if camera is not None:
            x, y = camera.project(x, y)
        font.draw(x + 1, y - 1, text, (35, 7, 5))
        color = (255, 214, 88) if critical else (255, 95, 64)
        font.draw(x, y, text, color)
