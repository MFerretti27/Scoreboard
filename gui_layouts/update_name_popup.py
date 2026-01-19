"""Popup layout to update team names."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys
from constants.sizing_utils import (
    calculate_button_size,
    calculate_text_size,
    get_responsive_scale,
    get_screen_width,
)
from get_data.get_team_names import get_new_team_names, update_new_division, update_new_names


def create_update_name_popup_layout() -> list:
    """Create layout for update team names popup.

    :return layout: List of elements and how the should be displayed
    """
    window_width = get_screen_width()
    _, scale = get_responsive_scale(window_width)

    button_size = calculate_button_size(scale)
    message = calculate_text_size(scale, min_size=14)
    return [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text(messages.FETCH_NEW_TEAM_NAMES, key=ui_keys.TOP_MESSAGE,
             font=(settings.FONT, message),
             ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text(messages.ONLY_IF_CHANGED,
             key=ui_keys.MIDDLE_MESSAGE, font=(settings.FONT, message, "underline"),
             ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text(messages.IF_TEAMS_UPDATED, key=ui_keys.BOTTOM_MESSAGE,
             font=(settings.FONT, message),
             ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Button(
                messages.BUTTON_UPDATE,
                key=ui_keys.UPDATE_POPUP_UPDATE,
                font=(settings.FONT, button_size),
                pad=(20),
            ),
            Sg.Button(
                messages.BUTTON_CANCEL,
                key=ui_keys.UPDATE_POPUP_CANCEL,
                font=(settings.FONT, button_size),
                pad=(20),
            ),
            Sg.Push(),
        ],
    ]


def show_fetch_popup(league: str) -> None:
    """Show a popup screen that give user a choice to update team names."""
    window = Sg.Window(
        "Warning",
        create_update_name_popup_layout(),
        modal=True,  # Forces focus until closed
        keep_on_top=True,
        resizable=True,
        finalize=True,
        auto_close=True,
        auto_close_duration=60,
    )

    update = False
    while True:
        window.bring_to_front()
        window.force_focus()
        event, _ = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            return

        if ui_keys.UPDATE_POPUP_UPDATE in event and not update:
            renamed, new_teams, error_message = get_new_team_names(league)
            if "Failed" in error_message:
                window[ui_keys.TOP_MESSAGE].Update(value="")
                window[ui_keys.BOTTOM_MESSAGE].Update(value="")
                window[ui_keys.MIDDLE_MESSAGE].Update(value=error_message, text_color=colors.ERROR_RED)
            elif not renamed:
                window[ui_keys.TOP_MESSAGE].Update(value="")
                window[ui_keys.BOTTOM_MESSAGE].Update(value="")
                window[ui_keys.MIDDLE_MESSAGE].Update(value=messages.NO_NEW_TEAM_NAMES, text_color=colors.NEUTRAL_BLACK)
            else:
                update = True
                display_renamed = ""
                for old, new in renamed:
                    display_renamed += f"{old}  --->  {new}\n"

                window[ui_keys.UPDATE_POPUP_UPDATE].Update(text=messages.BUTTON_CONFIRM)
                window[ui_keys.BOTTOM_MESSAGE].Update(value="")
                window[ui_keys.TOP_MESSAGE].Update(value=messages.TEAM_NAMES_UPDATED)
                window[ui_keys.MIDDLE_MESSAGE].Update(value=display_renamed, text_color=colors.NEUTRAL_BLACK)

        elif ui_keys.UPDATE_POPUP_UPDATE in event and update:
            update_new_names(league, new_teams, renamed)
            error_message = update_new_division(league)
            if "Failed" in error_message:
                window[ui_keys.TOP_MESSAGE].Update(value="")
                window[ui_keys.BOTTOM_MESSAGE].Update(value="")
                window[ui_keys.MIDDLE_MESSAGE].Update(value=error_message, text_color=colors.ERROR_RED)
            else:
                settings.always_get_logos = True  # re-download logos when starting
                window.close()
                return

        elif ui_keys.UPDATE_POPUP_CANCEL in event:
            window.close()
            return
