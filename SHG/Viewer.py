import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

class Viewer(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        # -------------------------
        # LEFT: SINGLE SHOT PLOT
        # -------------------------
        self.single_plot = pg.PlotWidget(title="Single Shot")
        self.single_curve = self.single_plot.plot(pen='r')

        # -------------------------
        # MIDDLE: AVERAGE PLOT
        # -------------------------
        self.avg_plot = pg.PlotWidget(title="Running Average")
        self.avg_curve = self.avg_plot.plot(pen='w')

        # -------------------------
        # RIGHT: POLAR PLOT
        # -------------------------
        self.polar_plot = pg.PlotWidget(title="Average (Polar)")
        self.polar_plot.setAspectLocked(True)
        self.polar_curve = self.polar_plot.plot(pen='y')

        # Set x-axis limits
        self.single_plot.setXRange(0, 360)
        self.avg_plot.setXRange(0, 360)

        # Tick labels every 15°
        ticks = [(i, str(i)) for i in range(0, 361, 15)]

        self.single_plot.getAxis("bottom").setTicks([ticks])
        self.avg_plot.getAxis("bottom").setTicks([ticks])

        # add to layout
        main_layout.addWidget(self.single_plot)
        main_layout.addWidget(self.avg_plot)
        main_layout.addWidget(self.polar_plot)

    # -------------------------
    # SINGLE SHOT UPDATE
    # -------------------------
    def update_single(self, data):
        angles = np.linspace(0, 360, len(data))

        self.single_curve.setData(angles, data)

    # -------------------------
    # AVERAGE UPDATE
    # -------------------------
    def update_average(self, data):
        angles = np.linspace(0, 360, len(data))
    
        self.avg_curve.setData(angles, data)
        self.update_polar(data)

    # -------------------------
    # POLAR CONVERSION
    # -------------------------
    def update_polar(self, data):
        if data is None:
            return

        angles_deg = np.linspace(0, 360, len(data))
        angles = np.deg2rad(angles_deg)

        r = np.array(data)

        x = r * np.cos(angles)
        y = r * np.sin(angles)

        self.polar_curve.setData(x, y)
    
