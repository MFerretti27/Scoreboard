"""GUI layout for a keyboard input window."""
import FreeSimpleGUI as Sg


def keyboard_layout(window: Sg.Window, target_key: str | list[str]) -> None:
    """Open a keyboard window to type in text.

    if multiple target keys are provided, will cycle through them on Enter key press.

    param window: The main window to update text in
    param target_key: The key of the element to update text for
    """
    layout = [
        [Sg.Button(c) for c in "QWERTYUIOP"],
        [Sg.Button(c) for c in "ASDFGHJKL"],
        [Sg.Button(c) for c in "ZXCVBNM"],
        [
            Sg.Button("Space"),
            Sg.Button("Back"),
            Sg.Button("Enter"),
        ],
        [Sg.Text("Press Enter to confirm input")],
    ]

    win = Sg.Window(
        f"Enter Text for {target_key} box",
        layout,
        keep_on_top=True,
        finalize=True,
        resizable=True,
        element_justification="center",
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
        event, _ = win.read()

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
        else:
            text += event

        window[target].update(text)

    win.close()
