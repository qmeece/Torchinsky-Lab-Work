import nidaqmx
from nidaqmx.constants import AcquisitionType, Edge
import numpy as np
from collections import deque
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# ============================================================
# USER SETTINGS
# ============================================================

DEVICE = "Dev1"

# Analog Inputs
PD1 = f"{DEVICE}/ai0"
PD2 = f"{DEVICE}/ai1"
PUMP_MONITOR = f"{DEVICE}/ai2"
CHOPPER_TTL = f"/{DEVICE}/ai3"      # high=open, low=blocked

# Digital Inputs
LASER_CLOCK = f"/{DEVICE}/PFI3"      # laser sync TTL

TTL_THRESHOLD = 2.5

N_HISTORY = 5000

averaging_num = 350

# ============================================================
# DATA STORAGE
# ============================================================

delta_history = deque(maxlen=N_HISTORY)
pump_history = deque(maxlen=N_HISTORY)

on_ratios = deque(maxlen=1000)
off_ratios = deque(maxlen=1000)

# ============================================================
# PLOT SETUP
# ============================================================

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

# ============================================================
# TASK SETUP
# ============================================================

ai_task = nidaqmx.Task()

for ch in [PD1, PD2, PUMP_MONITOR, CHOPPER_TTL]:
    ai_task.ai_channels.add_ai_voltage_chan(ch)

# Clocked by laser pulse TTL
ai_task.timing.cfg_samp_clk_timing(
    rate=5000,                     # ignored when external clock used
    source=LASER_CLOCK,
    active_edge=Edge.RISING,
    sample_mode=AcquisitionType.CONTINUOUS,
    samps_per_chan=1000
)

# Read chopper state
# di_task = nidaqmx.Task()
# di_task.di_channels.add_di_chan(f"{DEVICE}/port0/line0")

ai_task.start()
# di_task.start()

# ============================================================
# PROCESSING
# ============================================================

def update():

    try:

        samples_available = ai_task.in_stream.avail_samp_per_chan

        if samples_available == 0:
            return

        data = np.array(
            ai_task.read(
                number_of_samples_per_channel=samples_available
            )
        )

        pd1 = data[1]
        pd2 = data[0]
        pump = data[2]
        chop = data[3]

        delta = []
        ons = []
        offs = []

        for i in range(len(pd1)):

            # Avoid divide-by-zero
            if (
                abs(pd1[i]) < 1e-12
                or abs(pd2[i]) < 1e-12
            ):
                continue

            ratio = (pd1[i] / pd2[i])

            chopper_state = chop[i]

            if chopper_state > TTL_THRESHOLD:
                ons.append(ratio)
            else:
                offs.append(ratio)

        for i in range(len(ons)):
            point = (ons[i]/offs[i]) - 1
            delta_history.append(point)

        # Update plots

        if len(delta_history):

            curve_delta.setData(np.array(delta_history))
            curve_pump.setData(np.array(pump_history))

            scatter.setData(
                np.array(pump_history),
                np.array(delta_history)
            )

    except Exception as e:
        print(e)

# ============================================================
# TIMER
# ============================================================

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(20)

# while True:

#     n = ai_task.in_stream.avail_samp_per_chan

#     if n > 0:

#         data = ai_task.read(
#             number_of_samples_per_channel=n
#         )

#         print(
#             np.mean(data[0]),
#             np.mean(data[1]),
#             np.mean(data[2]),
#         )

app.exec()

ai_task.close()
# di_task.close()