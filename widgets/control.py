from textual import on
import json
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, Label

from screens.profile_list import ReflowProfileList


class ReflowControl(Vertical):
    """Control panel for the reflow oven."""
    
    current_temperature = reactive(0.0)
    current_time = reactive(0)
    relay_state = reactive(False)
    current_reflow_profile = reactive(
        {
            "name": "Sn63Pb37 #5",
            "description": "Reflow profile for Sn63Pb37 solder paste (#5). Times in seconds, temps in °C (e.g. points: [time, temperature]). Max temp is 250C.",
            "metadata": { "paste": "Sn63Pb37", "type": "#5", "author": "Reflowster-default" },
            "safety": { "max_temp_c": 260 },
            "points": [
                [0, 25],
                [90, 150],
                [150, 170],
                [210, 170],
                [255, 235],
                [285, 235],
                [360, 50]
            ]
        }
    )
    
    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error", disabled=True)
        yield Label(id="current-temp")
        yield Label(id="current-time")
        yield Label(id="relay-state")
        
        with Vertical(id="profile-selection"):
            yield Button("Change Profile", id="change-profile", variant="primary")
            yield Label("Current Profile:")
            yield Label(id="profile-label")
        
    def on_mount(self) -> None:
        self.query_one("#current-temp", Label).update(f"Current Temp: {self.current_temperature:.1f}°C")
        self.query_one("#current-time", Label).update(f"Current Time: {int(self.current_time)}s")
        self.query_one("#relay-state", Label).update(f"Relay State: {'ON' if self.relay_state else 'OFF'}")
        self.query_one("#profile-label", Label).update(f"{self.current_reflow_profile.get('name', 'Not Loaded')}")
    
    def on_profile_selected(self, selected_file: Path | None) -> None:
        """Handle the selection of a reflow profile."""
        
        if selected_file is None:
            return
        
        try:
            self.current_reflow_profile = json.loads(selected_file.read_text())
            self.app.log(f"Selected reflow profile: {selected_file}")
            
        except json.JSONDecodeError:
            self.app.log(f"Error decoding reflow profile: {selected_file}")
            return
    
    def watch_current_temperature(self, value: float) -> None:
        self.query_one("#current-temp", Label).update(f"Current Temp: {value:.1f}°C")
        
    def watch_current_time(self, value: float) -> None:
        self.query_one("#current-time", Label).update(f"Current Time: {value}s")
        
    def watch_relay_state(self, value: bool) -> None:
        self.query_one("#relay-state", Label).update(f"Relay State: {'ON' if value else 'OFF'}")
        
    def watch_current_reflow_profile(self, value: dict) -> None:
        self.query_one("#profile-label", Label).update(f"{value.get('name', 'Not Loaded')}")
        
        target_reflow_curve = value.get("points", [])
        self.app.query_one("ReflowCurvePlot").update_target_curve(target_reflow_curve)
        
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
