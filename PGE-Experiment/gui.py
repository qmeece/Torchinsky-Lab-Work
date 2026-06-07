"""PyQt6 GUI for photogalvanic effect experiment."""

import sys
from datetime import datetime
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QComboBox,
    QGroupBox, QFormLayout, QCheckBox, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg

from experiment_controller import ExperimentController
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, PLOT_UPDATE_INTERVAL_MS,
    DEFAULT_SAMPLE_RATE, DEFAULT_PLOT_WINDOW, DEFAULT_SCAN_START,
    DEFAULT_SCAN_STOP, DEFAULT_SCAN_STEP
)


class SignalBridge(QObject):
    """Bridge for thread-safe Qt signals."""
    data_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    status = pyqtSignal(str)


class ExperimentGUI(QMainWindow):
    """Main GUI window for the photogalvanic effect experiment."""

    def __init__(self):
        super().__init__()
        self.controller = ExperimentController()
        self.signal_bridge = SignalBridge()

        # Connect signals
        self.signal_bridge.data_ready.connect(self._on_data_ready)
        self.signal_bridge.error.connect(self._on_error)
        self.signal_bridge.status.connect(self._on_status)

        self.controller.on_data_ready = self.signal_bridge.data_ready.emit
        self.controller.on_error = self.signal_bridge.error.emit
        self.controller.on_status = self.signal_bridge.status.emit

        # Initialize DAQ
        if not self.controller.initialize():
            print("Warning: DAQ initialization failed. Running in demo mode.")

        self.init_ui()
        self.setup_timers()

    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Photogalvanic Effect Experiment Control")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Main container
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Left panel: Controls
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, stretch=1)

        # Right panel: Plots and data
        right_layout = QVBoxLayout()
        self.plot_widget = self._create_plot_widget()
        right_layout.addWidget(self.plot_widget, stretch=2)

        info_panel = self._create_info_panel()
        right_layout.addWidget(info_panel, stretch=1)

        main_layout.addLayout(right_layout, stretch=2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _create_control_panel(self) -> QGroupBox:
        """Create the control panel group."""
        group = QGroupBox("Experiment Controls")
        layout = QFormLayout()

        # DAQ Settings
        daq_group = QGroupBox("DAQ Settings")
        daq_layout = QFormLayout()

        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(100, 250000)
        self.sample_rate_spin.setValue(DEFAULT_SAMPLE_RATE)
        self.sample_rate_spin.setSuffix(" Hz")
        daq_layout.addRow("Sample Rate:", self.sample_rate_spin)

        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(10, 10000)
        self.buffer_size_spin.setValue(100)
        self.buffer_size_spin.setSuffix(" samples")
        daq_layout.addRow("Buffer Size:", self.buffer_size_spin)

        daq_group.setLayout(daq_layout)
        layout.addRow(daq_group)

        # Parameter Scanning
        scan_group = QGroupBox("Parameter Scanning")
        scan_layout = QFormLayout()

        self.scan_enabled_check = QCheckBox("Enable Scanning")
        scan_layout.addRow(self.scan_enabled_check)

        self.scan_param_combo = QComboBox()
        self.scan_param_combo.addItems(["delay (fs)", "wavelength (nm)", "intensity (V)"])
        scan_layout.addRow("Scan Parameter:", self.scan_param_combo)

        self.scan_start_spin = QDoubleSpinBox()
        self.scan_start_spin.setRange(-10000, 10000)
        self.scan_start_spin.setValue(DEFAULT_SCAN_START)
        scan_layout.addRow("Start:", self.scan_start_spin)

        self.scan_stop_spin = QDoubleSpinBox()
        self.scan_stop_spin.setRange(-10000, 10000)
        self.scan_stop_spin.setValue(DEFAULT_SCAN_STOP)
        scan_layout.addRow("Stop:", self.scan_stop_spin)

        self.scan_step_spin = QDoubleSpinBox()
        self.scan_step_spin.setRange(0.1, 10000)
        self.scan_step_spin.setValue(DEFAULT_SCAN_STEP)
        scan_layout.addRow("Step:", self.scan_step_spin)

        scan_group.setLayout(scan_layout)
        layout.addRow(scan_group)

        # Control Buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        layout.addRow(button_layout)

        # Logging checkbox
        self.log_enabled_check = QCheckBox("Enable Data Logging")
        self.log_enabled_check.setChecked(True)
        layout.addRow(self.log_enabled_check)

        group.setLayout(layout)
        return group

    def _create_plot_widget(self) -> pg.GraphicsLayoutWidget:
        """Create pyqtgraph plot widget."""
        plot_widget = pg.GraphicsLayoutWidget()

        # Create 3 subplots: Ch A, Ch B, Balanced
        self.plot_a = plot_widget.addPlot(title="Channel A", row=0, col=0)
        self.plot_b = plot_widget.addPlot(title="Channel B", row=1, col=0)
        self.plot_balanced = plot_widget.addPlot(title="Balanced (A-B)", row=2, col=0)

        # Configure plots
        for plot in [self.plot_a, self.plot_b, self.plot_balanced]:
            plot.setLabel("bottom", "Time", units="s")
            plot.setLabel("left", "Voltage", units="V")
            plot.enableAutoRange(x=True, y=True)

        # Data line items
        self.line_a = self.plot_a.plot(pen=pg.mkPen(color='b', width=2))
        self.line_b = self.plot_b.plot(pen=pg.mkPen(color='g', width=2))
        self.line_balanced = self.plot_balanced.plot(pen=pg.mkPen(color='r', width=2))

        return plot_widget

    def _create_info_panel(self) -> QGroupBox:
        """Create information panel."""
        group = QGroupBox("Experiment Info")
        layout = QFormLayout()

        self.status_label = QLabel("Idle")
        layout.addRow("Status:", self.status_label)

        self.samples_label = QLabel("0")
        layout.addRow("Samples Collected:", self.samples_label)

        self.time_label = QLabel("00:00:00")
        layout.addRow("Elapsed Time:", self.time_label)

        self.file_label = QLabel("None")
        layout.addRow("Log File:", self.file_label)

        self.scan_progress_label = QLabel("N/A")
        layout.addRow("Scan Progress:", self.scan_progress_label)

        group.setLayout(layout)
        return group

    def setup_timers(self):
        """Setup update timers."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(PLOT_UPDATE_INTERVAL_MS)

        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self._update_elapsed_time)
        self.start_time = None

    def _on_start_clicked(self):
        """Handle start button click."""
        metadata = {
            "sample_rate": self.sample_rate_spin.value(),
            "timestamp": datetime.now().isoformat(),
        }

        if not self.controller.start_experiment(
            sample_rate=self.sample_rate_spin.value(),
            metadata=metadata,
            log_enabled=self.log_enabled_check.isChecked(),
        ):
            self._on_error("Failed to start experiment")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.start_time = datetime.now()
        self.elapsed_timer.start(1000)

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.controller.stop_experiment()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.elapsed_timer.stop()

    def _on_data_ready(self, data: dict):
        """Called when new data is available."""
        self.latest_data = data

    def _update_display(self):
        """Update plots with latest data."""
        if not hasattr(self, "latest_data"):
            return

        data = self.latest_data
        if len(data["ch_a"]) > 0:
            # Update plots
            self.line_a.setData(data["timestamp"], data["ch_a"])
            self.line_b.setData(data["timestamp"], data["ch_b"])
            self.line_balanced.setData(data["timestamp"], data["balanced"])

            # Update info
            self.samples_label.setText(str(self.controller.processor.sample_count))

    def _update_elapsed_time(self):
        """Update elapsed time display."""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _on_error(self, message: str):
        """Handle error messages."""
        print(f"✗ GUI Error: {message}")
        self.statusBar().showMessage(f"Error: {message}")

    def _on_status(self, message: str):
        """Handle status messages."""
        print(f"✓ {message}")
        self.statusBar().showMessage(message)
        self.status_label.setText(message)

    def closeEvent(self, event):
        """Clean up on window close."""
        self.controller.cleanup()
        event.accept()


def main():
    """Main entry point for the GUI."""
    app = QApplication(sys.argv)
    gui = ExperimentGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
