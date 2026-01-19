"""GUI layout for a keyboard input window."""
from __future__ import annotations

import FreeSimpleGUI as Sg
from adafruit_ticks import ticks_diff, ticks_ms  # type: ignore[import]

from constants import messages


def _create_keyboard_window(title: str) -> Sg.Window:
    """Create and return the keyboard window with layout."""
    letter_rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    layout = [
        [Sg.Text("Keyboard will auto-close in 60 seconds", key="TimeoutText")],
        [Sg.Button(c, size=(3,1), pad=(5, 15, 0, 0), key=c) for c in "0123456789"],
        [Sg.Frame("",
                  [
                    [Sg.Button(c, size=(3,1), key=c) for c in letter_rows[0]],
                    [Sg.Button(c, size=(3,1), key=c) for c in letter_rows[1]],
                    [Sg.Button(c, size=(3,1), key=c) for c in letter_rows[2]],
                ],
            element_justification="center",
            ),
        ],
        [
            Sg.Button("Space", size=(12,1), key="Space"),
            Sg.Button("Caps", size=(12,1), key="Caps"),
            Sg.Button(messages.BUTTON_BACK, size=(12,1), key="Back"),
            Sg.Button("Enter", size=(12,1), key="Enter"),
        ],
        [Sg.Text("Press Enter to confirm input")],
    ]

    return Sg.Window(
        title,
        layout,
        keep_on_top=True,
        modal=True,
        finalize=True,
        return_keyboard_events=True,
        element_justification="center",
        auto_close=True,
        auto_close_duration=60,
    )


def _handle_keyboard_event(event: str, text: str, letter_keys: set,
                           win: Sg.Window, *, uppercase: bool) -> tuple[str, bool]:
    """Process a keyboard event and return updated text and uppercase state."""
    if event == "Space":
        return text + " ", uppercase
    if event == "Back":
        return text[:-1], uppercase
    if event == "Caps":
        return text, not uppercase
    if len(event) > 1:
        return text, uppercase

    event_upper = event.upper()
    if event_upper in letter_keys:
        return text + win[event_upper].ButtonText, uppercase
    return text + event, uppercase


def keyboard_layout(window: Sg.Window, target_key: str | list[str]) -> None:
    """Open a keyboard window to type in text.

    If multiple target keys are provided, will cycle through them on Enter key press.

    :param window: The main window to update text in
    :param target_key: The key of the element to update text for
    """
    letter_rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    letter_keys = set("".join(letter_rows))

    if isinstance(target_key, list):
        target = target_key[0]
        list_len = len(target_key)
        current_index = 0
    else:
        target = target_key
        list_len = 0
        current_index = 0

    win = _create_keyboard_window(f"Enter Text for {target} box")
    win.keep_on_top_set()
    text = ""
    uppercase = True
    time_till_close = ticks_ms()

    def set_letter_case(*, to_upper: bool) -> None:
        for letter in letter_keys:
            win[letter].update(letter if to_upper else letter.lower())

    while True:
        if win.is_closed():
            break

        try:
            win.bring_to_front()
            win["TimeoutText"].update(
                "Keyboard will auto-close in"
                f" {60 - ticks_diff(ticks_ms(), time_till_close) // 1000} seconds",
            )
            event, _ = win.read(timeout=100)
        except Exception:
            break

        if win.is_closed():
            break

        if event is None:
            continue

        if event == "Enter":
            if isinstance(target_key, list) and current_index < list_len - 1:
                current_index += 1
                target = target_key[current_index]
                win.set_title(f"Enter Text for {target} box")
                text = ""
                continue
            break

        if event == Sg.WIN_CLOSED:
            break

        if event == "Caps":
            uppercase = not uppercase
            set_letter_case(to_upper=uppercase)
            continue

        text, uppercase = _handle_keyboard_event(event, text, letter_keys, win, uppercase=uppercase)
        window[target].update(text)

    win.close()
