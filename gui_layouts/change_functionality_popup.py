"""Popup layout to change functionality settings."""

import sys

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings


def create_scoreboard_popup() -> list:
    """Create layout for update team names popup.

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme("LightBlue6")
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    window_width, _ = Sg.Window.get_screen_size()

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    button_size = min(max_size, max(14, int(50 * scale)))

    spoiler_button_color = "green" if settings.no_spoiler_mode else "red"
    spoiler_button_text = "No Spoiler Mode: ON" if settings.no_spoiler_mode else "No Spoiler Mode: OFF"
    delay_button_color = "green" if settings.delay else "red"
    delay_button_text = "Delay: ON" if settings.delay else "Delay: OFF"

    return [
        [Sg.Button(spoiler_button_text, key="no_spoiler_mode_button", font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1),
                   button_color=spoiler_button_color,
                   ),
         ],
        [Sg.Button(delay_button_text, key="delay_button", font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1),
                   button_color=delay_button_color,
                   ),
         ],
        [Sg.Button("Return to Main Menu", key="menu_button", font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1)),
        Sg.Button("Return to Scoreboard", key="cancel_button", font=(settings.FONT, button_size),
                   pad=(0), expand_x=True, size=(0, 1)),
         ],
    ]


def show_scoreboard_popup() -> None:
    """Show a popup screen that give user a choice to change functionality settings."""
    window = Sg.Window(
        "Update Display Behavior",
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

        if "delay_button" in event:
            settings.delay = not settings.delay
            button_text = "Delay: ON" if settings.delay else "Delay: OFF"
            button_color = "green" if settings.delay else "red"
            window["delay_button"].update(text=button_text, button_color=button_color)

        elif "menu_button" in event:
            sys.exit()

        elif "no_spoiler_mode_button" in event:
            settings.no_spoiler_mode = not settings.no_spoiler_mode
            button_text = "No Spoiler Mode: ON" if settings.no_spoiler_mode else "No Spoiler Mode: OFF"
            button_color = "green" if settings.no_spoiler_mode else "red"
            window["no_spoiler_mode_button"].update(text=button_text, button_color=button_color)

        elif "cancel_button" in event:
            window.close()
            return
