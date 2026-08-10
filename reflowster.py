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

    def compose(self) -> ComposeResult:
        
        yield Header()
        yield HorizontalGroup(
            ReflowControl(),
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
    Reflowster().run()