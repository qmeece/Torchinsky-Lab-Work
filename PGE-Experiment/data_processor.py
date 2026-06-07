"""Data processing and logging for photogalvanic effect experiment."""

import h5py
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from config import LOG_DIR, DEFAULT_PLOT_WINDOW


class DataProcessor:
    """Handles signal processing and data logging."""

    def __init__(self):
        self.ch_a_buffer = []
        self.ch_b_buffer = []
        self.balanced_buffer = []
        self.timestamp_buffer = []
        self.max_buffer_size = DEFAULT_PLOT_WINDOW

        self.h5_file = None
        self.h5_dataset_ch_a = None
        self.h5_dataset_ch_b = None
        self.h5_dataset_balanced = None
        self.h5_metadata = None

        self.sample_count = 0
        self.logged_count = 0
        self.start_time = None

    def process_sample(
        self, ch_a: float, ch_b: float, timestamp: float
    ) -> Dict[str, float]:
        """Process a single sample and compute balanced signal."""
        balanced = ch_a - ch_b

        # Append to rolling buffer for display
        self.ch_a_buffer.append(ch_a)
        self.ch_b_buffer.append(ch_b)
        self.balanced_buffer.append(balanced)
        self.timestamp_buffer.append(timestamp)

        # Limit buffer size for plotting
        if len(self.ch_a_buffer) > self.max_buffer_size:
            self.ch_a_buffer.pop(0)
            self.ch_b_buffer.pop(0)
            self.balanced_buffer.pop(0)
            self.timestamp_buffer.pop(0)

        self.sample_count += 1

        return {
            "ch_a": ch_a,
            "ch_b": ch_b,
            "balanced": balanced,
            "timestamp": timestamp,
        }

    def get_display_data(self) -> Dict[str, np.ndarray]:
        """Get current buffered data for plotting."""
        return {
            "ch_a": np.array(self.ch_a_buffer),
            "ch_b": np.array(self.ch_b_buffer),
            "balanced": np.array(self.balanced_buffer),
            "timestamp": np.array(self.timestamp_buffer),
        }

    def start_logging(
        self, experiment_name: str = None, metadata: Dict[str, Any] = None
    ) -> bool:
        """Initialize HDF5 file for data logging."""
        try:
            Path(LOG_DIR).mkdir(exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if experiment_name is None:
                experiment_name = "experiment"
            filename = f"{LOG_DIR}/{timestamp}_{experiment_name}.h5"

            # Create HDF5 file
            self.h5_file = h5py.File(filename, "w")

            # Store metadata
            if metadata:
                self.h5_metadata = self.h5_file.create_group("metadata")
                for key, value in metadata.items():
                    self.h5_metadata.attrs[key] = str(value)
                self.h5_metadata.attrs["experiment_name"] = experiment_name
                self.h5_metadata.attrs["start_time"] = timestamp

            # Create datasets (expandable)
            self.h5_dataset_ch_a = self.h5_file.create_dataset(
                "channel_a",
                shape=(0,),
                maxshape=(None,),
                dtype=np.float32,
                compression="gzip",
            )
            self.h5_dataset_ch_b = self.h5_file.create_dataset(
                "channel_b",
                shape=(0,),
                maxshape=(None,),
                dtype=np.float32,
                compression="gzip",
            )
            self.h5_dataset_balanced = self.h5_file.create_dataset(
                "balanced",
                shape=(0,),
                maxshape=(None,),
                dtype=np.float32,
                compression="gzip",
            )

            self.start_time = datetime.now()
            print(f"✓ Logging started: {filename}")
            return True

        except Exception as e:
            print(f"✗ Failed to start logging: {e}")
            return False

    def log_sample(self, ch_a: float, ch_b: float, balanced: float) -> bool:
        """Append sample to HDF5 file."""
        try:
            if self.h5_file is None:
                return False

            # Expand datasets and append data
            # Note: resize() requires a tuple for shape
            self.h5_dataset_ch_a.resize((self.logged_count + 1,))
            self.h5_dataset_ch_b.resize((self.logged_count + 1,))
            self.h5_dataset_balanced.resize((self.logged_count + 1,))

            # Ensure values are floats
            self.h5_dataset_ch_a[self.logged_count] = float(ch_a)
            self.h5_dataset_ch_b[self.logged_count] = float(ch_b)
            self.h5_dataset_balanced[self.logged_count] = float(balanced)

            self.logged_count += 1

            # Periodic flush for safety
            if self.logged_count % 1000 == 0:
                self.h5_file.flush()

            return True

        except Exception as e:
            print(f"[FAIL] Logging error: {e}")
            return False

    def stop_logging(self) -> bool:
        """Close HDF5 file and finalize logging."""
        try:
            if self.h5_file:
                if self.h5_metadata:
                    self.h5_metadata.attrs["end_time"] = datetime.now().isoformat()
                    self.h5_metadata.attrs["total_samples"] = self.logged_count

                self.h5_file.close()
                self.h5_file = None
                print(f"✓ Logging stopped. Total samples logged: {self.logged_count}")
                return True
        except Exception as e:
            print(f"✗ Failed to stop logging: {e}")
        return False

    def reset(self) -> None:
        """Reset buffers and counters."""
        self.ch_a_buffer.clear()
        self.ch_b_buffer.clear()
        self.balanced_buffer.clear()
        self.timestamp_buffer.clear()
        self.sample_count = 0
        self.logged_count = 0
        self.start_time = None
