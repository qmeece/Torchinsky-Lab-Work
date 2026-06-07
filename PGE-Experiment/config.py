"""Configuration constants for photogalvanic effect experiment."""

# DAQ Configuration
DAQ_DEVICE_NAME = "PXI-6733"
DAQ_INPUT_CHANNEL_A = "cDAQ1Mod1/ai0"  # Adjust based on your PXI setup
DAQ_INPUT_CHANNEL_B = "cDAQ1Mod1/ai1"
DAQ_OUTPUT_CHANNEL = "cDAQ1Mod1/ao0"   # For pump/probe control

# Sampling
DEFAULT_SAMPLE_RATE = 10000  # Hz
DEFAULT_BUFFER_SIZE = 1000   # Samples
DEFAULT_PLOT_WINDOW = 5000   # Samples to display

# Signal Processing
VOLTAGE_RANGE_INPUT = (-10, 10)  # Volts for analog input
VOLTAGE_RANGE_OUTPUT = (-10, 10)  # Volts for analog output

# GUI
PLOT_UPDATE_INTERVAL_MS = 100
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800

# Data Logging
LOG_DIR = "data"
DATA_FORMAT = "hdf5"  # Options: "hdf5", "csv"

# Parameter Scanning
DEFAULT_SCAN_PARAM = "delay"  # e.g., time delay in fs
DEFAULT_SCAN_START = 0
DEFAULT_SCAN_STOP = 1000
DEFAULT_SCAN_STEP = 10
SCAN_UNITS = "fs"  # Femtoseconds or user-defined

# Performance
MIN_UPDATE_RATE = 10  # Hz, minimum GUI refresh rate
