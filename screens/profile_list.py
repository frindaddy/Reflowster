from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Footer, Label


class ReflowProfileList(ModalScreen[Path]):
    """A modal screen for selecting a reflow profile."""
    
    AUTO_FOCUS = "#profile-tree"
    BINDINGS = [  # noqa: RUF012
        ("escape", "close_modal", "Close"),
        ("down", "focus_next_widget", "Next"),
        ("right", "focus_next_widget", "Next"),
        ("up", "focus_previous_widget", "Previous"),
        ("left", "focus_previous_widget", "Previous")
    ]
    
    def compose(self) -> ComposeResult:
        with Vertical(id="profile-list"):
            yield Label("Select a Reflow Profile:")
            yield DirectoryTree("reflow_profiles/", id="profile-tree")
            yield Footer()
    
    def action_close_modal(self) -> None:
        self.dismiss(None)
        
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle the selection of a reflow profile file."""
        selected_file = event.path
        if selected_file.is_file() and selected_file.suffix == ".json":
            self.dismiss(selected_file)
            
    def action_focus_next_widget(self) -> None:
        """Move focus to the next available widget."""
        self.screen.focus_next()
    
    def action_focus_previous_widget(self) -> None:
        """Move focus to the previous available widget."""
        self.screen.focus_previous()