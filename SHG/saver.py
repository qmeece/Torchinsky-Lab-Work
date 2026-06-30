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

        # Get date information when scan is done and attempting to save
        now = datetime.now()

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        year = now.strftime("%Y")
        full_date = now.strftime("%Y-%m-%d")

        # Takes metadata from calling the class and sorts it
        metadata = self.File.copy()
        metadata["timestamp"] = timestamp

        experiment = metadata.get("experiment", "UnknownExperiment")
        sample = metadata.get("sample", "UnknownSample")
        face = metadata.get("face", "UnknownFace")

        # Creates folder structure inside the Experiment_Data folder. It's reusable for any experiment type
        save_folder = os.path.join(
            self.base_folder,
            experiment,
            year,
            sample + face,
            full_date,
        )

        os.makedirs(save_folder, exist_ok=True)

        # Now we format the actual file names to be the experiment plus a scan number which is given in ascending order based on time
        existing_scans = glob.glob(
            os.path.join(save_folder, f"{experiment}_scan*.npz")
        )

        scan_number = len(existing_scans) + 1

        filename = os.path.join(
            save_folder,
            f"{experiment}_scan{scan_number:04d}.npz"
        )

        # Add the scan number to the metadata
        metadata["scan_number"] = scan_number

        # Save the average scan with metadata in a .npz file to the location specified
        np.savez(
            filename,
            average=pulse.average_shots,
            metadata=json.dumps(metadata)
        )

        print(f"[ScanSaver] Saved scan → {filename}")