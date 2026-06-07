# Installation & Getting Started

## ✓ Installation Complete

All files are ready in: `c:\Users\quinn\OneDrive\Documents\Torchinsky Lab Work\PGE-Experiment\`

### Dependencies Installed ✓
- PyQt6 6.11.0 (GUI framework)
- nidaqmx 1.5.0 (NI hardware control)
- h5py 3.16.0 (HDF5 data storage)
- pyqtgraph 0.13.0+ (real-time plotting)
- numpy 1.21.0+ (numerical processing)

---

## 🚀 Quick Test (Demo Mode - No Hardware Needed)

Run this to verify everything works:

```bash
cd "c:\Users\quinn\OneDrive\Documents\Torchinsky Lab Work\PGE-Experiment"
python launcher.py --demo
```

**What happens:**
1. GUI window opens
2. Three plots display synthetic signals
3. Click "Start" button
4. Watch signals update in real-time
5. Click "Stop" button
6. Data saved to `data/` folder as HDF5 file

---

## 🔧 Production Setup (With Your PXI-6733)

### Step 1: Configure Hardware
Edit `config.py` and update the channel names:

```python
DAQ_INPUT_CHANNEL_A = "cDAQ1Mod1/ai0"    # Your first input
DAQ_INPUT_CHANNEL_B = "cDAQ1Mod1/ai1"    # Your second input
DAQ_OUTPUT_CHANNEL = "cDAQ1Mod1/ao0"     # Optional pump control
```

**How to find your channel names:**
1. Open NI MAX: Press Windows key, search "MAX"
2. Navigate to "Devices and Interfaces" → Your PXI system
3. Note the exact channel names (case-sensitive!)

### Step 2: Run With Hardware
```bash
python launcher.py
# or simply
python main.py
```

### Step 3: Configure Experiment
In the GUI:
- **Sample Rate**: 10 kHz (typical start)
- **Buffer Size**: 100-1000 samples
- **Enable Logging**: ✓ Recommended
- Optional: Enable Parameter Scanning

### Step 4: Start Acquisition
1. Click "Start" button
2. Real-time plots show Channels A, B, and Balanced (A-B)
3. Monitor sample count and elapsed time
4. Click "Stop" when done
5. Data automatically saved to `data/` folder

---

## 📊 Accessing Your Data

### View in Python
```python
import h5py
import matplotlib.pyplot as plt
import numpy as np

# Open your data file
filepath = "data/20260606_190300_experiment.h5"  # Update date/time
with h5py.File(filepath, 'r') as f:
    ch_a = f['channel_a'][:]
    ch_b = f['channel_b'][:]
    balanced = f['balanced'][:]
    
    # Quick plot
    plt.figure(figsize=(12, 6))
    time = np.arange(len(ch_a)) / 10000  # Assuming 10 kHz sample rate
    plt.plot(time, ch_a, label='Channel A', alpha=0.7)
    plt.plot(time, ch_b, label='Channel B', alpha=0.7)
    plt.plot(time, balanced, label='Balanced (A-B)', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.grid()
    plt.show()
```

### View File Info
```python
import h5py

with h5py.File("data/20260606_190300_experiment.h5", 'r') as f:
    print("Datasets:", list(f.keys()))
    print("Metadata:", dict(f['metadata'].attrs))
    print("Total samples:", len(f['channel_a']))
```

---

## 🎯 Key Capabilities

| Feature | Status | Description |
|---------|--------|-------------|
| Real-Time Plotting | ✓ Ready | Live 3-channel display with auto-scaling |
| Balanced Detection | ✓ Ready | Automatic A-B difference calculation |
| Data Logging | ✓ Ready | HDF5 format with metadata |
| Parameter Scanning | ✓ Ready | Configurable scan loops |
| Demo Mode | ✓ Ready | Test without hardware |
| Threading | ✓ Ready | Non-blocking GUI during acquisition |
| Error Handling | ✓ Ready | Graceful failure recovery |

---

## 📁 File Organization

```
PGE-Experiment/
├── main.py                  ← Direct launcher
├── launcher.py              ← Launcher with --demo flag
├── gui.py                   ← PyQt6 user interface
├── experiment_controller.py ← Orchestration engine
├── daq_controller.py        ← Hardware interface (PXI-6733)
├── data_processor.py        ← Signal processing & HDF5 logging
├── demo_mode.py             ← Mock DAQ for testing
├── config.py                ← Configuration (edit for your hardware!)
├── requirements.txt         ← Dependencies (already installed)
├── README.md                ← Full documentation
├── QUICK_START.md           ← Quick reference guide
├── DELIVERY_SUMMARY.md      ← Project summary
└── data/                    ← Output folder (auto-created)
    └── 20260606_190300_experiment.h5  ← Example data file
```

---

## 🔨 Customization Tips

### Change GUI Layout
Edit `_create_control_panel()` in `gui.py`

### Add New Signal Processing
Add methods to `DataProcessor` class in `data_processor.py`

### Add New Parameters to Scan
Update `config.py` scan parameters section and `gui.py` combobox

### Modify Sample Rate
Edit `DEFAULT_SAMPLE_RATE` in `config.py` (10,000 = 10 kHz)

---

## ❓ Troubleshooting

**Problem**: GUI won't start  
**Solution**: Run `python -c "import PyQt6; import nidaqmx; print('OK')"`

**Problem**: "DAQ initialization failed"  
**Solution**: Check channel names in config.py match NI MAX exactly

**Problem**: Plots not updating  
**Solution**: Verify DAQ reads are working (check console output)

**Problem**: No data file created  
**Solution**: Check `data/` folder exists and is writable

**For more help**: Read README.md (full documentation)

---

## 📞 Next Steps

1. **Test demo mode first**: `python launcher.py --demo`
2. **Configure hardware**: Edit `config.py` with your channel names
3. **Run with hardware**: `python launcher.py`
4. **Read full docs**: Open `README.md` in your text editor
5. **Customize**: Modify code to fit your experiment needs

---

## ✨ What's Included

✓ Production-quality Python code (1000+ lines)  
✓ Complete PyQt6 GUI application  
✓ Real-time signal processing engine  
✓ HDF5 data storage with metadata  
✓ Threading for responsive UI  
✓ Demo mode for testing  
✓ Comprehensive documentation  
✓ Error handling & logging  

**Everything is ready to use!**
