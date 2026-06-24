#This file handles displaying the data from the single shot and average shots
#Author(s): Josh Woznicki, Quinn Meece

#Imports
from collections import deque
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore


app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(show=True)
win.resize(1200, 800)
win.setWindowTitle("Pump-Probe Live Monitor")

plot_delta = win.addPlot(title="ΔI/I₀")
curve_delta = plot_delta.plot(pen='y')

win.nextRow()

plot_pump = win.addPlot(title="Pump Monitor")
curve_pump = plot_pump.plot(pen='c')

win.nextRow()

plot_corr = win.addPlot(title="Correlation")
scatter = pg.ScatterPlotItem(size=5)
plot_corr.addItem(scatter)