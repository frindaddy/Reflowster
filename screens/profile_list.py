from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Label


class ReflowProfileList(ModalScreen):
    """A modal screen for selecting a reflow profile."""
    
    BINDINGS = [  # noqa: RUF012
        ("escape", "close_modal", "Close")
    ]
    
    def compose(self) -> ComposeResult:
        with Vertical(id="profile-list"):
            yield Label("Select a Reflow Profile:")
            yield DirectoryTree("profiles/", id="profile-tree")
            
    def action_close_modal(self) -> None:
        self.dismiss()