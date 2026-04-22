"""Themes - Terminal color themes."""

from dataclasses import dataclass
from typing import Dict

from rich.theme import Theme as RichTheme
from richpalette import Color


@dataclass
class Theme:
    """Color theme definition."""
    name: str
    primary: str
    accent: str
    warning: str
    critical: str
    think: str
    bg: str
    dim: str
    white: str = "#e8ffe8"


THEMES: Dict[str, Theme] = {
    "matrix": Theme(
        name="matrix",
        primary="#00ff41",
        accent="#00d4ff",
        warning="#ff9f00",
        critical="#ff003c",
        think="#c084fc",
        bg="default",
        dim="#3d5a3d",
    ),
    "dracula": Theme(
        name="dracula",
        primary="#50fa7b",
        accent="#8be9fd",
        warning="#ffb86c",
        critical="#ff5555",
        think="#bd93f9",
        bg="default",
        dim="#44475a",
    ),
    "monokai": Theme(
        name="monokai",
        primary="#a6e22e",
        accent="#66d9e8",
        warning="#e6db74",
        critical="#f92672",
        think="#ae81ff",
        bg="default",
        dim="#75715e",
    ),
    "blood": Theme(
        name="blood",
        primary="#ff2244",
        accent="#ff6600",
        warning="#ffaa00",
        critical="#ffffff",
        think="#cc44ff",
        bg="default",
        dim="#661122",
    ),
}


def get_theme(name: str = "matrix") -> Theme:
    """Get theme by name."""
    return THEMES.get(name.lower(), THEMES["matrix"])


def get_rich_theme(name: str = "matrix") -> RichTheme:
    """Get Rich theme."""
    theme = get_theme(name)

    return RichTheme({
        "primary": theme.primary,
        "accent": theme.accent,
        "warning": theme.warning,
        "critical": theme.critical,
        "think": theme.think,
        "dim": theme.dim,
    })


def get_console_theme(name: str = "matrix") -> Dict[str, str]:
    """Get console color mapping."""
    theme = get_theme(name)

    return {
        "primary": theme.primary,
        "accent": theme.accent,
        "warning": theme.warning,
        "critical": theme.critical,
        "think": theme.think,
        "dim": theme.dim,
        "white": theme.white,
    }


def list_themes() -> list:
    """List available themes."""
    return list(THEMES.keys())