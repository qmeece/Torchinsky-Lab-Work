import numpy as np
import json
import os
from datetime import datetime


class ScanSaver:
    def __init__(self, folder="scans"):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)

    def save(self, pulse):
        """
        Save final results from a PulseData object.
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = os.path.join(
            self.folder,
            f"scan_{timestamp}.npz"
        )

        metadata = {
            "timestamp": timestamp,
            "samples_per_channel": pulse.samples_per_channel,
            "averages": pulse.averages,
            "sample_rate": pulse.sample_rate,
            "PMT_channel": pulse.PMT_channel,
            "counter_channel": pulse.counter_channel,
        }

        np.savez(
            filename,
            average=pulse.average_shots,
            single=pulse.single_shot,
            metadata=json.dumps(metadata)
        )

        print(f"[ScanSaver] Saved scan → {filename}")