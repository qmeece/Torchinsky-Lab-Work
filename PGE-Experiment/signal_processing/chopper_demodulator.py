"""Chopper-based lock-in demodulation for balanced detection."""

import numpy as np
from typing import Tuple, Dict, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ChopperDemodulator:
    """
    Demodulates signals using a chopper trigger (lock-in detection).
    
    Separates samples into two states based on chopper trigger:
    - State HIGH (pump on): Light passes through chopper
    - State LOW (pump off): Chopper blocks light
    
    This enables extraction of pump-probe signal by comparing
    the two measurement states.
    """

    def __init__(self, threshold: float = 2.5):
        """
        Initialize chopper demodulator.
        
        Args:
            threshold: Voltage threshold for detecting HIGH state (V)
        """
        self.threshold = threshold
        self.samples_on = deque(maxlen=10000)    # Pump ON (HIGH) samples
        self.samples_off = deque(maxlen=10000)   # Pump OFF (LOW) samples
        self.last_state = None
        self.state_transitions = 0

    def process_sample(self, signal: float, chopper_trigger: float) -> Dict[str, Any]:
        """
        Process a single sample with its chopper state.
        
        Args:
            signal: Signal value (voltage)
            chopper_trigger: Chopper trigger level (voltage)
        
        Returns:
            Dict with: {
                'state': 'HIGH' or 'LOW',
                'signal': signal value,
                'transition': bool (state changed),
                'count_on': samples in ON buffer,
                'count_off': samples in OFF buffer
            }
        """
        # Detect state
        current_state = "HIGH" if chopper_trigger >= self.threshold else "LOW"
        
        # Track transitions
        transition = (self.last_state != current_state)
        if transition and self.last_state is not None:
            self.state_transitions += 1
        
        self.last_state = current_state
        
        # Append to appropriate buffer
        if current_state == "HIGH":
            self.samples_on.append(signal)
        else:
            self.samples_off.append(signal)
        
        return {
            "state": current_state,
            "signal": signal,
            "transition": transition,
            "count_on": len(self.samples_on),
            "count_off": len(self.samples_off),
        }

    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistics of accumulated samples.
        
        Returns:
            Dict with means, stds, counts for ON/OFF states
        """
        stats = {
            "mean_on": np.mean(self.samples_on) if len(self.samples_on) > 0 else np.nan,
            "std_on": np.std(self.samples_on) if len(self.samples_on) > 1 else np.nan,
            "count_on": len(self.samples_on),
            "mean_off": np.mean(self.samples_off) if len(self.samples_off) > 0 else np.nan,
            "std_off": np.std(self.samples_off) if len(self.samples_off) > 1 else np.nan,
            "count_off": len(self.samples_off),
            "transitions": self.state_transitions,
        }
        return stats

    def reset(self):
        """Clear all accumulated samples."""
        self.samples_on.clear()
        self.samples_off.clear()
        self.last_state = None
        self.state_transitions = 0


class BalancedDetectionProcessor:
    """
    Compute normalized photovoltage (ΔI/I₀) from two photodiodes
    with pump-on and pump-off measurements via chopper demodulation.
    
    Formula:
        ΔI/I₀ = [(PD1_on / PD1_off) / (PD2_on / PD2_off)] - 1
    
    Where:
        - PD1: Signal photodiode (pump-probe overlap region)
        - PD2: Reference photodiode (no pump-probe overlap)
        - _on: Measurement when pump is active (chopper HIGH)
        - _off: Measurement when pump is blocked (chopper LOW)
    """

    def __init__(self, min_signal_threshold: float = 0.01):
        """
        Initialize balanced detection processor.
        
        Args:
            min_signal_threshold: Minimum signal level to avoid division errors
        """
        self.min_threshold = min_signal_threshold
        self.demod_pd1 = ChopperDemodulator()
        self.demod_pd2 = ChopperDemodulator()
        self.delta_i_over_i0_history = deque(maxlen=10000)

    def process_sample(
        self, 
        pd1_signal: float, 
        pd2_signal: float, 
        chopper_trigger: float
    ) -> Dict[str, Any]:
        """
        Process a single dual-photodiode measurement.
        
        Args:
            pd1_signal: Signal from PD1 (signal photodiode, V)
            pd2_signal: Signal from PD2 (reference photodiode, V)
            chopper_trigger: Chopper trigger level (V)
        
        Returns:
            Dict with demodulation state and any computed ΔI/I₀
        """
        # Demodulate each photodiode
        state_pd1 = self.demod_pd1.process_sample(pd1_signal, chopper_trigger)
        state_pd2 = self.demod_pd2.process_sample(pd2_signal, chopper_trigger)
        
        result = {
            "pd1_state": state_pd1["state"],
            "pd2_state": state_pd2["state"],
            "pd1_signal": pd1_signal,
            "pd2_signal": pd2_signal,
            "delta_i_over_i0": None,
            "ready": False,
        }
        
        # Try to compute ΔI/I₀ if we have enough ON and OFF samples
        if (len(self.demod_pd1.samples_on) > 5 and 
            len(self.demod_pd1.samples_off) > 5 and
            len(self.demod_pd2.samples_on) > 5 and 
            len(self.demod_pd2.samples_off) > 5):
            
            delta_i_over_i0 = self._compute_delta_i_over_i0()
            if delta_i_over_i0 is not None:
                result["delta_i_over_i0"] = delta_i_over_i0
                result["ready"] = True
                self.delta_i_over_i0_history.append(delta_i_over_i0)
        
        return result

    def _compute_delta_i_over_i0(self) -> float:
        """
        Compute ΔI/I₀ from current demodulated samples.
        
        Returns:
            ΔI/I₀ value or None if calculation fails
        """
        try:
            # Get means for each state and photodiode
            pd1_on = np.mean(self.demod_pd1.samples_on)
            pd1_off = np.mean(self.demod_pd1.samples_off)
            pd2_on = np.mean(self.demod_pd2.samples_on)
            pd2_off = np.mean(self.demod_pd2.samples_off)
            
            # Check for signal levels below threshold
            if (abs(pd1_off) < self.min_threshold or 
                abs(pd2_off) < self.min_threshold):
                logger.warning("Signal below threshold, skipping calculation")
                return None
            
            # ΔI/I₀ = [(PD1_on / PD1_off) / (PD2_on / PD2_off)] - 1
            ratio_pd1 = pd1_on / pd1_off
            ratio_pd2 = pd2_on / pd2_off
            delta_i_over_i0 = (ratio_pd1 / ratio_pd2) - 1.0
            
            return float(delta_i_over_i0)
        
        except (ZeroDivisionError, ValueError) as e:
            logger.error(f"Error computing ΔI/I₀: {e}")
            return None

    def get_current_value(self) -> float:
        """Get the most recent ΔI/I₀ value."""
        return self.delta_i_over_i0_history[-1] if len(self.delta_i_over_i0_history) > 0 else np.nan

    def get_mean_value(self) -> float:
        """Get mean ΔI/I₀ over all accumulated samples."""
        return np.mean(self.delta_i_over_i0_history) if len(self.delta_i_over_i0_history) > 0 else np.nan

    def get_snr(self) -> float:
        """
        Estimate signal-to-noise ratio.
        
        SNR = mean(ΔI/I₀) / std(ΔI/I₀)
        """
        if len(self.delta_i_over_i0_history) < 2:
            return np.nan
        
        mean_val = np.mean(self.delta_i_over_i0_history)
        std_val = np.std(self.delta_i_over_i0_history)
        
        if std_val < 1e-10:
            return np.inf if mean_val > 0 else np.nan
        
        return abs(mean_val) / std_val

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        history = np.array(self.delta_i_over_i0_history)
        
        return {
            "mean": np.mean(history) if len(history) > 0 else np.nan,
            "std": np.std(history) if len(history) > 1 else np.nan,
            "min": np.min(history) if len(history) > 0 else np.nan,
            "max": np.max(history) if len(history) > 0 else np.nan,
            "count": len(history),
            "snr": self.get_snr(),
            "pd1_on": np.mean(self.demod_pd1.samples_on) if len(self.demod_pd1.samples_on) > 0 else np.nan,
            "pd1_off": np.mean(self.demod_pd1.samples_off) if len(self.demod_pd1.samples_off) > 0 else np.nan,
            "pd2_on": np.mean(self.demod_pd2.samples_on) if len(self.demod_pd2.samples_on) > 0 else np.nan,
            "pd2_off": np.mean(self.demod_pd2.samples_off) if len(self.demod_pd2.samples_off) > 0 else np.nan,
        }

    def reset(self):
        """Reset all internal state."""
        self.demod_pd1.reset()
        self.demod_pd2.reset()
        self.delta_i_over_i0_history.clear()
