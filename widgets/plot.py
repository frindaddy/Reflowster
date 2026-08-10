from textual_plotext import PlotextPlot


class ReflowCurvePlot(PlotextPlot):
    """A widget to display the reflow curve."""
        
    def on_mount(self) -> None:
        self.target_x: list[float] = []
        self.target_y: list[float] = []
        self.actual_x: list[float] = []
        self.actual_y: list[float] = []
        
        self.plt.title("Reflow Curve")
        self.plt.xlabel("Time (s)")
        self.plt.ylabel("Temperature (°C)")
        
        self.plt.text("NO PROFILE LOADED", 0, 0, color="red")
        
    def add_actual_point(self, time_s: float, temp_c: float) -> None:
            """Append a new live sample and redraw."""
            self.actual_x.append(time_s)
            self.actual_y.append(temp_c)
            self.redraw()
    
    def clear_actual_curve(self) -> None:
        """Reset actual temperature history for a new run."""
        self.actual_x.clear()
        self.actual_y.clear()
        self.redraw()

    def redraw(self) -> None:
        """Re-render both curves on the plot."""
        self.plt.clear_data()

        if self.target_x and self.target_y:
            self.plt.plot(self.target_x, self.target_y, label="Target Temperature", color="blue")

        if self.actual_x and self.actual_y:
            self.plt.plot(self.actual_x, self.actual_y, label="Actual Temperature", color="red")

        self.refresh()
        
    def update_target_curve(self, points: list[list[float]] | list[tuple[float, float]]) -> None:
        """Set target profile points and redraw."""
        self.target_x = [pt[0] for pt in points]
        self.target_y = [pt[1] for pt in points]
        self.redraw()
    