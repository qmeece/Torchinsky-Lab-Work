import numpy as np
import json
import os
from datetime import datetime
import glob
import config

class ScanSaver:
    def __init__(self, File=config.FILE_INFO):
        self.File = File

        # Directory containing ScanSaver.py
        this_dir = os.path.dirname(os.path.abspath(__file__))

        # Parent directory
        parent_dir = os.path.dirname(this_dir)

        # Create/use experiment_data folder
        self.base_folder = os.path.join(parent_dir, "Experiment_Data")
        os.makedirs(self.base_folder, exist_ok=True)

    def save(self, pulse):

        now = datetime.now()

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        year = now.strftime("%Y")
        full_date = now.strftime("%Y-%m-%d")
        print(self.File)

        metadata = self.File.copy()
        metadata["timestamp"] = timestamp

        experiment = metadata.get("experiment", "UnknownExperiment")
        sample = metadata.get("sample", "UnknownSample")
        face = metadata.get("face", "UnknownFace")

        save_folder = os.path.join(
            self.base_folder,
            experiment,
            year,
            sample + face,
            full_date,
        )

        os.makedirs(save_folder, exist_ok=True)

        existing_scans = glob.glob(
            os.path.join(save_folder, f"{experiment}_scan*.npz")
        )

        scan_number = len(existing_scans) + 1

        filename = os.path.join(
            save_folder,
            f"{experiment}_scan{scan_number:04d}.npz"
        )

        metadata["scan_number"] = scan_number

        np.savez(
            filename,
            average=pulse.average_shots,
            metadata=json.dumps(metadata)
        )

        print(f"[ScanSaver] Saved scan → {filename}")