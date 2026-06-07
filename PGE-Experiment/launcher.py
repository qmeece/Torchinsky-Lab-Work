"""Launcher script with demo mode support."""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Photogalvanic Effect Experiment Control Software"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with synthetic data (no hardware required)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PGE Experiment v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Enable demo mode if requested
    if args.demo:
        print("=" * 60)
        print("DEMO MODE ENABLED - Using synthetic data")
        print("=" * 60)
        print("This mode generates synthetic signals for testing.")
        print("Real hardware will NOT be used.\n")
        from demo_mode import enable_demo_mode
        enable_demo_mode()
    
    # Import and run GUI
    from gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
