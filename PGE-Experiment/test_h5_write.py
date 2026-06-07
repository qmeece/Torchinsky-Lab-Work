"""Simple test of HDF5 writing."""

import h5py
import numpy as np
from pathlib import Path

print("Testing HDF5 write...")

Path("data").mkdir(exist_ok=True)

# Create file
with h5py.File("data/test_h5_write.h5", "w") as f:
    # Create expandable dataset
    ds = f.create_dataset("data", shape=(0,), maxshape=(None,), dtype=np.float32)
    
    # Try to write samples one by one
    for i in range(5):
        value = float(i * 1.5)
        print(f"Writing sample {i}: {value}")
        
        try:
            # Resize - note: requires a tuple for shape
            ds.resize((i + 1,))
            # Write
            ds[i] = value
            print(f"  [OK] Written")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            import traceback
            traceback.print_exc()

print("\nReading back...")
with h5py.File("data/test_h5_write.h5", "r") as f:
    ds = f["data"][:]
    print(f"Read {len(ds)} samples: {ds}")
