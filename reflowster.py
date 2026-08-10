import argparse

import board
import digitalio
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Footer, Header

from widgets.control import ReflowControl
from widgets.plot import ReflowCurvePlot


class Reflowster(App):
    """A Textual app to control a reflow oven."""

    AUTO_FOCUS = None
    CSS_PATH = "style.tcss"
    BINDINGS = [  # noqa: RUF012
        ("q", "quit", "Quit"),
        ("down", "focus_next_widget", "Next"),
        ("right", "focus_next_widget", "Next"),
        ("up", "focus_previous_widget", "Previous"),
        ("left", "focus_previous_widget", "Previous")
    ]

    def __init__(self, relay_pin: int, spi: board.SPI, cs: digitalio.DigitalInOut, **kwargs) -> None:
        super().__init__(**kwargs)
        self.relay_pin = relay_pin
        self.spi = spi
        self.cs = cs

    def compose(self) -> ComposeResult:
        yield Header()
        yield HorizontalGroup(
            ReflowControl(relay_pin=self.relay_pin, spi=self.spi, cs=self.cs),
            ReflowCurvePlot()
        )
        yield Footer()

    def action_focus_next_widget(self) -> None:
        """Move focus to the next available widget."""
        self.screen.focus_next()

    def action_focus_previous_widget(self) -> None:
        """Move focus to the previous available widget."""
        self.screen.focus_previous()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--relay-pin", default=17, type=int, help="GPIO pin number for the SSR relay")
    parser.add_argument("--cs-pin", default="D5", help="Board pin name used for MAX31855 CS")
    args = parser.parse_args()

    spi = board.SPI()
    try:
        cs_pin = getattr(board, args.cs_pin)
    except AttributeError as error:
        raise SystemExit(f"Unknown board pin '{args.cs_pin}'.") from error
    cs = digitalio.DigitalInOut(cs_pin)

    Reflowster(relay_pin=args.relay_pin, spi=spi, cs=cs).run()
