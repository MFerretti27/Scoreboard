"""Popup layout to change functionality settings."""

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys
from constants.sizing_utils import (
    calculate_button_size,
    get_responsive_scale,
    get_screen_width,
)


def create_scoreboard_popup() -> list:
    """Create layout for update team names popup.

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme(colors.THEME_LIGHT_BLUE)
    window_width = get_screen_width()
    _, scale = get_responsive_scale(window_width)

    button_size = calculate_button_size(scale)
    return_button_size = min(100, max(14, int(25 * scale)))

    spoiler_button_color = colors.SUCCESS_GREEN if settings.no_spoiler_mode else colors.ERROR_RED
    spoiler_button_text = messages.SPOILER_MODE_ON if settings.no_spoiler_mode else messages.SPOILER_MODE_OFF
    delay_button_color = colors.SUCCESS_GREEN if settings.delay else colors.ERROR_RED
    delay_button_text = messages.DELAY_ON if settings.delay else messages.DELAY_OFF

    return [
        [Sg.Button(spoiler_button_text, key=ui_keys.NO_SPOILER_MODE_BUTTON, font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1),
                   button_color=spoiler_button_color,
                   ),
         ],
        [Sg.Button(delay_button_text, key=ui_keys.DELAY_BUTTON, font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1),
                   button_color=delay_button_color,
                   ),
         ],
        [Sg.Button(messages.BUTTON_RETURN_MAIN, key=ui_keys.MENU_BUTTON, font=(settings.FONT, return_button_size),
                   pad=(5), expand_x=True, size=(0, 1)),
        Sg.Button(messages.BUTTON_RETURN_SCOREBOARD, key=ui_keys.CANCEL_BUTTON,
                  font=(settings.FONT, return_button_size), pad=(5), expand_x=True, size=(0, 1)),
         ],
    ]


def show_scoreboard_popup() -> str | None:
    """Show a popup to toggle delay/spoiler or return to menu.

    :return: "MENU" if user chooses to return to main menu, None otherwise.
    """
    window = Sg.Window(
        messages.CHANGE_FUNCTIONALITY,
        create_scoreboard_popup(),
        no_titlebar=True,
        modal=False,
        keep_on_top=True,
        resizable=True,
        finalize=True,
        auto_close=True,
        auto_close_duration=20,
    )
    window.keep_on_top_set()

    while True:
        window.bring_to_front()
        event, _ = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            return None

        if ui_keys.DELAY_BUTTON in event:
            settings.delay = not settings.delay
            button_text = messages.DELAY_ON if settings.delay else messages.DELAY_OFF
            button_color = colors.SUCCESS_GREEN if settings.delay else colors.ERROR_RED
            window[ui_keys.DELAY_BUTTON].update(text=button_text, button_color=button_color)

        elif ui_keys.MENU_BUTTON in event:
            window.close()
            return "MENU"

        elif ui_keys.NO_SPOILER_MODE_BUTTON in event:
            settings.no_spoiler_mode = not settings.no_spoiler_mode
            button_text = messages.SPOILER_MODE_ON if settings.no_spoiler_mode else messages.SPOILER_MODE_OFF
            button_color = colors.SUCCESS_GREEN if settings.no_spoiler_mode else colors.ERROR_RED
            window[ui_keys.NO_SPOILER_MODE_BUTTON].update(text=button_text, button_color=button_color)

        elif ui_keys.CANCEL_BUTTON in event:
            window.close()
            return None
