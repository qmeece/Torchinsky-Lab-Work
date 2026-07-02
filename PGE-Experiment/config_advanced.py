"""Advanced configuration for enhanced photogalvanic effect experiment."""

# ============================================================================
# NI PCI-6143 DAQ Configuration
# ============================================================================

DAQ_DEVICE_NAME = "Dev1"  # Adjust based on your NI MAX configuration

# Analog Input Channels
DAQ_AI_PD1 = f"{DAQ_DEVICE_NAME}/ai0"      # Signal photodiode (PD1)
DAQ_AI_PD2 = f"{DAQ_DEVICE_NAME}/ai1"      # Reference photodiode (PD2)

# Digital Input (Program Function Interface)
DAQ_PFI_CHOPPER = f"{DAQ_DEVICE_NAME}/PFI3"   # Chopper trigger (HIGH=light, LOW=blocked)
DAQ_PFI_SDG = f"{DAQ_DEVICE_NAME}/PFI0"       # External trigger from SDG

# Input Voltage Range
VOLTAGE_RANGE_INPUT = (-10, 10)  # ±10V

# Sampling Configuration
DEFAULT_SAMPLE_RATE = 100000     # 100 kHz - adjust based on signal bandwidth
DEFAULT_BUFFER_SIZE = 1000       # 1000 samples per DAQ read

# ============================================================================
# Signal Processing Configuration
# ============================================================================

# Chopper Demodulation
CHOPPER_DETECT_THRESHOLD = 2.5   # Voltage threshold for state detection (V)
CHOPPER_STATE_HIGH = 1            # Pump ON (light passed)
CHOPPER_STATE_LOW = 0             # Pump blocked (light blocked)

# Balanced Detection
# ΔI/I₀ = [(PD1_on / PD1_off) / (PD2_on / PD2_off)] - 1
MIN_SIGNAL_THRESHOLD = 0.01       # Minimum signal level to avoid div by zero
NOISE_FLOOR = 0.001              # Expected noise floor (for SNR calculation)

# Time Conversion (Optical Path Length to Time)
# Time (fs) = Delay (μm) × 2 / c
# = Delay (μm) / 0.15  [in femtoseconds]
SPEED_OF_LIGHT = 3e8             # m/s
DELAY_TO_TIME_FACTOR = 1 / 0.15  # Convert μm delay to fs (factor of 2 for round-trip)

# ============================================================================
# Thorlabs TSP01 Configuration (Temperature/Humidity Sensor)
# ============================================================================

TSP01_ENABLED = True
TSP01_COM_PORT = "COM3"           # Auto-detect if set to None
TSP01_BAUDRATE = 115200
TSP01_TIMEOUT = 1.0               # seconds
TSP01_POLL_INTERVAL = 1.0         # Query every 1 second

# ============================================================================
# SmarAct Delay Stage Configuration
# ============================================================================

SMARACT_ENABLED = True
SMARACT_DEVICE_ID = 2148602629    # Unique identifier for your stage
SMARACT_CHANNEL = 0               # Channel number (typically 0)

# Position Limits (micrometers)
SMARACT_RANGE_MIN = -20000        # -20 mm
SMARACT_RANGE_MAX = 20000         # +20 mm
SMARACT_STEP_MIN = 10             # 10 μm minimum step
SMARACT_STEP_DEFAULT = 50         # Default step size

# Speed & Acceleration
SMARACT_SPEED = 1000              # μm/s
SMARACT_ACCELERATION = 5000       # μm/s²

# ============================================================================
# Delay Scan Configuration
# ============================================================================

# Adjustable per scan, but here are defaults
DEFAULT_SCAN_START = -5000        # μm
DEFAULT_SCAN_STOP = 5000          # μm
DEFAULT_SCAN_STEP = 50            # μm

# Sampling during scan
DEFAULT_SAMPLES_PER_DELAY = 250   # Samples to acquire per delay position
SCAN_SETTLING_TIME = 50           # ms - wait after stage movement before acquisition

# ============================================================================
# FFT Configuration
# ============================================================================

FFT_WINDOW = "hann"               # Window function: "hann", "blackman", "hamming"
FFT_ZERO_PAD_FACTOR = 2           # Zero-padding multiplier for frequency resolution
FFT_NORMALIZE = True              # Normalize by window sum

# ============================================================================
# GUI Configuration
# ============================================================================

# Window Geometry
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

# Oscilloscope View
OSCILLOSCOPE_BUFFER_SIZE = 10000  # Samples to display
OSCILLOSCOPE_UPDATE_INTERVAL_MS = 100

# Plotting
PLOT_UPDATE_INTERVAL_MS = 100
DEFAULT_PLOT_WINDOW = 5000        # Samples for rolling buffer display

# ============================================================================
# Data Logging
# ============================================================================

LOG_DIR = "data"
DATA_FORMAT = "hdf5"  # HDF5 for complex hierarchical data

# Metadata to store
STORE_RAW_DATA = True             # Store raw PD1/PD2/chopper
STORE_PROCESSED_DATA = True       # Store demodulated ΔI/I₀
STORE_FFT_DATA = True             # Store FFT results
STORE_ENVIRONMENT = True          # Store TSP01 readings

# ============================================================================
# Performance Settings
# ============================================================================

MIN_UPDATE_RATE = 10              # Hz - minimum GUI refresh rate
MAX_BUFFER_MEMORY_MB = 100        # Limit in-memory buffer size

# Threading
ACQUISITION_THREAD_PRIORITY = "high"  # Thread priority for DAQ
FFT_PROCESSING_THRESHOLD = 100    # Samples before triggering async FFT

# ============================================================================
# Trigger Configuration
# ============================================================================

# Oscilloscope Trigger Modes
TRIGGER_MODES = ["Internal", "External (SDG)", "Chopper"]
DEFAULT_TRIGGER_MODE = "Internal"

# Trigger Settings
TRIGGER_LEVEL = 5.0               # V - default trigger level
TRIGGER_SLOPE = "rising"          # "rising" or "falling"

# ============================================================================
# Experiment Defaults
# ============================================================================

EXPERIMENT_NAME_FORMAT = "%Y%m%d_%H%M%S"  # For filename generation
AUTO_SAVE_ENABLED = True
BACKUP_INTERVAL = 300             # Save backup every 5 minutes
