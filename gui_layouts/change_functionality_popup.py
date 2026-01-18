"""Popup layout to change functionality settings."""

import sys

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys


def create_scoreboard_popup() -> list:
    """Create layout for update team names popup.

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme(colors.THEME_LIGHT_BLUE)
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    window_width, _ = Sg.Window.get_screen_size()

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    button_size = min(max_size, max(14, int(50 * scale)))

    spoiler_button_color = colors.GREEN if settings.no_spoiler_mode else colors.RED
    spoiler_button_text = messages.SPOILER_MODE_ON if settings.no_spoiler_mode else messages.SPOILER_MODE_OFF
    delay_button_color = colors.GREEN if settings.delay else colors.RED
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
        [Sg.Button(messages.BUTTON_RETURN_MAIN, key=ui_keys.MENU_BUTTON, font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1)),
        Sg.Button(messages.BUTTON_RETURN_SCOREBOARD, key=ui_keys.CANCEL_BUTTON, font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1)),
         ],
    ]


def show_scoreboard_popup() -> None:
    """Show a popup screen that give user a choice to change functionality settings."""
    window = Sg.Window(
        messages.CHANGE_FUNCTIONALITY,
        create_scoreboard_popup(),
        no_titlebar=True,
        modal=False,
        keep_on_top=True,
        resizable=True,
        finalize=True,
        auto_close=True,
        auto_close_duration=60,
    )

    while True:
        window.bring_to_front()
        window.force_focus()
        event, _ = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            return

        if ui_keys.DELAY_BUTTON in event:
            settings.delay = not settings.delay
            button_text = messages.DELAY_ON if settings.delay else messages.DELAY_OFF
            button_color = colors.GREEN if settings.delay else colors.RED
            window[ui_keys.DELAY_BUTTON].update(text=button_text, button_color=button_color)

        elif ui_keys.MENU_BUTTON in event:
            sys.exit()

        elif ui_keys.NO_SPOILER_MODE_BUTTON in event:
            settings.no_spoiler_mode = not settings.no_spoiler_mode
            button_text = messages.SPOILER_MODE_ON if settings.no_spoiler_mode else messages.SPOILER_MODE_OFF
            button_color = colors.GREEN if settings.no_spoiler_mode else colors.RED
            window[ui_keys.NO_SPOILER_MODE_BUTTON].update(text=button_text, button_color=button_color)

        elif ui_keys.CANCEL_BUTTON in event:
            window.close()
            return
