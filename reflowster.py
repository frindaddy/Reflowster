from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, Vertical
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Footer, Header, Label
from textual_plotext import PlotextPlot


class ReflowControl(Vertical):
    """Control panel for the reflow oven."""
    
    current_temperature = reactive(0.0)
    current_time = reactive(0)
    relay_state = reactive(False)
    current_reflow_profile = reactive("Default")
    
    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error", disabled=True)
        yield Label(id="current-temp")
        yield Label(id="current-time")
        yield Label(id="relay-state")
        
        with Vertical(id="profile-selection"):
            yield Button("Change Profile", id="change-profile", variant="default")
            yield Label("Current Profile:")
            yield Label(id="profile-label")
        
    def on_mount(self) -> None:
        self.query_one("#current-temp", Label).update(f"Current Temp: {self.current_temperature:.1f}°C")
        self.query_one("#current-time", Label).update(f"Current Time: {int(self.current_time)}s")
        self.query_one("#relay-state", Label).update(f"Relay State: {'ON' if self.relay_state else 'OFF'}")
        self.query_one("#profile-label", Label).update(f"{self.current_reflow_profile}")
        
    def watch_current_temperature(self, value: float) -> None:
        self.query_one("#current-temp", Label).update(f"Current Temp: {value:.1f}°C")
        
    def watch_current_time(self, value: float) -> None:
        self.query_one("#current-time", Label).update(f"Current Time: {value}s")
        
    def watch_relay_state(self, value: bool) -> None:
        self.query_one("#relay-state", Label).update(f"Relay State: {'ON' if value else 'OFF'}")
        
    def watch_current_reflow_profile(self, value: str) -> None:
        self.query_one("#profile-label", Label).update(f"{value}")
        
    @on(Button.Pressed, "#start")
    def start_reflow(self) -> None:
        """Handle the start button press."""
        # Logic to start the reflow process
        
        start_button = self.query_one("#start", Button)
        stop_button = self.query_one("#stop", Button)
        start_button.disabled = True
        stop_button.disabled = False
        stop_button.focus()
        self.app.log("Reflow process started.")
        
    @on(Button.Pressed, "#stop")
    def stop_reflow(self) -> None:
        """Handle the stop button press."""
        # Logic to stop the reflow process
        
        start_button = self.query_one("#start", Button)
        stop_button = self.query_one("#stop", Button)
        start_button.disabled = False
        stop_button.disabled = True
        start_button.focus()
        self.app.log("Reflow process stopped.")
        
    @on(Button.Pressed, "#change-profile")
    def change_profile(self) -> None:
        """Handle the change profile button press."""
        self.app.push_screen(ReflowProfileList())
        self.app.log("Reflow profile changed.")

class ReflowCurvePlot(PlotextPlot):
    """A widget to display the reflow curve."""
        
    def on_mount(self) -> None:        
        self.plt.title("Reflow Curve")
        self.plt.xlabel("Time (s)")
        self.plt.ylabel("Temperature (°C)")
        
        target_temp = self.plt.sin() # sinusoidal test signal
        actual_temp = self.plt.square() # square wave test signal
        self.plt.plot(target_temp, label="Target Temperature", color="blue")
        self.plt.plot(actual_temp, label="Actual Temperature", color="red")
        
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

class Reflowster(App):
    """A Textual app to control a reflow oven."""

    AUTO_FOCUS = None
    CSS_PATH = "style.tcss"
    BINDINGS = [  # noqa: RUF012
        ("q", "quit", "Quit"),
        ("s", "start_reflow", "Start Reflow"),
        ("t", "stop_reflow", "Stop Reflow"),
        ("c", "change_profile", "Change Profile"),
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
        
    def action_start_reflow(self) -> None:
        """Start the reflow process."""
        self.query_one(ReflowControl).start_reflow()
        
    def action_stop_reflow(self) -> None:
        """Stop the reflow process."""
        self.query_one(ReflowControl).stop_reflow()
        
    def action_change_profile(self) -> None:
        """Change the reflow profile."""
        self.query_one(ReflowControl).change_profile()

if __name__ == "__main__":
    Reflowster().run()