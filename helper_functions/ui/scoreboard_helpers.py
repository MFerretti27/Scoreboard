"""Module to Create and modify scoreboard GUI using FreeSimpleGUI."""
from __future__ import annotations

import platform
import tkinter as tk
from tkinter import font as tk_font

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, ui_keys
from helper_functions.logging.logger_config import logger


def count_lines(text: str) -> int:
    """Count how many lines a string takes up based on newline characters.

    :param text: The string to count lines for
    :return: Number of lines the string occupies
    """
    if not text:
        return 0
    return text.count("\n") + 1


def will_text_fit_on_screen(text: str, txt_size: int | None = None) -> bool:
    """Check if text will fit on screen.

    :param text: str to compare to width of screen

    :return bool: boolean value representing if string will fit on screen
    """
    if settings.no_spoiler_mode:
        return False

    if txt_size is None:
        txt_size = settings.INFO_TXT_SIZE

    screen_width = Sg.Window.get_screen_size()[0]  # Get screen width

    root = tk.Tk()
    root.withdraw()  # Hide the root window
    font = tk_font.Font(family=settings.FONT, size=txt_size)
    txt_width: float = float(font.measure(text))
    txt_width = txt_width * 1.1  # Ensure text fits on screen by adding a buffer
    root.destroy()

    if txt_width >= screen_width:
        logger.info("Bottom Text will scroll, text size: %s, screen size: %s", int(txt_width), screen_width)
        return True

    return False


