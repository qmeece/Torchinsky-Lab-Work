"""NI DAQmx controller for photogalvanic effect experiment."""

import nidaqmx
from nidaqmx.constants import AcquisitionType, Edge
from typing import Tuple, Optional
import numpy as np
from config import (
    DAQ_DEVICE_NAME,
    DAQ_INPUT_CHANNEL_A,
    DAQ_INPUT_CHANNEL_B,
    DAQ_OUTPUT_CHANNEL,
    VOLTAGE_RANGE_INPUT,
    VOLTAGE_RANGE_OUTPUT,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_BUFFER_SIZE,
)


class DAQController:
    """Manages NI PXI-6733 data acquisition."""

    def __init__(self):
        self.task_input = None
        self.task_output = None
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.buffer_size = DEFAULT_BUFFER_SIZE
        self.is_running = False

    def initialize(self) -> bool:
        """Initialize DAQ card and channels."""
        try:
            # Create input task for balanced detection (2 channels)
            self.task_input = nidaqmx.Task()
            self.task_input.ai_channels.add_ai_voltage_chan(
                DAQ_INPUT_CHANNEL_A,
                min_val=VOLTAGE_RANGE_INPUT[0],
                max_val=VOLTAGE_RANGE_INPUT[1],
            )
            self.task_input.ai_channels.add_ai_voltage_chan(
                DAQ_INPUT_CHANNEL_B,
                min_val=VOLTAGE_RANGE_INPUT[0],
                max_val=VOLTAGE_RANGE_INPUT[1],
            )

            # Configure timing for continuous sampling
            self.task_input.timing.cfg_samp_clk_timing(
                rate=self.sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=self.buffer_size,
            )

            # Create output task for pump/probe control (optional)
            self.task_output = nidaqmx.Task()
            self.task_output.ao_channels.add_ao_voltage_chan(
                DAQ_OUTPUT_CHANNEL,
                min_val=VOLTAGE_RANGE_OUTPUT[0],
                max_val=VOLTAGE_RANGE_OUTPUT[1],
            )

            print(f"✓ DAQ initialized: {DAQ_INPUT_CHANNEL_A}, {DAQ_INPUT_CHANNEL_B}")
            return True

        except Exception as e:
            print(f"✗ DAQ initialization failed: {e}")
            return False

    def start_acquisition(self) -> bool:
        """Start DAQ acquisition."""
        try:
            if self.task_input:
                self.task_input.start()
                self.is_running = True
                print("✓ Acquisition started")
                return True
        except Exception as e:
            print(f"✗ Failed to start acquisition: {e}")
        return False

    def stop_acquisition(self) -> bool:
        """Stop DAQ acquisition."""
        try:
            if self.task_input and self.is_running:
                self.task_input.stop()
                self.is_running = False
                print("✓ Acquisition stopped")
                return True
        except Exception as e:
            print(f"✗ Failed to stop acquisition: {e}")
        return False

    def read_data(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Read data from both channels."""
        try:
            if self.task_input and self.is_running:
                # Read 1 sample from each channel
                data = self.task_input.read(number_of_samples_per_channel=1)
                ch_a = np.array(data[0])  # Channel A
                ch_b = np.array(data[1])  # Channel B
                return ch_a, ch_b
        except Exception as e:
            print(f"✗ Read error: {e}")
        return None

    def set_sample_rate(self, rate: float) -> bool:
        """Update sample rate."""
        try:
            self.sample_rate = rate
            if self.task_input:
                self.task_input.timing.samp_clk_rate = rate
            print(f"✓ Sample rate set to {rate} Hz")
            return True
        except Exception as e:
            print(f"✗ Failed to set sample rate: {e}")
        return False

    def set_buffer_size(self, size: int) -> bool:
        """Update buffer size."""
        try:
            self.buffer_size = size
            print(f"✓ Buffer size set to {size} samples")
            return True
        except Exception as e:
            print(f"✗ Failed to set buffer size: {e}")
        return False

    def write_output(self, voltage: float) -> bool:
        """Write voltage to output channel (for pump/probe control)."""
        try:
            if self.task_output:
                self.task_output.write(voltage)
                return True
        except Exception as e:
            print(f"✗ Write output error: {e}")
        return False

    def cleanup(self) -> None:
        """Clean up DAQ resources."""
        try:
            self.stop_acquisition()
            if self.task_input:
                self.task_input.close()
            if self.task_output:
                self.task_output.close()
            print("✓ DAQ cleaned up")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")
