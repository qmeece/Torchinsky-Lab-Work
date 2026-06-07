"""Main experiment control and orchestration."""

import time
from threading import Thread, Event
from typing import Callable, Optional, Dict, Any
import numpy as np

from daq_controller import DAQController
from data_processor import DataProcessor
from config import DEFAULT_SAMPLE_RATE


class ExperimentController:
    """Orchestrates the entire experiment workflow."""

    def __init__(self):
        self.daq = DAQController()
        self.processor = DataProcessor()

        self.is_running = False
        self.stop_event = Event()
        self.acquisition_thread = None

        # Callbacks for GUI updates
        self.on_data_ready: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_status: Optional[Callable] = None

        # Scan parameters
        self.scan_enabled = False
        self.scan_param_name = "delay"
        self.scan_values = []
        self.current_scan_index = 0

    def initialize(self) -> bool:
        """Initialize DAQ hardware."""
        if not self.daq.initialize():
            if self.on_error:
                self.on_error("Failed to initialize DAQ hardware")
            return False
        return True

    def start_experiment(
        self,
        sample_rate: float = DEFAULT_SAMPLE_RATE,
        metadata: Dict[str, Any] = None,
        log_enabled: bool = True,
    ) -> bool:
        """Start the experiment and data acquisition."""
        try:
            if self.is_running:
                if self.on_error:
                    self.on_error("Experiment already running")
                return False

            # Configure DAQ
            self.daq.set_sample_rate(sample_rate)

            # Start logging
            if log_enabled:
                if not self.processor.start_logging(metadata=metadata):
                    if self.on_error:
                        self.on_error("Failed to start logging")
                    return False

            # Start DAQ acquisition
            if not self.daq.start_acquisition():
                if self.on_error:
                    self.on_error("Failed to start DAQ acquisition")
                return False

            # Start acquisition thread
            self.is_running = True
            self.stop_event.clear()
            self.acquisition_thread = Thread(target=self._acquisition_loop, daemon=False)
            self.acquisition_thread.start()

            if self.on_status:
                self.on_status("Experiment started")
            return True

        except Exception as e:
            if self.on_error:
                self.on_error(f"Start experiment error: {e}")
            self.is_running = False
            return False

    def stop_experiment(self) -> bool:
        """Stop the experiment and acquisition."""
        try:
            self.is_running = False
            self.stop_event.set()

            if self.acquisition_thread:
                self.acquisition_thread.join(timeout=5)

            self.daq.stop_acquisition()
            self.processor.stop_logging()

            if self.on_status:
                self.on_status("Experiment stopped")
            return True

        except Exception as e:
            if self.on_error:
                self.on_error(f"Stop experiment error: {e}")
            return False

    def _acquisition_loop(self) -> None:
        """Main acquisition loop (runs in separate thread)."""
        start_time = time.time()

        try:
            while not self.stop_event.is_set():
                # Read data from DAQ
                result = self.daq.read_data()
                if result is None:
                    continue

                ch_a, ch_b = result
                timestamp = time.time() - start_time

                # Process sample
                processed = self.processor.process_sample(ch_a[0], ch_b[0], timestamp)

                # Log to file
                self.processor.log_sample(
                    processed["ch_a"], processed["ch_b"], processed["balanced"]
                )

                # Notify GUI (throttled to ~100ms)
                if self.processor.sample_count % 100 == 0:
                    if self.on_data_ready:
                        display_data = self.processor.get_display_data()
                        self.on_data_ready(display_data)

                time.sleep(0.001)  # Small delay to prevent CPU spinning

        except Exception as e:
            if self.on_error:
                self.on_error(f"Acquisition loop error: {e}")
        finally:
            self.is_running = False

    def setup_parameter_scan(
        self, param_name: str, start: float, stop: float, step: float
    ) -> None:
        """Configure parameter scanning."""
        self.scan_param_name = param_name
        self.scan_values = np.arange(start, stop + step, step)
        self.scan_enabled = len(self.scan_values) > 0
        self.current_scan_index = 0

        if self.on_status:
            self.on_status(
                f"Scan configured: {param_name} from {start} to {stop} step {step}"
            )

    def get_current_scan_parameter(self) -> Optional[Dict[str, Any]]:
        """Get current scan parameter value."""
        if not self.scan_enabled or self.current_scan_index >= len(self.scan_values):
            return None

        return {
            "name": self.scan_param_name,
            "value": self.scan_values[self.current_scan_index],
            "index": self.current_scan_index,
            "total": len(self.scan_values),
        }

    def advance_scan(self) -> bool:
        """Move to next scan parameter."""
        if self.scan_enabled:
            self.current_scan_index += 1
            return self.current_scan_index < len(self.scan_values)
        return False

    def reset(self) -> None:
        """Reset experiment state."""
        self.processor.reset()
        self.current_scan_index = 0

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.stop_experiment()
        self.daq.cleanup()
