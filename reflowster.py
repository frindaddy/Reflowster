import time
import threading
from simple_pid import PID
from gpiozero import OutputDevice
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
import plotext as plt

# --- HARDWARE SETUP ---
ssr = OutputDevice(18)  # GPIO pin driving SSR

class ReflowController:
    def __init__(self):
        self.pid = PID(kp=2.0, ki=0.05, kd=1.0, setpoint=25, output_limits=(0, 100))
        self.current_temp = 25.0
        self.target_temp = 25.0
        self.history_time = []
        self.history_actual = []
        self.history_target = []
        self.running = False

    def read_thermocouple(self):
        # Read from SPI MAX31855 / MAX31856 module
        return self.current_temp  # Placeholder

    def control_loop(self):
        start_time = time.time()
        while self.running:
            loop_start = time.time()
            elapsed = loop_start - start_time
            
            # 1. Update setpoint based on active reflow profile stage
            self.current_temp = self.read_thermocouple()
            duty_cycle = self.pid(self.current_temp) / 100.0  # Normalized 0.0 to 1.0
            
            # 2. Time-proportional SSR drive (1-second total window)
            if duty_cycle > 0:
                ssr.on()
                time.sleep(duty_cycle * 1.0)
            if duty_cycle < 1.0:
                ssr.off()
                time.sleep((1.0 - duty_cycle) * 1.0)

            # 3. Log history for terminal plot
            self.history_time.append(round(elapsed, 1))
            self.history_actual.append(self.current_temp)
            self.history_target.append(self.pid.setpoint)

# --- TEXTUAL TUI INTERFACE ---
class ReflowApp(App):
    BINDINGS = [("s", "start", "Start Profile"), ("q", "stop", "Stop/Emergency Cool")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="plot_container")
        yield Button("Start Reflow", id="start_btn", variant="success")
        yield Button("Stop", id="stop_btn", variant="error")
        yield Footer()

    def update_plot(self):
        # Draw target curve vs actual temp in terminal canvas using plotext
        plt.clear_data()
        plt.plot(controller.history_time, controller.history_target, label="Target (°C)")
        plt.plot(controller.history_time, controller.history_actual, label="Actual (°C)")
        plt.title("Reflowster Profile Plot")
        plot_widget = self.query_one("#plot_container", Static)
        plot_widget.update(plt.build())

if __name__ == "__main__":
    controller = ReflowController()
    app = ReflowApp()
    app.run()