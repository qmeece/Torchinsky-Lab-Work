# Quick Start Guide

## Installation (5 minutes)

1. **Install dependencies**
   ```bash
   cd PGE-Experiment
   python -m pip install -r requirements.txt
   ```

2. **[Optional] Test with demo mode**
   ```bash
   python launcher.py --demo
   ```
   This runs without hardware - great for testing the GUI!

3. **[Production] Configure hardware**
   - Edit `config.py`
   - Update `DAQ_INPUT_CHANNEL_A` and `DAQ_INPUT_CHANNEL_B` to match your setup
   - Run `nimax` to verify your PXI-6733 is recognized

## First Run

### Demo Mode (No Hardware Needed)
```bash
python launcher.py --demo
```
- Click **Start** to begin data acquisition with synthetic signals
- Observe the three plots updating in real-time
- Data is logged to `data/` folder as HDF5
- Click **Stop** to end the experiment

### Production Mode (With Hardware)
```bash
python launcher.py
# or simply
python main.py
```

## Basic Workflow

1. **Configure sampling**
   - Sample Rate: 10 kHz (typical)
   - Buffer Size: 100-1000 samples

2. **[Optional] Enable scanning**
   - Check "Enable Scanning"
   - Choose parameter (delay, wavelength, intensity)
   - Set range and step size

3. **Enable logging** ✓ (recommended)

4. **Click Start**
   - Watch real-time plots
   - Monitor sample count
   - Check elapsed time

5. **Click Stop**
   - Data automatically saved
   - Check `data/` folder for output file

## Viewing Your Data

**In Python:**
```python
import h5py
import numpy as np

# Open the HDF5 file
with h5py.File('data/20260606_190300_experiment.h5', 'r') as f:
    ch_a = f['channel_a'][:]
    ch_b = f['channel_b'][:]
    balanced = f['balanced'][:]
    
    # Plot with matplotlib
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.plot(ch_a, label='Channel A', alpha=0.7)
    plt.plot(ch_b, label='Channel B', alpha=0.7)
    plt.plot(balanced, label='Balanced (A-B)', linewidth=2)
    plt.legend()
    plt.xlabel('Sample Index')
    plt.ylabel('Voltage (V)')
    plt.title('Photogalvanic Effect Data')
    plt.show()
```

## Troubleshooting

**GUI won't start?**
```bash
# Verify dependencies
python -c "import PyQt6; import nidaqmx; print('OK')"
```

**Hardware not found?**
```bash
# Run NI Measurement & Automation Explorer
nimax
# Check device shows up and note the exact channel names
```

**Can't import nidaqmx?**
```bash
# Reinstall
python -m pip install --upgrade nidaqmx
```

## Next Steps

- Read `README.md` for detailed documentation
- Explore `config.py` to customize your setup
- Check out `experiment_controller.py` to understand the data flow
- Modify `gui.py` to add custom controls

## File Organization

```
PGE-Experiment/
├── main.py                    # Entry point
├── launcher.py                # Launcher with demo mode
├── gui.py                     # PyQt6 interface
├── experiment_controller.py   # Orchestration
├── daq_controller.py          # Hardware interface
├── data_processor.py          # Signal processing
├── demo_mode.py               # Demo/test mode
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── README.md                  # Full documentation
├── QUICK_START.md             # This file
└── data/                      # Output directory (auto-created)
    └── 20260606_190300_experiment.h5  # Example data file
```

## Questions?

- Check `README.md` for detailed info
- Review code comments in source files
- Test with `launcher.py --demo` first
