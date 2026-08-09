from textual_plotext import PlotextPlot


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