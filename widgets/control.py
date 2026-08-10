import json
import time
from pathlib import Path

import board
import digitalio
from simple_pid import PID
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, Label
from textual.worker import get_current_worker

from hw.max31855 import MAX31855
from hw.ssr import SSR
from screens.profile_list import ReflowProfileList
from widgets.plot import ReflowCurvePlot


class ReflowControl(Vertical):
    """Control panel for the reflow oven."""
    
    can_focus = True    
    
    current_temperature = reactive(0.0)
    current_time = reactive(0)
    relay_state = reactive(False)
    is_reflow_running = reactive(False)
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
    
    BINDINGS = [  # noqa: RUF012
        Binding("s", "start_reflow_action", "Start Reflow", show=True),
        Binding("x", "stop_reflow_action", "Stop Reflow", show=True),
        Binding("c", "change_profile_action", "Change Profile", show=True)
    ]
    
    def __init__(self, relay_pin: int, spi: board.SPI, cs: digitalio.DigitalInOut) -> None:
        super().__init__()
        self.relay_pin = relay_pin
        self.spi = spi
        self.cs = cs
        self.sensor = MAX31855(spi=self.spi, cs=self.cs)
    
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
        self.query_one("#relay-state", Label).update("Relay State: [bold red]OFF[/]")
        self.query_one("#profile-label", Label).update(f"{self.current_reflow_profile.get('name', 'Not Loaded')}")
        
        self.update_temperature()
        
        self.set_interval(5.0, callback=lambda: self.update_temperature() if not self.is_reflow_running else None)
        
        self.focus()
    
    def on_profile_selected(self, selected_file: Path | None) -> None:
        """Handle the selection of a reflow profile."""

        if selected_file is None:
            return

        try:
            profile_data = json.loads(selected_file.read_text())
            if not isinstance(profile_data, dict) or not isinstance(profile_data.get("points"), list):
                self.app.log(f"Selected reflow profile is invalid: {selected_file}")
                return

            self.current_reflow_profile = profile_data
            self.app.log(f"Selected reflow profile: {selected_file}")

        except json.JSONDecodeError:
            self.app.log(f"Error decoding reflow profile: {selected_file}")
            return
    
    def action_start_reflow_action(self) -> None:
        if not self.is_reflow_running:
            self.start_reflow()

    def action_stop_reflow_action(self) -> None:
        if self.is_reflow_running:
            self.stop_reflow()

    def action_change_profile_action(self) -> None:
        if not self.is_reflow_running:
            self.change_profile()
    
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Dynamically enable or disable bindings and palette commands."""
        # Disable 'Start' and 'Change Profile' while reflow is actively running
        if action in ("start_reflow_action", "change_profile_action") and self.is_reflow_running:
            return False

        # Disable 'Stop' when reflow is idle
        if action == "stop_reflow_action" and not self.is_reflow_running:
            return False

        return True
    
    def on_reflow_finished(self, log_message: str = "Reflow process completed.") -> None:
        """Reset UI buttons and state when the reflow process ends."""
        start_button = self.query_one("#start", Button)
        stop_button = self.query_one("#stop", Button)
        change_profile_button = self.query_one("#change-profile", Button)
        
        start_button.disabled = False
        stop_button.disabled = True
        change_profile_button.disabled = False
        start_button.focus()
        
        self.is_reflow_running = False
        self.app.log(log_message)
        
    def update_temperature(self) -> None:
        """Update the current temperature from the MAX31855 sensor."""
        temperature = self.sensor.read_temperature()
        if temperature is None:
            self.app.log("Temperature sensor returned no reading.")
            return

        self.current_temperature = temperature
    
    def watch_current_temperature(self, value: float) -> None:
        self.query_one("#current-temp", Label).update(f"Current Temp: {value:.1f}°C")
        
    def watch_current_time(self, value: float) -> None:
        self.query_one("#current-time", Label).update(f"Current Time: {value}s")
        
    def watch_relay_state(self, value: bool) -> None:
        label_text = "Relay State: [bold green]ON[/]" if value else "Relay State: [bold red]OFF[/]"
        self.query_one("#relay-state", Label).update(label_text)
        
    def watch_current_reflow_profile(self, value: dict) -> None:
        self.query_one("#profile-label", Label).update(f"{value.get('name', 'Not Loaded')}")
        
        target_reflow_curve = value.get("points", [])
        self.app.query_one(ReflowCurvePlot).update_target_curve(target_reflow_curve)
        
    @on(Button.Pressed, "#start")
    def start_reflow(self) -> None:
        """Handle the start button press."""        
        start_button = self.query_one("#start", Button)
        stop_button = self.query_one("#stop", Button)
        change_profile_button = self.query_one("#change-profile", Button)
        
        # Clear previous run's actual temperature line on the plot
        self.app.query_one(ReflowCurvePlot).clear_actual_curve()
        
        pid_parameters_file_path = Path(__file__).resolve().parents[1] / "pid_parameters.json"
        pid_parameters = {"Kp": 1.0, "Ki": 0.1, "Kd": 0.01}

        if pid_parameters_file_path.is_file():
            try:
                loaded_parameters = json.loads(pid_parameters_file_path.read_text())
                if isinstance(loaded_parameters, dict):
                    pid_parameters.update(loaded_parameters)
                    self.app.log(f"Loaded PID parameters from: {pid_parameters_file_path}")
                else:
                    self.app.log(f"PID parameters file {pid_parameters_file_path} does not contain a JSON object.")
            except json.JSONDecodeError:
                self.app.log(f"Error decoding PID parameters from: {pid_parameters_file_path}")

        target_reflow_curve = self.current_reflow_profile.get("points", [])
        if not target_reflow_curve or not all(isinstance(point, (list, tuple)) and len(point) == 2 for point in target_reflow_curve):
            self.app.log("Invalid reflow profile points. Please select a valid profile before starting.")
            return

        safety_cutoff = self.current_reflow_profile.get("safety", {}).get("max_temp_c", 260)

        self.run_reflow(
            pid_parameters=pid_parameters,
            target_reflow_curve=target_reflow_curve,
            safety_cutoff=safety_cutoff
        )

        start_button.disabled = True
        stop_button.disabled = False
        change_profile_button.disabled = True
        stop_button.focus()
        self.app.log("Reflow process started.")
        
    @on(Button.Pressed, "#stop")
    def stop_reflow(self) -> None:
        """Handle the stop button press."""
        self.workers.cancel_group(self, "reflow_worker")
        
    @on(Button.Pressed, "#change-profile")
    def change_profile(self) -> None:
        """Handle the change profile button press."""
        self.app.push_screen(ReflowProfileList(), callback=self.on_profile_selected)
        self.app.log("Reflow profile changed.")

    @work(exclusive=True, thread=True, group="reflow_worker")
    def run_reflow(self, pid_parameters: dict[str, float], target_reflow_curve: list[tuple[float, float]], safety_cutoff: float) -> None:
        """Run the reflow process based on the provided profile."""
        worker = get_current_worker()
        
        self.is_reflow_running = True
        
        ssr = SSR(self.relay_pin)
        pid = PID(
            pid_parameters.get("Kp", 1.0),
            pid_parameters.get("Ki", 0.1),
            pid_parameters.get("Kd", 0.01),
            setpoint=target_reflow_curve[0][1],
        )
        pid.output_limits = (0, 100)
        
        start_time = time.time()
        completion_msg = "Reflow process completed successfully."
        safety_tripped = False
        
        try:
            for i in range(len(target_reflow_curve) - 1):
                t_start, temp_start = target_reflow_curve[i]
                t_end, temp_end = target_reflow_curve[i + 1]

                while not worker.is_cancelled:
                    self.update_temperature()
                    now = time.time() - start_time
                    self.current_time = int(now)

                    # Update plot with actual temperature
                    self.app.call_from_thread(
                        self.app.query_one(ReflowCurvePlot).add_actual_point,
                        round(now, 1),
                        self.current_temperature
                    )
                    
                    # Segment complete, move to next waypoint
                    if now >= t_end:
                        break
                    
                    # Interpolate target setpoint for current time
                    progress = (now - t_start) / (t_end - t_start) if t_end > t_start else 1.0
                    pid.setpoint = temp_start + progress * (temp_end - temp_start)

                    # Safety override for temperatures at or above the configured cutoff.
                    if self.current_temperature >= safety_cutoff:
                        if not safety_tripped:
                            self.app.log(
                                f"SAFETY OVERRIDE: Temp ({self.current_temperature:.1f}°C) >= max limit ({safety_cutoff}°C). SSR disabled."
                            )
                            safety_tripped = True
                        duty_cycle = 0.0
                    else:
                        if safety_tripped:
                            self.app.log(
                                f"SAFETY RECOVERY: Temp ({self.current_temperature:.1f}°C) dropped below max limit. Control restored."
                            )
                            safety_tripped = False
                        duty_cycle = pid(self.current_temperature) / 100.0

                    # Time-Proportional Control (1.0s window)
                    cycle_time = 1.0
                    on_time = cycle_time * duty_cycle
                    off_time = cycle_time - on_time

                    if on_time > 0:
                        ssr.on()
                        self.relay_state = ssr.is_on()
                        time.sleep(on_time)

                    if off_time > 0 and not worker.is_cancelled:
                        ssr.off()
                        self.relay_state = ssr.is_on()
                        time.sleep(off_time)

                if worker.is_cancelled:
                    completion_msg = "Reflow process stopped by user."
                    break

        finally:
            ssr.off()
            self.relay_state = ssr.is_on()
            self.app.call_from_thread(self.on_reflow_finished, completion_msg)