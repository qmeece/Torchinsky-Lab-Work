# Photogalvanic Effect Experiment Control Software

A Python-based control and data acquisition system for pump-probe photogalvanic effect experiments with balanced detection using NI PXI-6733 hardware.

## Features

### Core Capabilities
- **Real-Time Signal Visualization**: Live plots of Channel A, Channel B, and balanced detection signal (A-B)
- **Data Logging**: HDF5-based structured data storage with metadata
- **Parameter Scanning**: Automated scanning of experiment parameters (delay, wavelength, intensity, etc.)
- **Balanced Detection**: Dual-channel input with automatic difference signal computation
- **Extensible Architecture**: Modular design for easy feature additions

### GUI Features
- **Experiment Controls**
  - Sample rate configuration (100 Hz - 250 kHz)
  - Buffer size adjustment
  - Start/Stop buttons with status feedback
  
- **Parameter Scanning**
  - Enable/disable scanning
  - Parameter selection (delay, wavelength, intensity)
  - Start, stop, step configuration
  
- **Real-Time Plots**
  - Three synchronized plots for all signals
  - Auto-scaling and zoom controls
  - ~100ms update rate

- **Information Panel**
  - Experiment status
  - Sample count tracking
  - Elapsed time display
  - Scan progress indicator

## Installation

### Prerequisites
- Python 3.8+
- Windows system with NI DAQmx runtime installed
- PXI-6733 (or compatible) NI hardware configured

### Setup

1. **Clone/extract project files**
   ```bash
   cd PGE-Experiment
   ```

2. **Install dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Configure hardware** (see Configuration section)

## Usage

### Quick Start

```bash
python main.py
```

This launches the GUI. The interface is intuitive:

1. **Configure DAQ Settings**
   - Set sample rate (typically 10 kHz for stable acquisition)
   - Set buffer size (100-1000 samples)

2. **Configure Parameter Scanning (Optional)**
   - Check "Enable Scanning"
   - Select parameter to scan
   - Set start, stop, step values

3. **Enable Data Logging** (Recommended)
   - Check "Enable Data Logging" to save data to HDF5

4. **Start Acquisition**
   - Click "Start" button
   - Monitor real-time plots
   - Watch sample counter and elapsed time

5. **Stop Experiment**
   - Click "Stop" button
   - Data is automatically saved and logging is finalized

### Data Output

Data is saved in the `data/` directory as HDF5 files with format:
```
data/YYYYMMDD_HHMMSS_experiment.h5
```

**HDF5 Structure:**
```
├── metadata/
│   ├── experiment_name
│   ├── start_time
│   ├── end_time
│   ├── total_samples
│   └── sample_rate
├── channel_a[]      # Raw channel A data (float32)
├── channel_b[]      # Raw channel B data (float32)
└── balanced[]       # Balanced signal (A-B) (float32)
```

**Reading Data (Python)**
```python
import h5py
import numpy as np

with h5py.File('data/20260606_190300_experiment.h5', 'r') as f:
    ch_a = np.array(f['channel_a'])
    ch_b = np.array(f['channel_b'])
    balanced = np.array(f['balanced'])
    metadata = dict(f['metadata'].attrs)
    print(f"Samples collected: {len(ch_a)}")
    print(f"Metadata: {metadata}")
```

## Configuration

### Hardware Configuration

Edit `config.py` to match your hardware setup:

```python
# DAQ Device Configuration
DAQ_DEVICE_NAME = "PXI-6733"
DAQ_INPUT_CHANNEL_A = "cDAQ1Mod1/ai0"    # Modify based on your chassis
DAQ_INPUT_CHANNEL_B = "cDAQ1Mod1/ai1"    # and module slot number
DAQ_OUTPUT_CHANNEL = "cDAQ1Mod1/ao0"     # For pump/probe control

# Voltage ranges
VOLTAGE_RANGE_INPUT = (-10, 10)           # ±10V for analog input
VOLTAGE_RANGE_OUTPUT = (-10, 10)          # ±10V for analog output

# Default sampling
DEFAULT_SAMPLE_RATE = 10000               # 10 kHz
DEFAULT_BUFFER_SIZE = 1000                # 1000 samples per read
```

