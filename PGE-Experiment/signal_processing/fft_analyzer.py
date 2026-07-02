"""FFT analysis for pump-probe delay scans."""

import numpy as np
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq
from typing import Tuple, Dict, Any, Optional


class FFTAnalyzer:
    """
    Performs FFT analysis on delay scan data.
    
    Converts optical delay scan (ΔI/I₀ vs. delay) to frequency domain
    via time-domain intermediate representation.
    
    Key conversions:
    - Optical delay (μm) → Time (fs)
    - Time domain (fs) → Frequency domain (THz)
    """

    def __init__(
        self,
        delay_to_time_factor: float = 1/0.15,
        window: str = "hann",
        zero_pad_factor: int = 2,
        normalize: bool = True
    ):
        """
        Initialize FFT analyzer.
        
        Args:
            delay_to_time_factor: Conversion factor from μm to fs
                                 (default: 1/0.15 for c=3e8 m/s)
            window: Window function ('hann', 'blackman', 'hamming', 'none')
            zero_pad_factor: Zero-padding multiplier (2 = double length)
            normalize: Normalize by window sum
        """
        self.delay_to_time_factor = delay_to_time_factor
        self.window_name = window
        self.zero_pad_factor = zero_pad_factor
        self.normalize = normalize

    def analyze_delay_scan(
        self,
        delay_positions: np.ndarray,
        delta_i_over_i0: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Analyze a complete delay scan using FFT.
        
        Args:
            delay_positions: Delay stage positions (μm), shape (N,)
            delta_i_over_i0: ΔI/I₀ values at each delay (unitless), shape (N,)
        
        Returns:
            Dict with:
            {
                'delay_axis': delay (μm),
                'time_axis': time (fs),
                'delta_i_over_i0': ΔI/I₀ signal,
                'frequency_axis': frequency (THz),
                'magnitude_spectrum': FFT magnitude,
                'phase_spectrum': FFT phase (rad),
                'power_spectrum': Power (magnitude squared),
                'metadata': {
                    'n_samples': N,
                    'delay_step': average step (μm),
                    'time_step': average step (fs),
                    'frequency_resolution': resolution (THz),
                    'max_frequency': Nyquist frequency (THz)
                }
            }
        """
        # Validate inputs
        if len(delay_positions) != len(delta_i_over_i0):
            raise ValueError("Delay and signal arrays must have same length")
        
        if len(delay_positions) < 2:
            raise ValueError("Need at least 2 samples for FFT")
        
        # Sort by delay position (in case not sorted)
        sort_idx = np.argsort(delay_positions)
        delay_sorted = delay_positions[sort_idx]
        signal_sorted = delta_i_over_i0[sort_idx]
        
        # Convert delay to time
        time_axis = delay_sorted * self.delay_to_time_factor
        
        # Compute sample spacing in time domain
        time_step = np.mean(np.diff(time_axis))  # fs
        delay_step = np.mean(np.diff(delay_sorted))  # μm
        
        # Apply window
        windowed_signal = self._apply_window(signal_sorted)
        
        # Zero-pad
        n_original = len(windowed_signal)
        n_padded = n_original * self.zero_pad_factor
        signal_padded = np.pad(windowed_signal, (0, n_padded - n_original), mode='constant')
        
        # Compute FFT
        fft_values = fft(signal_padded)
        magnitude_spectrum = np.abs(fft_values)
        phase_spectrum = np.angle(fft_values)
        power_spectrum = magnitude_spectrum ** 2
        
        # Frequency axis (THz)
        # Conversion: Hz = 1/T, where T is in seconds
        # 1 fs = 1e-15 s, so 1/fs = 1e15 Hz = 1 PHz
        # 1 THz = 1e12 Hz
        # frequency (THz) = frequency (Hz) / 1e12
        freq_hz = fftfreq(n_padded, d=time_step * 1e-15)  # time_step in fs, convert to s
        freq_thz = freq_hz / 1e12  # Convert Hz to THz
        
        # Nyquist frequency
        nyquist_thz = 1 / (2 * time_step * 1e-15) / 1e12
        
        return {
            "delay_axis": delay_sorted,
            "time_axis": time_axis,
            "delta_i_over_i0": signal_sorted,
            "frequency_axis": freq_thz,
            "magnitude_spectrum": magnitude_spectrum,
            "phase_spectrum": phase_spectrum,
            "power_spectrum": power_spectrum,
            "metadata": {
                "n_samples": n_original,
                "n_fft": n_padded,
                "delay_step": float(delay_step),
                "time_step": float(time_step),
                "frequency_resolution": float(np.abs(freq_thz[1] - freq_thz[0])) if len(freq_thz) > 1 else np.nan,
                "max_frequency": float(nyquist_thz),
                "window": self.window_name,
            }
        }

    def find_peaks(
        self,
        fft_result: Dict[str, Any],
        height: Optional[float] = None,
        distance: int = 1
    ) -> Dict[str, Any]:
        """
        Find peaks in the FFT magnitude spectrum.
        
        Args:
            fft_result: Output from analyze_delay_scan()
            height: Minimum peak height (absolute value)
            distance: Minimum distance between peaks (in samples)
        
        Returns:
            Dict with peak locations and properties
        """
        magnitude = fft_result["magnitude_spectrum"]
        freq_axis = fft_result["frequency_axis"]
        
        # Only look at positive frequencies
        pos_freq_idx = freq_axis >= 0
        magnitude_pos = magnitude[pos_freq_idx]
        freq_pos = freq_axis[pos_freq_idx]
        
        # Find peaks
        if height is None:
            height = np.max(magnitude_pos) * 0.1  # 10% of max
        
        peaks, properties = scipy_signal.find_peaks(
            magnitude_pos,
            height=height,
            distance=distance
        )
        
        return {
            "peak_indices": peaks,
            "peak_frequencies": freq_pos[peaks],
            "peak_magnitudes": magnitude_pos[peaks],
            "peak_heights": properties["peak_heights"],
            "threshold": height,
        }

    def _apply_window(self, signal: np.ndarray) -> np.ndarray:
        """Apply window function to signal."""
        n = len(signal)
        
        if self.window_name == "none":
            window_vals = np.ones(n)
        elif self.window_name == "hann":
            window_vals = scipy_signal.hann(n)
        elif self.window_name == "blackman":
            window_vals = scipy_signal.blackman(n)
        elif self.window_name == "hamming":
            window_vals = scipy_signal.hamming(n)
        else:
            raise ValueError(f"Unknown window: {self.window_name}")
        
        # Apply window
        windowed = signal * window_vals
        
        # Normalize if requested
        if self.normalize:
            window_sum = np.sum(window_vals)
            if window_sum > 0:
                windowed = windowed / (window_sum / n)
        
        return windowed


def convert_delay_to_time(delay_um: np.ndarray, factor: float = 1/0.15) -> np.ndarray:
    """Convert optical delay (μm) to time (fs)."""
    return delay_um * factor


def convert_time_to_frequency(time_fs: np.ndarray) -> np.ndarray:
    """Convert time (fs) to frequency (THz) via Fourier domain."""
    # This is typically done in FFT, but for reference:
    # freq (THz) = 1 / (time (fs) * 1e-3)
    return 1 / (time_fs * 1e-3)


def estimate_delay_resolution(delay_positions: np.ndarray) -> Tuple[float, float]:
    """
    Estimate spatial and temporal resolution from delay scan.
    
    Args:
        delay_positions: Delay stage positions (μm)
    
    Returns:
        (delay_resolution_um, time_resolution_fs)
    """
    delay_res = np.min(np.diff(np.sort(np.unique(delay_positions))))
    time_res = delay_res / 0.15  # μm to fs conversion
    return delay_res, time_res