def reset_window_elements(window: Sg.Window) -> None:
    """Reset window elements to default values.

    :param window: element that can be updated for displaying information
    """
    window[ui_keys.TOP_INFO].update(
        value="",
        font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.BOTTOM_INFO].update(
        value="",
        font=(settings.FONT, settings.INFO_TXT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.HOME_TIMEOUTS].update(
        value="",
        font=(settings.FONT, settings.TIMEOUT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.AWAY_TIMEOUTS].update(
        value="",
        font=(settings.FONT, settings.TIMEOUT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.HOME_RECORD].update(
        value="",
        font=(settings.FONT, settings.RECORD_TXT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.AWAY_RECORD].update(
        value="",
        font=(settings.FONT, settings.RECORD_TXT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.HOME_SCORE].update(
        value="",
        font=(settings.FONT, settings.SCORE_TXT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.AWAY_SCORE].update(
        value="",
        font=(settings.FONT, settings.SCORE_TXT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.ABOVE_SCORE_TXT].update(
        value="",
        font=(settings.FONT, settings.NBA_TIMEOUT_SIZE),
        text_color=colors.TEXT_WHITE,
    )
    window[ui_keys.HOME_PLAYER_STATS].update(value="", text_color=colors.TEXT_WHITE)
    window[ui_keys.AWAY_PLAYER_STATS].update(value="", text_color=colors.TEXT_WHITE)
    window[ui_keys.HYPHEN].update(value="-", font=(settings.FONT, settings.HYPHEN_SIZE), text_color=colors.TEXT_WHITE)
    window[ui_keys.SIGNATURE].update(
        value="Created By: Matthew Ferretti",
        font=(settings.FONT, settings.SIGNATURE_SIZE),
        text_color=colors.TEXT_WHITE,
    )

    window[ui_keys.HOME_TEAM_STATS].update(value="", text_color=colors.TEXT_WHITE)
    window[ui_keys.AWAY_TEAM_STATS].update(value="", text_color=colors.TEXT_WHITE)
    window[ui_keys.UNDER_SCORE_IMAGE].update(filename="")


def resize_text() -> None:
    """Resize text to fit screen size."""
    window_width = Sg.Window.get_screen_size()[0]

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    logger.info("Closest screen size: %s, multiplier: %s\n", base_width, scale)

    max_size = 200
    settings.SCORE_TXT_SIZE = min(max_size, max(40, int(80 * scale)))
    settings.INFO_TXT_SIZE = min(max_size, max(20, int(62 * scale)))
    settings.RECORD_TXT_SIZE = min(max_size, max(35, int(72 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(30, int(50 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(18, int(20 * scale)))
    settings.NOT_PLAYING_TOP_INFO_SIZE = min(max_size, max(10, int(24 * scale)))
    settings.TOP_TXT_SIZE = min(max_size, max(10, int(30 * scale)))
    settings.SIGNATURE_SIZE = min(15, max(7, int(9 * scale)))
    settings.PLAYER_STAT_SIZE = min(18, max(4, int(14 * scale)))
    settings.TEAM_STAT_SIZE = min(18, max(4, int(16 * scale)))
    settings.NBA_TIMEOUT_SIZE = min(max_size, max(8, int(16 * scale)))
    settings.TIMEOUT_HEIGHT = min(max_size, max(20, int(65 * scale)))

    logger.info("\nScore txt size: %s", settings.SCORE_TXT_SIZE)
    logger.info("Info txt size: %s", settings.INFO_TXT_SIZE)
    logger.info("Record txt size: %s", settings.RECORD_TXT_SIZE)
    logger.info("Clock txt size: %s", settings.CLOCK_TXT_SIZE)
    logger.info("Hyphen txt size: %s", settings.HYPHEN_SIZE)
    logger.info("Timeout txt size: %s", settings.TIMEOUT_SIZE)
    logger.info("NBA timeouts txt size: %s", settings.NBA_TIMEOUT_SIZE)
    logger.info("Not playing top txt size: %s", settings.NOT_PLAYING_TOP_INFO_SIZE)
    logger.info("Top txt size: %s", settings.TOP_TXT_SIZE)
    logger.info("Signature txt size: %s", settings.SIGNATURE_SIZE)
    logger.info("Team Stat txt size: %s", settings.TEAM_STAT_SIZE)
    logger.info("Player Stat txt size: %s", settings.PLAYER_STAT_SIZE)
    logger.info("Timeout height size: %s\n", settings.TIMEOUT_HEIGHT)


def maximize_screen(window: Sg.Window) -> None:
    """Maximize the window to fullscreen."""
    # Maximize does not work on MacOS, so we use attributes to set fullscreen
    if platform.system() == "Darwin":
        window.TKroot.attributes("-fullscreen", True)  # noqa: FBT003
    else:
        window.Maximize()


def find_max_font_size(text: str, base_size: int, screen_width: float,
                        max_iterations: int = 100, buffer: float = 1.1) -> int:
    """Find the maximum font size that fits within screen width."""
    for i in range(max_iterations):
        new_txt_size = base_size + i
        font = tk_font.Font(family=settings.FONT, size=new_txt_size)
        txt_width = float(font.measure(text)) * buffer

        if txt_width > screen_width:
            return new_txt_size - 1 if i > 0 else base_size
    return base_size + max_iterations - 1


def _update_font_size(window: Sg.Window, window_key: str, text: str, base_size: int,  # noqa: PLR0913
                      screen_width: float, max_iterations: int = 100, buffer: float = 1.1) -> tuple[int, bool]:
    """Update window element font size and return new size and if it changed.

    :param window: The window element to update
    :param window_key: The key of the window element to update
    :param text: The text to fit
    :param base_size: The base font size to start from
    :param screen_width: The width of the screen to fit within
    :param max_iterations: Maximum iterations to try increasing font size
    :param buffer: Buffer multiplier to ensure text fits comfortably

    :return: Tuple of (new_size, size_changed)
    """
    new_size = find_max_font_size(text, base_size, screen_width, max_iterations, buffer)
    window[window_key].update(font=(settings.FONT, new_size))
    return new_size, new_size != base_size


def increase_text_size(window: Sg.Window, team_info: dict, team_league: str = "",
                       *, currently_playing: bool = False) -> None:
    """Increase the size of the score text and timeouts text if there is more room on the screen.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param team_league: The league of the teams playing
    :param currently_playing: Whether a game is currently in progress; defaults to False.
    :return: None
    """
    root = tk.Tk()
    root.withdraw()

    try:
        log_entries = []
        screen_width = Sg.Window.get_screen_size()[0] / 3

        home_score_str = str(team_info.get("home_score", "0"))
        away_score_str = str(team_info.get("away_score", "0"))
        score_digits = sum(ch.isdigit() for ch in home_score_str + away_score_str)
        score_text = ("88-88" if score_digits <= 3 and settings.display_player_stats
                      else f"{home_score_str}-{away_score_str}")

        new_score_size, score_changed = _update_font_size(window, "home_score", score_text,
                                                           settings.SCORE_TXT_SIZE, screen_width, max_iterations=100)
        window["away_score"].update(font=(settings.FONT, new_score_size))

        new_hyphen_size = settings.HYPHEN_SIZE + (new_score_size - settings.SCORE_TXT_SIZE - 10)
        window["hyphen"].update(font=(settings.FONT, new_hyphen_size))

        if score_changed or new_hyphen_size != settings.HYPHEN_SIZE:
            log_entries.append(f"score: {settings.SCORE_TXT_SIZE}->{new_score_size}, "
                             f"hyphen: {settings.HYPHEN_SIZE}->{new_hyphen_size}")

        # Update timeouts text if present
        if currently_playing:
            # Update timeouts
            timeout_width = screen_width / 2
            timeout_size = settings.NBA_TIMEOUT_SIZE if team_league == "NBA" else settings.TIMEOUT_SIZE
            timeout_text = ("\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF"
                            if team_league == "NBA" else "\u25CF  \u25CF  \u25CF")
            new_timeout_size, timeout_changed = _update_font_size(window, "home_timeouts", timeout_text,
                                                                   timeout_size, timeout_width, max_iterations=50,
                                                                   buffer=1.4)
            window["away_timeouts"].update(font=(settings.FONT, new_timeout_size))
            if timeout_changed:
                log_entries.append(f"timeouts_txt: {timeout_size}->{new_timeout_size}")

            # Update top text
            new_top_size, top_changed = _update_font_size(window, "top_info", team_info.get("top_info", ""),
                                                          settings.NOT_PLAYING_TOP_INFO_SIZE,
                                                          Sg.Window.get_screen_size()[0], buffer=1.5,
                                                          max_iterations=100)

            # Ensure top size does not exceed info text size
            if new_top_size > settings.INFO_TXT_SIZE:
                new_top_size = settings.INFO_TXT_SIZE
                window["top_info"].update(font=(settings.FONT, new_top_size))

            if top_changed:
                log_entries.append(f"top_info: {settings.NOT_PLAYING_TOP_INFO_SIZE}->{new_top_size}")

        # Update above score text if present
        if "above_score_txt" in team_info:
            text = team_info.get("above_score_txt", "")
            has_team_names = "@" in text
            above_width = screen_width / 2 if has_team_names else screen_width
            above_size = settings.TOP_TXT_SIZE if has_team_names else settings.NBA_TIMEOUT_SIZE
            new_above_size, above_changed = _update_font_size(window, "above_score_txt", text,
                                                               above_size, above_width, max_iterations=50, buffer=1.5)
            if above_changed:
                log_entries.append(f"above_score_txt: {above_size}->{new_above_size}")

        if log_entries:
            logger.info("Increased Size: %s", ", ".join(log_entries))

    finally:
        root.destroy()
