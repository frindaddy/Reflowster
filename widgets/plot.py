from textual_plotext import PlotextPlot


class ReflowCurvePlot(PlotextPlot):
    """A widget to display the reflow curve."""
        
    def on_mount(self) -> None:
        self.plt.title("Reflow Curve")
        self.plt.xlabel("Time (s)")
        self.plt.ylabel("Temperature (°C)")
        
        self.plt.text("NO PROFILE LOADED", 0, 0, color="red")
        
    def update_target_curve(self, points: list[list[float]]) -> None:
        """Update the target temperature curve."""
        if not points:
            return
        
        times, temps = zip(*points)
        self.plt.clear_data()
        self.plt.plot(times, temps, label="Target Temperature", color="blue")
        self.refresh()