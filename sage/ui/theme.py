"""SAGE theme — Rich console, colors, identity, and ASCII banner."""

from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

# ── SAGE Color Palette ───────────────────────────────────────────
COLORS = {
    "primary": "#7C9EFF",       # soft electric blue
    "secondary": "#A78BFA",     # muted violet
    "accent": "#34D399",        # emerald green — success/completion
    "warning": "#FBBF24",       # amber
    "error": "#F87171",         # soft red
    "bg": "#0F0F1A",            # near black
    "muted": "#4B5563",         # gray
    "text": "#E5E7EB",          # light gray text
    "bright": "#FFFFFF",        # white
}

# ── Rich Theme ───────────────────────────────────────────────────
SAGE_THEME = Theme({
    "sage.primary": COLORS["primary"],
    "sage.secondary": COLORS["secondary"],
    "sage.accent": COLORS["accent"],
    "sage.warning": COLORS["warning"],
    "sage.error": COLORS["error"],
    "sage.muted": COLORS["muted"],
    "sage.text": COLORS["text"],
    "sage.bright": COLORS["bright"],
    "sage.success": COLORS["accent"],
    # Pipeline status styles
    "sage.done": f"bold {COLORS['accent']}",
    "sage.running": f"bold {COLORS['primary']}",
    "sage.pending": COLORS["muted"],
    "sage.failed": f"bold {COLORS['error']}",
    # Info styles
    "sage.label": f"bold {COLORS['secondary']}",
    "sage.value": COLORS["text"],
    "sage.dim": COLORS["muted"],
})

# ── Console Singleton ────────────────────────────────────────────
console = Console(theme=SAGE_THEME, highlight=False)

# ── ASCII Banner ─────────────────────────────────────────────────
BANNER_RAW = r"""
 ░██████╗░█████╗░░██████╗░███████╗
 ██╔════╝██╔══██╗██╔════╝░██╔════╝
 ╚█████╗░███████║██║░░██╗░█████╗░░
 ░╚═══██╗██╔══██║██║░░╚██╗██╔══╝░░
 ██████╔╝██║░░██║╚██████╔╝███████╗
 ╚═════╝░╚═╝░░╚═╝░╚═════╝░╚══════╝
""".strip()

SUBTITLE = "Study · Ask · Generate · Explain"


def _gradient_banner() -> Text:
    """Create the SAGE banner with a blue→violet gradient."""
    lines = BANNER_RAW.split("\n")
    text = Text()
    total = len(lines)
    for i, line in enumerate(lines):
        # Interpolate from primary (#7C9EFF) to secondary (#A78BFA)
        ratio = i / max(total - 1, 1)
        r = int(0x7C + (0xA7 - 0x7C) * ratio)
        g = int(0x9E + (0x8B - 0x9E) * ratio)
        b = int(0xFF + (0xFA - 0xFF) * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        text.append(line + "\n", style=f"bold {color}")
    return text


def print_banner(subject: str | None = None, unit: str | None = None) -> None:
    """Print the SAGE banner with optional subject/unit context."""
    banner_text = _gradient_banner()

    # Subtitle line
    subtitle = Text(f"        {SUBTITLE}", style=f"italic {COLORS['muted']}")

    # Context line
    context_parts: list[str] = []
    if subject:
        context_parts.append(subject)
    if unit:
        context_parts.append(unit)

    content = Text()
    content.append_text(banner_text)
    content.append_text(subtitle)

    if context_parts:
        context_line = Text(
            f"\n        {' · '.join(context_parts)}",
            style=f"bold {COLORS['text']}",
        )
        content.append_text(context_line)

    panel = Panel(
        Align.center(content),
        border_style=COLORS["muted"],
        padding=(1, 2),
    )
    console.print(panel)


def print_error(message: str) -> None:
    """Print a styled error panel."""
    console.print(
        Panel(
            f"[sage.error]❌ {message}[/]",
            border_style=COLORS["error"],
            title="[sage.error]Error[/]",
            title_align="left",
        )
    )


def print_warning(message: str) -> None:
    """Print a styled warning panel."""
    console.print(
        Panel(
            f"[sage.warning]⚠️  {message}[/]",
            border_style=COLORS["warning"],
            title="[sage.warning]Warning[/]",
            title_align="left",
        )
    )


def print_success(message: str) -> None:
    """Print a styled success panel."""
    console.print(
        Panel(
            f"[sage.accent]✓ {message}[/]",
            border_style=COLORS["accent"],
            title="[sage.accent]Success[/]",
            title_align="left",
        )
    )


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"  [sage.primary]ℹ[/]  [sage.text]{message}[/]")
