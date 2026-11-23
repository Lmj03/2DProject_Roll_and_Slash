POPUP_DURATION = 0.65
POPUP_RISE = 24


def add_damage_popup(popups, damage, x, y, duration=POPUP_DURATION):
    popups.append({'damage': damage, 'x': x, 'y': y, 'remaining': duration})


def update_damage_popups(popups, delta_time):
    for popup in popups:
        popup['remaining'] -= delta_time
    popups[:] = [popup for popup in popups if popup['remaining'] > 1e-9]


def draw_damage_popups(font, popups, duration=POPUP_DURATION, *, camera=None):
    for popup in popups:
        progress = 1.0 - popup['remaining'] / duration
        text = f"-{popup['damage']:g}"
        x = popup['x'] - len(text) * 5
        y = popup['y'] + POPUP_RISE * progress
        if camera is not None:
            x, y = camera.project(x, y)
        font.draw(x + 1, y - 1, text, (35, 7, 5))
        font.draw(x, y, text, (255, 95, 64))