**Finding Your Channel Names:**

1. Open NI MAX (Measurement & Automation Explorer)
2. Navigate to Devices and Interfaces → PXI-6733
3. Check the channel mappings in your chassis

### GUI Configuration

Adjust GUI appearance and behavior:

```python
# GUI Settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
PLOT_UPDATE_INTERVAL_MS = 100             # ~10 Hz update rate
DEFAULT_PLOT_WINDOW = 5000                # Display last 5000 samples
```

## Architecture

### Module Overview

| Module | Purpose |
|--------|---------|
| `main.py` | Entry point, launches GUI |
| `gui.py` | PyQt6 user interface |
| `experiment_controller.py` | Experiment orchestration & threading |
| `daq_controller.py` | NI DAQmx hardware control |
| `data_processor.py` | Signal processing & HDF5 logging |
| `config.py` | Global configuration constants |

### Threading Model

- **Main Thread**: GUI and user interaction
- **Acquisition Thread**: DAQ polling and data processing (runs in background)
- **Thread-Safe Communication**: Qt signals bridge data between threads

### Signal Flow

```
DAQ Hardware
    ↓
daq_controller.read_data() [Acquisition Thread]
    ↓
data_processor.process_sample() [Computes A-B]
    ↓
data_processor.log_sample() [Writes to HDF5]
    ↓
signal_bridge.data_ready [Qt Signal - Thread Safe]
    ↓
gui._update_display() [Main Thread]
    ↓
Plots Updated
```

## Extending the Code

### Adding a New Signal Processing Filter

1. Add method to `DataProcessor`:
   ```python
   def apply_lowpass_filter(self, cutoff_freq):
       """Apply low-pass filter to balanced signal."""
       # Implementation here
   ```

2. Call from `process_sample()` if enabled

### Adding New Scan Parameter Types

1. Edit `config.py` scan parameters section
2. Update `scan_param_combo` in `gui.py`
3. Update `ExperimentController.get_current_scan_parameter()`

### Adding Real-Time Analysis

1. Extend `DataProcessor` with analysis methods
2. Emit custom Qt signals from acquisition thread
3. Display results in GUI info panel

## Troubleshooting

### "Failed to initialize DAQ hardware"
- Check NI DAQmx Runtime installation: `nimax` command
- Verify PXI-6733 is recognized in NI MAX
- Check channel names in config.py match your hardware

### "nidaqmx module not found"
```bash
python -m pip install nidaqmx
```

### GUI not updating/frozen
- Check that DAQ reads are succeeding (check console output)
- Increase PLOT_UPDATE_INTERVAL_MS if CPU usage is high
- Reduce DEFAULT_PLOT_WINDOW for fewer points to display

### Data file not created
- Check that `data/` directory exists (auto-created on first run)
- Ensure write permissions in project directory
- Check disk space availability

### High CPU usage
- Reduce sample rate (if acquisition allows)
- Increase buffer size to reduce read frequency
- Increase plot update interval

## Performance Notes

- **PXI-6733 Specs**: 8 AI channels, 4 AO channels, 250 kS/s aggregate
- **Recommended Sample Rate**: 5-20 kHz for stable performance
- **Memory**: Typical experiment ~100 MB/minute at 10 kHz
- **File Size**: HDF5 with gzip compression reduces storage by ~50%

## Future Enhancements (Phase 2/3)

- [ ] Configuration presets and experiment templates
- [ ] Multi-dimensional parameter scanning
- [ ] Real-time Fast Fourier Transform (FFT) analysis
- [ ] Lock-in detection integration
- [ ] Data export to multiple formats (CSV, NetCDF)
- [ ] Experiment scheduling and batch processing
- [ ] Advanced signal filtering (Butterworth, Chebyshev)
- [ ] Performance profiling and optimization tools

## License

Academic research software - Torchinsky Lab

## Contact

For questions or issues, contact the lab administrator.
