"""Popup layout to update team names."""

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from get_data.get_team_names import get_new_team_names, update_new_division, update_new_names


def create_update_name_popup_layout() -> list:
    """Create layout for update team names popup.

    :return layout: List of elements and how the should be displayed
    """
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    window_width, _ = Sg.Window.get_screen_size()

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    button_size = min(max_size, max(14, int(50 * scale)))
    message = min(max_size, max(14, int(20 * scale)))
    return [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("This will fetch new team names", key="top_message",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("Only do this if a team has changed their name",
                 key="middle_message", font=(settings.FONT, message, "underline"),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("\nIf Team's are updated logo's will be re-downloaded when starting", key="bottom_message",
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
        [Sg.Push(),
         Sg.Button("Update", key="update", font=(settings.FONT, button_size), pad=(20)),
         Sg.Button("Cancel", key="cancel", font=(settings.FONT, button_size), pad=(20)),
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

        if "update" in event and not update:
            renamed, new_teams, error_message = get_new_team_names(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value=error_message, text_color="red")
            elif not renamed:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value="No New Team Names Found", text_color="black")
            else:
                update = True
                display_renamed = ""
                for old, new in renamed:
                    display_renamed += f"{old}  --->  {new}\n"

                window["update"].Update(text="Confirm")
                window["bottom_message"].Update(value="")
                window["top_message"].Update(value="Found New Team Names, Press Confirm to Update")
                window["middle_message"].Update(value=display_renamed, text_color="black")

        elif "update" in event and update:
            update_new_names(league, new_teams, renamed)
            error_message = update_new_division(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value=error_message, text_color="red")
            else:
                settings.always_get_logos = True  # re-download logos when starting
                window.close()
                return

        elif "cancel" in event:
            window.close()
            return
