"""GUI layout for a keyboard input window."""
from __future__ import annotations

import FreeSimpleGUI as Sg


def keyboard_layout(window: Sg.Window, target_key: str | list[str]) -> None:
    """Open a keyboard window to type in text.

    If multiple target keys are provided, will cycle through them on Enter key press.

    :param window: The main window to update text in
    :param target_key: The key of the element to update text for
    """
    layout = [
        [Sg.Button(c, size=(3,1)) for c in "QWERTYUIOP"],
        [Sg.Button(c, size=(3,1)) for c in "ASDFGHJKL"],
        [Sg.Button(c, size=(3,1)) for c in "ZXCVBNM"],
        [
            Sg.Button("Space", size=(6,1)),
            Sg.Button("Back", size=(6,1)),
            Sg.Button("Enter"),
        ],
        [Sg.Text("Press Enter to confirm input")],
    ]

    win = Sg.Window(
        f"Enter Text for {target_key} box",
        layout,
        keep_on_top=True,
        modal=True,
        finalize=True,
        return_keyboard_events=True,
        element_justification="center",
        auto_close=True,
        auto_close_duration=60,
    )

    text = ""

    if isinstance(target_key, list):
        # If multiple keys, focus on the first one
        target = target_key[0]
        list_len = len(target_key)
        current_index = 0
        win.set_title(f"Enter Text for {target} box")
    else:
        target = target_key
        list_len = 0
        current_index = 0

    while True:
        win.bring_to_front()
        win.force_focus()
        event, _ = win.read(timeout=100)

        if event == "Enter":
            if current_index < list_len - 1:
                current_index += 1
                target = target_key[current_index]
                win.set_title(f"Enter Text for {target} box")
                text = ""
                continue

            break

        if event == Sg.WIN_CLOSED:
            break

        if event == "Space":
            text += " "
        elif event == "Back":
            text = text[:-1]
        elif len(event) > 1:
            continue
        else:
            text += event

        window[target].update(text)

    win.close()
