"""Responsive sizing utilities for GUI elements."""

import FreeSimpleGUI as Sg  # type: ignore[import]


def get_responsive_scale(window_width: int) -> tuple[int, float]:
    """Calculate responsive base width and scale factor.

    :param window_width: Current window width
    :return: Tuple of (base_width, scale)
    """
    common_base_widths = [1366, 1920, 1440, 1280]
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width
    return base_width, scale


def calculate_button_size(scale: float, min_size: int = 14, base_multiplier: int = 50) -> int:
    """Calculate responsive button font size.

    :param scale: Scale factor from get_responsive_scale
    :param min_size: Minimum button size
    :param base_multiplier: Base multiplier for calculation
    :return: Calculated button size
    """
    max_size = 100
    return min(max_size, max(min_size, int(base_multiplier * scale)))


def calculate_text_size(scale: float, min_size: int = 12, base_multiplier: int = 20) -> int:
    """Calculate responsive text font size.

    :param scale: Scale factor from get_responsive_scale
    :param min_size: Minimum text size
    :param base_multiplier: Base multiplier for calculation
    :return: Calculated text size
    """
    max_size = 100
    return min(max_size, max(min_size, int(base_multiplier * scale)))


def calculate_message_size(scale: float, min_size: int = 12, base_multiplier: int = 60) -> int:
    """Calculate responsive message font size.

    :param scale: Scale factor from get_responsive_scale
    :param min_size: Minimum message size
    :param base_multiplier: Base multiplier for calculation
    :return: Calculated message size
    """
    max_size = 100
    return min(max_size, max(min_size, int(base_multiplier * scale)))


def calculate_title_size(scale: float, min_size: int = 40, base_multiplier: int = 50) -> int:
    """Calculate responsive title font size.

    :param scale: Scale factor from get_responsive_scale
    :param min_size: Minimum title size
    :param base_multiplier: Base multiplier for calculation
    :return: Calculated title size
    """
    max_size = 100
    return min(max_size, max(min_size, int(base_multiplier * scale)))


def get_screen_width() -> int:
    """Get current screen width.

    :return: Screen width in pixels
    """
    return Sg.Window.get_screen_size()[0]
