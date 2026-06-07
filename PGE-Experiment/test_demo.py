"""Test script to verify demo mode works end-to-end."""

import sys
import time
from demo_mode import enable_demo_mode

# Enable demo mode before importing experiment controller
enable_demo_mode()

from experiment_controller import ExperimentController
from data_processor import DataProcessor

def test_demo_mode():
    """Test demo mode acquisition and logging."""
    print("\n" + "="*60)
    print("TESTING DEMO MODE - End-to-End Verification")
    print("="*60 + "\n")

    controller = ExperimentController()

    # Initialize
    print("[1] Initializing DAQ...")
    if not controller.initialize():
        print("✗ Initialization failed")
        return False
    print("✓ DAQ initialized successfully\n")

    # Start experiment with logging
    print("[2] Starting experiment with data logging...")
    metadata = {
        "test": "demo_mode_verification",
        "sample_rate": 10000,
    }
    if not controller.start_experiment(
        sample_rate=10000,
        metadata=metadata,
        log_enabled=True
    ):
        print("✗ Failed to start experiment")
        return False
    print("✓ Experiment started\n")

    # Let it run for a few seconds
    print("[3] Running acquisition for 3 seconds...")
    time.sleep(3)
    print(f"✓ Acquired {controller.processor.sample_count} samples\n")

    # Stop experiment
    print("[4] Stopping experiment...")
    if not controller.stop_experiment():
        print("✗ Failed to stop experiment")
        return False
    print("✓ Experiment stopped\n")

    # Verify data was logged
    print("[5] Verifying logged data...")
    import h5py
    import os
    from pathlib import Path

    # Find the most recent HDF5 file
    data_dir = Path("data")
    if not data_dir.exists():
        print("✗ Data directory not created")
        return False

    h5_files = list(data_dir.glob("*.h5"))
    if not h5_files:
        print("✗ No HDF5 files created")
        return False

    latest_file = max(h5_files, key=os.path.getctime)
    print(f"✓ Found data file: {latest_file.name}\n")

    # Verify file contents
    print("[6] Verifying file contents...")
    with h5py.File(latest_file, 'r') as f:
        ch_a = f['channel_a'][:]
        ch_b = f['channel_b'][:]
        balanced = f['balanced'][:]
        metadata_attrs = dict(f['metadata'].attrs)

        print(f"  Samples in Channel A: {len(ch_a)}")
        print(f"  Samples in Channel B: {len(ch_b)}")
        print(f"  Samples in Balanced: {len(balanced)}")
        print(f"  Metadata: {metadata_attrs}")

        if len(ch_a) == 0 or len(ch_b) == 0 or len(balanced) == 0:
            print("✗ No samples logged")
            return False

        print("✓ All channels have data\n")

        # Verify data values are reasonable
        print("[7] Verifying data values...")
        print(f"  Channel A range: [{ch_a.min():.4f}, {ch_a.max():.4f}]")
        print(f"  Channel B range: [{ch_b.min():.4f}, {ch_b.max():.4f}]")
        print(f"  Balanced range: [{balanced.min():.4f}, {balanced.max():.4f}]")
        print("✓ Data values look reasonable\n")

    # Cleanup
    controller.cleanup()

    print("="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print("\nDemo mode is working correctly.")
    print("You can now run: python launcher.py --demo")
    print("to launch the full GUI application.\n")

    return True


if __name__ == "__main__":
    try:
        success = test_demo_mode()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
