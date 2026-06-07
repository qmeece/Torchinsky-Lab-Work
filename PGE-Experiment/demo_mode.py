"""Demo mode for testing without NI hardware."""

import numpy as np
from typing import Optional, Tuple
import time


class DAQControllerDemo:
    """Mock DAQ controller for testing without NI hardware."""

    def __init__(self):
        self.is_running = False
        self.sample_rate = 10000
        self.buffer_size = 100
        self.time_step = 0
        self.base_freq_a = 100  # Hz
        self.base_freq_b = 105  # Hz
        self.amplitude = 0.5

    def initialize(self) -> bool:
        """Initialize (mock)."""
        print("[OK] DAQ Demo initialized (no hardware)")
        return True

    def start_acquisition(self) -> bool:
        """Start acquisition (mock)."""
        self.is_running = True
        self.time_step = 0
        print("[OK] Acquisition started (demo mode)")
        return True

    def stop_acquisition(self) -> bool:
        """Stop acquisition (mock)."""
        self.is_running = False
        print("[OK] Acquisition stopped")
        return True

    def read_data(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Generate synthetic data."""
        if not self.is_running:
            return None

        # Simulate two slightly different sinusoids
        t = self.time_step / self.sample_rate
        
        # Channel A: 100 Hz + noise
        ch_a = (
            self.amplitude * np.sin(2 * np.pi * self.base_freq_a * t)
            + 0.05 * np.random.randn()
        )
        
        # Channel B: 105 Hz + noise (phase-shifted)
        ch_b = (
            self.amplitude * np.sin(2 * np.pi * self.base_freq_b * t + np.pi/4)
            + 0.05 * np.random.randn()
        )
        
        self.time_step += 1
        return np.array([ch_a]), np.array([ch_b])

    def set_sample_rate(self, rate: float) -> bool:
        """Set sample rate."""
        self.sample_rate = rate
        print(f"[OK] Sample rate set to {rate} Hz (demo)")
        return True

    def set_buffer_size(self, size: int) -> bool:
        """Set buffer size."""
        self.buffer_size = size
        print(f"[OK] Buffer size set to {size} samples")
        return True

    def write_output(self, voltage: float) -> bool:
        """Mock write output."""
        return True

    def cleanup(self) -> None:
        """Cleanup (mock)."""
        print("[OK] DAQ demo cleaned up")


def enable_demo_mode():
    """
    Replace DAQController with demo version for testing.
    Call this BEFORE importing experiment_controller.
    """
    import sys
    import daq_controller
    
    # Replace the DAQController class with demo version
    original_daq = daq_controller.DAQController
    daq_controller.DAQController = DAQControllerDemo
    
    print("[OK] Demo mode enabled - using synthetic data")
    return original_daq
