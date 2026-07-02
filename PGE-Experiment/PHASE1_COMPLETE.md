# Phase 1 Implementation - Core Infrastructure Complete ✓

## 📊 What's Been Implemented

### Advanced Configuration (`config_advanced.py`)
- ✅ NI PCI-6143 DAQ channel mapping (AI0=PD1, AI1=PD2, PFI3=chopper, PFI0=SDG)
- ✅ Thorlabs TSP01 settings (USB, baud rate, polling interval)
- ✅ SmarAct delay stage config (±20mm range, 10μm steps, speed/acceleration)
- ✅ Signal processing parameters (thresholds, noise floor, time conversion)
- ✅ FFT configuration (windowing, zero-padding)
- ✅ GUI layout and plotting settings
- ✅ All values user-adjustable from config file

### Signal Processing Modules

#### 1. **Chopper Demodulator** (`signal_processing/chopper_demodulator.py`)
- **ChopperDemodulator class**:
  - Separates samples into pump-ON (HIGH) and pump-OFF (LOW) states
  - Tracks state transitions
  - Provides statistics per state (mean, std, count)
  - Configurable detection threshold

- **BalancedDetectionProcessor class**:
  - Calculates ΔI/I₀ = [(PD1ₐ/PD1ᵦ) / (PD2ₐ/PD2ᵦ)] - 1
  - Uses two ChopperDemodulators (one per photodiode)
  - Computes SNR (signal-to-noise ratio)
  - Maintains history for statistics
  - Handles edge cases (division by zero, noise floor)

#### 2. **FFT Analyzer** (`signal_processing/fft_analyzer.py`)
- **FFTAnalyzer class**:
  - Converts delay (μm) → time (fs) → frequency (THz)
  - Applies configurable window functions (Hann, Blackman, Hamming)
  - Zero-padding for frequency resolution
  - Computes magnitude, phase, and power spectra
  - Peak detection algorithm
  - Metadata tracking (resolution, Nyquist frequency, etc.)

- **Utility functions**:
  - `convert_delay_to_time()`: μm → fs conversion
  - `convert_time_to_frequency()`: fs → THz conversion
  - `estimate_delay_resolution()`: Calculate spatial/temporal resolution

---

## 🎯 Ready for Next Steps

### Phase 1b: Hardware Controllers (Next)
- [ ] Enhanced DAQController for PCI-6143 with digital triggers
- [ ] TSP01Controller (USB communication)
- [ ] SmarActController (delay stage control)
- [ ] TriggerHandler (SDG and chopper trigger management)

### Phase 2: Experiment Control & Scanning
- [ ] DelayScanController (automated position scanning)
- [ ] Enhanced ExperimentController (orchestration)
- [ ] HDF5Manager (advanced data storage with metadata)

### Phase 3: GUI Implementation
- [ ] OscilloscopeView (real-time monitoring)
- [ ] DelayScanPanel (scan configuration)
- [ ] FFTViewer (frequency domain display)
- [ ] EnvironmentPanel (T/H monitoring)

---

## 🔧 Testing Phase 1 Signal Processing

### Test Chopper Demodulation
```python
from signal_processing import ChopperDemodulator
import numpy as np

# Create demodulator
demod = ChopperDemodulator(threshold=2.5)

# Simulate signal with chopper modulation
for i in range(200):
    signal = np.sin(2*np.pi*i/50) + 0.1*np.random.randn()
    chopper = 5.0 if (i // 50) % 2 == 0 else 1.0  # Alternating HIGH/LOW
    result = demod.process_sample(signal, chopper)
    
    if (i+1) % 50 == 0:
        print(f"Sample {i+1}: ON={demod.samples_on[-1]:.3f}, "
              f"OFF={demod.samples_off[-1]:.3f}")

stats = demod.get_statistics()
print(f"Statistics:\n{stats}")
```

### Test Balanced Detection
```python
from signal_processing import BalancedDetectionProcessor
import numpy as np

# Create processor
processor = BalancedDetectionProcessor(min_signal_threshold=0.01)

# Simulate dual-PD measurement
for i in range(500):
    pd1 = 2.0 + 0.5*np.sin(2*np.pi*i/100) + 0.05*np.random.randn()
    pd2 = 1.5 + 0.3*np.sin(2*np.pi*i/100 + 0.5) + 0.03*np.random.randn()
    chopper = 5.0 if (i // 100) % 2 == 0 else 1.0
    
    result = processor.process_sample(pd1, pd2, chopper)
    
    if result["ready"]:
        print(f"ΔI/I₀ = {result['delta_i_over_i0']:.6f}")

stats = processor.get_statistics()
print(f"Final SNR: {stats['snr']:.2f}")
```

### Test FFT Analysis
```python
from signal_processing import FFTAnalyzer
import numpy as np

# Create analyzer
fft_analyzer = FFTAnalyzer(
    delay_to_time_factor=1/0.15,
    window="hann",
    zero_pad_factor=2
)

# Simulate delay scan
delays = np.linspace(-5000, 5000, 200)  # μm
signal = np.sin(2*np.pi*delays/1000) * np.exp(-delays**2/5000**2)

# Analyze
result = fft_analyzer.analyze_delay_scan(delays, signal)

print(f"Frequency resolution: {result['metadata']['frequency_resolution']:.4f} THz")
print(f"Max frequency: {result['metadata']['max_frequency']:.4f} THz")

# Find peaks
peaks = fft_analyzer.find_peaks(result, distance=5)
print(f"Found {len(peaks['peak_frequencies'])} peaks")
for freq, mag in zip(peaks['peak_frequencies'][:5], peaks['peak_magnitudes'][:5]):
    print(f"  {freq:.4f} THz: {mag:.2f}")
```

---

## 📁 File Structure After Phase 1

```
PGE-Experiment/
├── config_advanced.py               [NEW] Advanced hardware config
├── signal_processing/
│   ├── __init__.py
│   ├── chopper_demodulator.py      [NEW] Lock-in demodulation
│   └── fft_analyzer.py              [NEW] FFT & frequency analysis
├── hardware/                         [FUTURE] Hardware drivers
├── scanning/                         [FUTURE] Scan control
├── data/                             [FUTURE] Data management
├── gui_advanced/                     [FUTURE] Enhanced GUI
└── [existing files...]
```

---

## 🚀 Next Priority

I'm ready to implement **Phase 1b: Hardware Controllers**

Which hardware driver should I tackle first?
1. **Enhanced DAQController** (PCI-6143 with digital triggers)
2. **TSP01Controller** (Thorlabs sensor communication)
3. **SmarActController** (Delay stage movement)
4. **TriggerHandler** (SDG and chopper management)

Or implement all 4 in parallel?
