"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ULTRAFAST LASER PULSE NOISE TRACKER — NI DAQ 6143                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Continuous-acquisition design for 5 kHz (or higher) laser rep-rates.

The NI PCI-6143 does NOT support:
  • RSE / NRSE terminal configuration  (DIFF only)
  • DAQmx_StartTrig_Retriggerable      (no hardware retrigger)

Strategy
────────
  • Run one CONTINUOUS analog input task at 1 MS/s.
  • Poll the DAQ buffer every ~10 ms, pulling 10 000 samples per chunk.
  • Detect pulses via threshold crossing in Python/NumPy — zero dead time.
  • Extract peak amplitude of each pulse → per-pulse noise statistics.

At 1 MS/s / 5 kHz = 200 samples per pulse period, so each ~ns–µs pulse is
captured with many points.  Adjust threshold_volts to sit between baseline
noise and the pulse foot.

──────────────────────────────────────────────────────────────────────────────
HARDWARE WIRING  (NI PCI-6143 with BNC-2110 / BNC-2090A breakout)
──────────────────────────────────────────────────────────────────────────────
  DIFFERENTIAL mode (only mode supported):

  ai0  →  AI0+  pin 68  /  AI0−  pin 34
  ai1  →  AI1+  pin 33  /  AI1−  pin 66
  ai2  →  AI2+  pin 65  /  AI2−  pin 31
  ai3  →  AI3+  pin 64  /  AI3−  pin 30
  (see 6143 User Manual Table 1 for all channels)

  Connect: photodiode signal → AIx+,  photodiode GND → AIx−
  Shield / case → AIGND (pin 32 or 67)

──────────────────────────────────────────────────────────────────────────────
DEPENDENCIES
──────────────────────────────────────────────────────────────────────────────
  pip install nidaqmx numpy matplotlib scipy

  NI-DAQmx driver:
    https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html

──────────────────────────────────────────────────────────────────────────────
QUICK START
──────────────────────────────────────────────────────────────────────────────
  1. Set ai_channel, v_min/v_max, threshold_volts in Config below.
  2. python laser_noise_tracker.py
  3. Without nidaqmx installed the program auto-runs in SIMULATION mode.
"""

from __future__ import annotations

import csv
import queue
import threading
import time
import collections
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, List

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.animation as animation
from matplotlib.ticker import AutoMinorLocator
from scipy import stats

try:
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration
    from nidaqmx.errors import DaqReadError
    HW_AVAILABLE = True
except ImportError:
    HW_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG  ← edit this block
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    # ── NI device ──────────────────────────────────────────────────────────
    device:          str   = "Dev1"
    ai_channel:      str   = "ai2"        # change to match your wiring

    v_min:           float = -1.0         # ADC range min (V)
    v_max:           float =  1.0         # ADC range max (V)

    # ── Sample rate ────────────────────────────────────────────────────────
    # NI 6143 inter-channel ADC conversion minimum period is ~800 ns.
    # DAQmx overhead means -200019 fires above ~500 kS/s on many systems.
    # For a 5 kHz laser:
    #
    #   200 kS/s  →  40 samples per pulse period  ← safe default
    #   500 kS/s  → 100 samples per pulse period  ← try if you need finer
    #                                                 pulse shape resolution
    #
    # If -200019 persists at 200 kS/s, drop to 100 kS/s.
    sample_rate:     int   = 200_000      # Hz

    # Samples per polling call.
    # 200 kS/s / 5 kHz = 40 samp/period → 2000 samples ≈ 50 pulses per read.
    read_chunk:      int   = 2_000

    # ── Pulse detection ────────────────────────────────────────────────────
    # Set threshold_volts to ~40 % of your expected pulse peak.
    # Run quick_check() at the bottom of this file first if unsure.
    threshold_volts: float = 0.02         # V  ← TUNE THIS

    # Pulse width bounds in samples at sample_rate.
    # 200 kS/s / 5 kHz = 40 samp/period; typical photodiode pulse << period.
    pulse_min_samp:  int   = 1            # reject single-sample spikes
    pulse_max_samp:  int   = 35           # reject long baseline excursions

    # How to represent each pulse: "peak" | "mean" | "integral"
    pulse_metric:    str   = "mean"

    # ── Statistics & display ───────────────────────────────────────────────
    display_window:  int   = 2000         # pulses on rolling plots
    stats_window:    int   = 200          # pulses for rolling statistics
    mean_stride:     int   = 25           # plot one mean point every N pulses
    alarm_rms_pct:   float = 2.0          # alarm threshold (% RMS noise)

    # ── CSV logging ────────────────────────────────────────────────────────
    log_to_csv:      bool  = True
    log_path:        str   = "laser_noise_log.csv"

    # ── Simulation ─────────────────────────────────────────────────────────
    sim_rep_rate:    int   = 5000         # Hz — matches real laser
    sim_voltage:     float = 0.5          # V mean amplitude
    sim_noise_frac:  float = 0.008        # fractional RMS noise (~0.8 %)
    sim_pulse_width: int   = 4            # samples (at 200 kS/s ≈ 20 µs pulse)
    sim_drift_tau:   float = 5000         # Ornstein-Uhlenbeck correlation


CFG = Config()


# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PulseMeasurement:
    index:     int
    timestamp: float    # time.perf_counter()
    voltage:   float    # peak / mean / integral amplitude


@dataclass
class RollingStats:
    mean:         float = 0.0
    std:          float = 0.0
    rms_noise:    float = 0.0   # std / |mean| × 100 (%)
    rms_abs:      float = 0.0
    peak_to_peak: float = 0.0
    n:            int   = 0


_pulse_queue: "queue.Queue[PulseMeasurement]" = queue.Queue(maxsize=200_000)
_stop = threading.Event()


# ══════════════════════════════════════════════════════════════════════════════
# PULSE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_pulses(
    chunk:     np.ndarray,
    leftover:  np.ndarray,
    threshold: float,
    min_samp:  int,
    max_samp:  int,
    metric:    str,
) -> tuple[list[float], np.ndarray]:
    """
    Find above-threshold regions in `chunk`, prepended with any `leftover`
    samples carried from the previous call (handles pulses that straddle
    a chunk boundary).

    Strategy: build a boolean mask, prepend/append a guaranteed False so
    np.diff always sees both edges even when the signal starts or ends
    above threshold.  All indices are in buf-space with no offset arithmetic.

    Returns
    -------
    amplitudes   : one float per complete detected pulse
    new_leftover : tail of buf if a pulse is open at the end of the buffer,
                   otherwise an empty array
    """
    buf = np.concatenate((leftover, chunk)) if leftover.size else chunk.copy()

    if buf.size == 0:
        return [], np.array([], dtype=np.float64)

    # Boolean mask: True where signal is above threshold
    above = buf >= threshold

    # Wrap with False so diff always sees a clean 0→1 and 1→0 transition
    # even when the first or last sample is above threshold.
    wrapped = np.empty(buf.size + 2, dtype=bool)
    wrapped[0]    = False
    wrapped[-1]   = False
    wrapped[1:-1] = above

    diff = np.diff(wrapped.view(np.int8))   # +1 = rising, -1 = falling

    # Indices into `buf`: rising edge = first above-threshold sample
    rising  = np.where(diff ==  1)[0]   # wrapped[i]→wrapped[i+1]: 0→1, buf idx = i
    falling = np.where(diff == -1)[0]   # wrapped[i]→wrapped[i+1]: 1→0, buf idx = i

    # Verify: rising[k] is the buf index of the FIRST above-threshold sample.
    # falling[k] is the buf index of the FIRST below-threshold sample after
    # a rising edge (exclusive end).  Width = falling[k] - rising[k].

    amplitudes: list[float] = []

    for start in rising:
        # Find the closing edge strictly after this opening
        ends = falling[falling > start]

        if ends.size == 0:
            # Pulse extends to end of buffer — carry it into next call
            return amplitudes, buf[start:]

        end   = int(ends[0])          # exclusive: buf[start:end] is the pulse
        width = end - start

        if width < min_samp or width > max_samp:
            continue

        segment = buf[start:end]      # always non-empty: width >= min_samp >= 1

        if metric == "peak":
            amp = float(segment.max())
        elif metric == "mean":
            amp = float(segment.mean())
        else:                         # "integral"
            amp = float(segment.sum()) / CFG.sample_rate

        amplitudes.append(amp)

    return amplitudes, np.array([], dtype=np.float64)


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def compute_stats(arr: np.ndarray) -> RollingStats:
    n = len(arr)
    if n < 2:
        return RollingStats(n=n)
    mean  = float(np.mean(arr))
    std   = float(np.std(arr, ddof=1))
    rms_a = float(np.sqrt(np.mean(arr ** 2)))
    rms_n = (std / abs(mean) * 100.0) if mean != 0 else 0.0
    p2p   = float(arr.max() - arr.min())
    return RollingStats(mean=mean, std=std, rms_noise=rms_n,
                        rms_abs=rms_a, peak_to_peak=p2p, n=n)


# ══════════════════════════════════════════════════════════════════════════════
# ACQUISITION — REAL HARDWARE  (continuous, no trigger, no retrigger)
# ══════════════════════════════════════════════════════════════════════════════

def _acquire_hardware() -> None:
    """
    Continuous analog input at sample_rate.
    Pulses are detected in software via threshold crossing on each chunk.

    No digital trigger is used — the DAQ free-runs and every pulse is
    captured as long as the polling interval << pulse period.
    """
    ch = f"{CFG.device}/{CFG.ai_channel}"
    samps_per_period = CFG.sample_rate / CFG.sim_rep_rate  # informational
    print(f"[DAQ] Channel        : {ch}  [{CFG.v_min}, {CFG.v_max}] V  DIFF")
    print(f"[DAQ] Sample rate    : {CFG.sample_rate/1e6:.2f} MS/s")
    print(f"[DAQ] Read chunk     : {CFG.read_chunk} samples  "
          f"({CFG.read_chunk/CFG.sample_rate*1e3:.1f} ms)")
    print(f"[DAQ] Pulse threshold: {CFG.threshold_volts:.3f} V")
    print(f"[DAQ] Pulse width    : {CFG.pulse_min_samp}–{CFG.pulse_max_samp} samples")

    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(
            ch,
            terminal_config=TerminalConfiguration.DIFF,
            min_val=CFG.v_min,
            max_val=CFG.v_max,
        )
        # samps_per_chan sets the onboard hardware FIFO / DMA buffer size.
        # Keep it large (≥ 1 s worth) so a slow Python poll never causes
        # a buffer-overflow error (-200279).
        hw_buf = max(CFG.read_chunk * 100, CFG.sample_rate)
        task.timing.cfg_samp_clk_timing(
            rate=CFG.sample_rate,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=hw_buf,
        )
        task.start()
        print("[DAQ] Running — detecting pulses by threshold …")

        pulse_idx = 0
        leftover  = np.array([], dtype=np.float64)

        while not _stop.is_set():
            try:
                raw = task.read(
                    number_of_samples_per_channel=CFG.read_chunk,
                    timeout=2.0,
                )
                chunk = np.asarray(raw, dtype=np.float64)

                amps, leftover = detect_pulses(
                    chunk, leftover,
                    CFG.threshold_volts,
                    CFG.pulse_min_samp,
                    CFG.pulse_max_samp,
                    CFG.pulse_metric,
                )

                t_now = time.perf_counter()
                for amp in amps:
                    pulse_idx += 1
                    _pulse_queue.put_nowait(
                        PulseMeasurement(pulse_idx, t_now, amp)
                    )

            except DaqReadError as exc:
                if _stop.is_set():
                    break
                print(f"[DAQ] Read error: {exc}")
                time.sleep(0.01)

    print("[DAQ] Task closed.")


# ══════════════════════════════════════════════════════════════════════════════
# ACQUISITION — SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def _acquire_simulation() -> None:
    """
    Generates a synthetic continuous waveform at sample_rate containing
    Gaussian pulses at sim_rep_rate with shot noise + drift, then feeds it
    through the same detect_pulses() path as real hardware.
    """
    sr       = CFG.sample_rate
    chunk_n  = CFG.read_chunk
    interval = chunk_n / sr           # real-time interval per chunk

    rng   = np.random.default_rng(0)
    drift = 0.0
    alpha = 1.0 - 1.0 / CFG.sim_drift_tau

    # Phase accumulator — fractional sample position of next pulse
    phase = 0.0
    spp   = sr / CFG.sim_rep_rate     # samples per pulse period

    print(f"[SIM] {CFG.sim_rep_rate} Hz  noise={CFG.sim_noise_frac*100:.1f}%  "
          f"drift_tau={CFG.sim_drift_tau}  chunk={chunk_n}")

    pulse_idx = 0
    leftover  = np.array([], dtype=np.float64)

    while not _stop.is_set():
        t0 = time.perf_counter()

        # Build waveform chunk
        waveform = np.zeros(chunk_n, dtype=np.float64)

        # Place pulses at regular intervals (with sub-sample jitter)
        pos = phase
        while pos < chunk_n:
            i = int(pos)
            if 0 <= i < chunk_n:
                # Ornstein-Uhlenbeck drift
                drift = (alpha * drift
                         + np.sqrt(1 - alpha**2)
                         * rng.standard_normal()
                         * CFG.sim_noise_frac * CFG.sim_voltage * 0.5)
                amp = (CFG.sim_voltage + drift
                       + rng.normal(0, CFG.sim_noise_frac * CFG.sim_voltage))
                # Gaussian pulse shape, width = sim_pulse_width samples
                w = CFG.sim_pulse_width
                xs = np.arange(max(0, i - w * 2), min(chunk_n, i + w * 2))
                waveform[xs] += amp * np.exp(-0.5 * ((xs - pos) / (w / 2.5)) ** 2)
            pos += spp

        # Carry-over phase for next chunk
        phase = pos - chunk_n

        # Add broadband baseline noise
        waveform += rng.normal(0, CFG.sim_noise_frac * CFG.sim_voltage * 0.1,
                               size=chunk_n)

        amps, leftover = detect_pulses(
            waveform, leftover,
            CFG.threshold_volts,
            CFG.pulse_min_samp,
            CFG.pulse_max_samp,
            CFG.pulse_metric,
        )

        t_now = time.perf_counter()
        for amp in amps:
            pulse_idx += 1
            try:
                _pulse_queue.put_nowait(
                    PulseMeasurement(pulse_idx, t_now, amp)
                )
            except queue.Full:
                pass

        # Pace to real time
        elapsed = time.perf_counter() - t0
        wait    = interval - elapsed
        if wait > 0:
            time.sleep(wait)

    print("[SIM] Stopped.")


# ══════════════════════════════════════════════════════════════════════════════
# LIVE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

_BG  = "#0d1117"
_FG  = "#e6edf3"
_AX  = "#161b22"
_DIM = "#30363d"
_BLU = "#58a6ff"
_ORG = "#f0883e"
_GRN = "#56d364"
_RED = "#ff7b72"

plt.rcParams.update({
    "figure.facecolor": _BG, "axes.facecolor": _AX,
    "axes.edgecolor":   _DIM, "axes.labelcolor": _FG,
    "axes.titlecolor":  _FG,  "xtick.color": _DIM,
    "ytick.color":      _DIM, "xtick.labelcolor": _FG,
    "ytick.labelcolor": _FG,  "grid.color": _DIM,
    "grid.alpha":       0.4,  "text.color": _FG,
    "legend.facecolor": "#0d1117", "legend.edgecolor": _DIM,
    "legend.labelcolor": _FG, "font.family": "monospace",
    "font.size": 9, "axes.titlesize": 10,
})


def run_dashboard() -> None:
    W, SW = CFG.display_window, CFG.stats_window

    buf_idx  : Deque[int]   = collections.deque(maxlen=W)
    buf_volt : Deque[float] = collections.deque(maxlen=W)
    buf_mean : Deque[float] = collections.deque(maxlen=W)
    buf_rms  : Deque[float] = collections.deque(maxlen=W)
    # Downsampled mean: one point every mean_stride pulses
    MS = CFG.mean_stride
    ds_mean_idx : Deque[int]   = collections.deque(maxlen=W // max(MS, 1))
    ds_mean_val : Deque[float] = collections.deque(maxlen=W // max(MS, 1))

    csv_fh, csv_wr = None, None
    if CFG.log_to_csv:
        csv_fh = open(Path(CFG.log_path), "w", newline="")
        csv_wr = csv.writer(csv_fh)
        csv_wr.writerow(["pulse_index", "timestamp_s", "voltage_V",
                         "rolling_mean_V", "rolling_std_V",
                         "rolling_rms_noise_pct"])
        print(f"[LOG] Writing → {CFG.log_path}")

    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor(_BG)
    mode = "HARDWARE  continuous @ " + f"{CFG.sample_rate/1e6:.1f} MS/s" \
           if HW_AVAILABLE else "SIMULATION"
    fig.suptitle(
        f"  LASER PULSE NOISE TRACKER  ·  NI DAQ 6143  ·  [ {mode} ]",
        fontsize=11, fontweight="bold", color=_FG, y=0.98,
    )

    gs = gridspec.GridSpec(3, 2, figure=fig,
                           hspace=0.55, wspace=0.30,
                           left=0.07, right=0.97, top=0.93, bottom=0.07)

    ax_sig   = fig.add_subplot(gs[0, :])
    ax_noise = fig.add_subplot(gs[1, :])
    ax_hist  = fig.add_subplot(gs[2, 0])
    ax_stat  = fig.add_subplot(gs[2, 1])

    for ax in (ax_sig, ax_noise, ax_hist):
        ax.grid(True, linestyle="--")
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax_stat.axis("off")

    (ln_v,) = ax_sig.plot([], [], lw=0.6, color=_BLU, label="Pulse amplitude")
    (ln_m,) = ax_sig.plot([], [], lw=0, color=_ORG,  # line hidden; markers only
                           marker="o", markersize=3, markerfacecolor=_ORG,
                           markeredgewidth=0, ls="--",
                           label=f"Mean every {CFG.mean_stride} pulses (window={SW})",
                           alpha=0.9)
    ax_sig.set_ylabel("Voltage (V)")
    ax_sig.set_title(f"Per-Pulse Amplitude  [{CFG.pulse_metric}]")
    ax_sig.legend(loc="upper right", fontsize=8)

    (ln_rms,)   = ax_noise.plot([], [], lw=1.0, color=_GRN, label="RMS noise (%)")
    (ln_alarm,) = ax_noise.plot([], [], lw=1.0, color=_RED, ls=":",
                                 label=f"Alarm  {CFG.alarm_rms_pct:.1f}%")
    ax_noise.set_ylabel("Noise (%)")
    ax_noise.set_title(f"Rolling RMS Noise  (window = {SW} pulses)")
    ax_noise.set_xlabel("Pulse #")
    ax_noise.legend(loc="upper right", fontsize=8)

    ax_hist.set_xlabel("Voltage (V)")
    ax_hist.set_ylabel("Count")
    ax_hist.set_title(f"Amplitude Distribution  (last {W} pulses)")

    stats_txt = ax_stat.text(
        0.05, 0.97, "", transform=ax_stat.transAxes,
        va="top", fontsize=9.5, fontfamily="monospace",
        color=_FG, linespacing=1.8,
    )
    ax_stat.set_title("Live Statistics", pad=6)

    alarm_bg = plt.Rectangle(
        (0.73, 0.946), 0.25, 0.042,
        transform=fig.transFigure, facecolor=_AX,
        edgecolor=_DIM, linewidth=0.8, zorder=5,
    )
    fig.add_artist(alarm_bg)
    alarm_lbl = fig.text(
        0.855, 0.966, "● OK", ha="center", va="center",
        fontsize=9, fontweight="bold", fontfamily="monospace",
        color=_GRN, zorder=6,
    )

    def _update(_frame):
        batch: List[PulseMeasurement] = []
        while True:
            try:
                batch.append(_pulse_queue.get_nowait())
            except queue.Empty:
                break
        if not batch:
            return

        for pm in batch:
            buf_idx.append(pm.index)
            buf_volt.append(pm.voltage)

        recent = np.array(list(buf_volt)[-SW:])
        st = compute_stats(recent)

        for pm in batch:
            buf_mean.append(st.mean)
            buf_rms.append(st.rms_noise)
            # Downsample: emit a mean point every mean_stride pulses
            if pm.index % MS == 0:
                ds_mean_idx.append(pm.index)
                ds_mean_val.append(st.mean)
            if csv_wr:
                csv_wr.writerow([pm.index, f"{pm.timestamp:.6f}",
                                 f"{pm.voltage:.6f}", f"{st.mean:.6f}",
                                 f"{st.std:.6f}", f"{st.rms_noise:.4f}"])

        idx_l  = list(buf_idx)
        volt_l = list(buf_volt)

        ln_v.set_data(idx_l, volt_l)
        ln_m.set_data(list(ds_mean_idx), list(ds_mean_val))
        ax_sig.relim(); ax_sig.autoscale_view()

        ln_rms.set_data(idx_l, list(buf_rms))
        if idx_l:
            ln_alarm.set_data([idx_l[0], idx_l[-1]],
                              [CFG.alarm_rms_pct] * 2)
        ax_noise.relim(); ax_noise.autoscale_view()
        ax_noise.set_ylim(bottom=0)

        # Histogram
        ax_hist.cla()
        ax_hist.set_facecolor(_AX)
        ax_hist.grid(True, linestyle="--", alpha=0.4)
        ax_hist.set_xlabel("Voltage (V)")
        ax_hist.set_ylabel("Count")
        ax_hist.set_title(f"Amplitude Distribution  (last {W} pulses)")
        v_arr  = np.array(volt_l)
        n_bins = min(80, max(15, len(v_arr) // 6))
        ax_hist.hist(v_arr, bins=n_bins, color=_BLU,
                     alpha=0.65, edgecolor=_BG, linewidth=0.3)
        if len(v_arr) >= 20:
            mu_f, sig_f = float(np.mean(v_arr)), float(np.std(v_arr))
            bw = (v_arr.max() - v_arr.min()) / n_bins if n_bins else 1
            x_fit = np.linspace(v_arr.min(), v_arr.max(), 300)
            y_fit = stats.norm.pdf(x_fit, mu_f, sig_f) * len(v_arr) * bw
            ax_hist.plot(x_fit, y_fit, color=_ORG, lw=1.5,
                         label=f"Fit  μ={mu_f:.4f} V  σ={sig_f:.5f} V")
            ax_hist.legend(fontsize=7.5, loc="upper right")

        # Pulse rate estimate
        if len(buf_idx) >= 2:
            span_pulses = buf_idx[-1] - buf_idx[0]
            # timestamps not stored per-pulse here; use count/window as proxy
            rate_str = f"{CFG.sim_rep_rate if not HW_AVAILABLE else '~5k'} Hz"
        else:
            rate_str = "–"

        stats_txt.set_text(
            f"Pulse count   {idx_l[-1]:>10,d}\n"
            f"──────────────────────────\n"
            f"Mean amp      {st.mean:>+10.5f} V\n"
            f"Std dev (σ)   {st.std:>+10.5f} V\n"
            f"RMS noise     {st.rms_noise:>9.4f} %\n"
            f"RMS absolute  {st.rms_abs:>+10.5f} V\n"
            f"Peak-to-peak  {st.peak_to_peak:>10.5f} V\n"
            f"──────────────────────────\n"
            f"Stat window   {st.n:>10,d} pulses\n"
            f"Threshold     {CFG.threshold_volts:>9.3f} V\n"
            f"Alarm thresh  {CFG.alarm_rms_pct:>9.2f} %\n"
            f"──────────────────────────\n"
            f"Last voltage  {volt_l[-1]:>+10.5f} V"
        )

        tripped = st.rms_noise > CFG.alarm_rms_pct
        alarm_lbl.set_text("⚠ ALARM" if tripped else "● OK")
        alarm_lbl.set_color(_RED if tripped else _GRN)
        alarm_bg.set_facecolor("#2d0000" if tripped else _AX)

    ani = animation.FuncAnimation(   # noqa: F841
        fig, _update, interval=100, blit=False, cache_frame_data=False
    )

    try:
        plt.show()
    finally:
        _stop.set()
        if csv_fh:
            csv_fh.flush()
            csv_fh.close()
            print(f"[LOG] Saved → {CFG.log_path}")


# ══════════════════════════════════════════════════════════════════════════════
# QUICK CHECK — run this to find your threshold before launching the dashboard
# ══════════════════════════════════════════════════════════════════════════════

def quick_check(seconds: float = 0.5) -> None:
    """
    Acquire a short burst at the configured sample_rate, print baseline and
    peak statistics, and suggest a threshold.  Run once before main():

        python -c "from laser_noise_tracker import quick_check; quick_check()"
    """
    if not HW_AVAILABLE:
        print("[quick_check] nidaqmx not available — cannot run on hardware.")
        return

    n = int(CFG.sample_rate * seconds)
    ch = f"{CFG.device}/{CFG.ai_channel}"
    print(f"[quick_check] Acquiring {n} samples ({seconds:.1f} s) from {ch} …")

    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(
            ch,
            terminal_config=TerminalConfiguration.DIFF,
            min_val=CFG.v_min,
            max_val=CFG.v_max,
        )
        task.timing.cfg_samp_clk_timing(
            rate=CFG.sample_rate,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=n,
        )
        task.start()
        data = np.array(task.read(number_of_samples_per_channel=n, timeout=seconds + 5))

    peak      = float(data.max())
    baseline  = float(np.median(data[data < np.percentile(data, 50)]))
    suggested = round((peak - baseline) * 0.4 + baseline, 3)

    print(f"  Baseline (median low half) : {baseline:+.4f} V")
    print(f"  Peak                       : {peak:+.4f} V")
    print(f"  Suggested threshold (~40%) : {suggested:+.4f} V")
    print(f"  → set  threshold_volts = {suggested}  in Config")


# ══════════════════════════════════════════════════════════════════════════════
# OSCILLOSCOPE — raw waveform viewer (run this first to diagnose signal)
# ══════════════════════════════════════════════════════════════════════════════

def oscilloscope(duration_s: float = 10.0) -> None:
    """
    Display a live raw-sample oscilloscope of the DAQ input.
    No pulse detection — just raw voltage vs sample index.

    Use this to:
      1. Confirm the DAQ is receiving a signal at all.
      2. Read off the baseline and pulse peak to set threshold_volts.
      3. Measure the pulse width in samples to set pulse_min/max_samp.

    Usage:
        python -c "from laser_noise_tracker import oscilloscope; oscilloscope()"
    """
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

    # Keep a rolling buffer of the last N raw samples for display
    DISP_SAMPLES = CFG.read_chunk * 4      # ~4 read-chunks wide
    raw_buf: collections.deque = collections.deque(maxlen=DISP_SAMPLES)
    chunk_queue: queue.Queue = queue.Queue(maxsize=200)
    stop_osc = threading.Event()

    # ── acquisition thread ────────────────────────────────────────────────
    def _acq():
        if not HW_AVAILABLE:
            # Simulate a clean signal so the oscilloscope is useful in sim mode
            rng  = np.random.default_rng(1)
            spp  = CFG.sample_rate / CFG.sim_rep_rate
            phase = 0.0
            while not stop_osc.is_set():
                chunk = np.zeros(CFG.read_chunk)
                pos   = phase
                while pos < CFG.read_chunk:
                    i = int(pos)
                    if 0 <= i < CFG.read_chunk:
                        w = CFG.sim_pulse_width
                        xs = np.arange(max(0, i - w*2), min(CFG.read_chunk, i + w*2))
                        amp = CFG.sim_voltage * (1 + rng.normal(0, CFG.sim_noise_frac))
                        chunk[xs] += amp * np.exp(-0.5*((xs-pos)/(w/2.5))**2)
                    pos += spp
                phase = pos - CFG.read_chunk
                chunk += rng.normal(0, CFG.sim_noise_frac * CFG.sim_voltage * 0.05,
                                    size=CFG.read_chunk)
                try:
                    chunk_queue.put_nowait(chunk)
                except queue.Full:
                    pass
                time.sleep(CFG.read_chunk / CFG.sample_rate)
            return

        ch = f"{CFG.device}/{CFG.ai_channel}"
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                ch,
                terminal_config=TerminalConfiguration.DIFF,
                min_val=CFG.v_min,
                max_val=CFG.v_max,
            )
            hw_buf = max(CFG.read_chunk * 100, CFG.sample_rate)
            task.timing.cfg_samp_clk_timing(
                rate=CFG.sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=hw_buf,
            )
            task.start()
            while not stop_osc.is_set():
                try:
                    raw = task.read(
                        number_of_samples_per_channel=CFG.read_chunk,
                        timeout=2.0,
                    )
                    try:
                        chunk_queue.put_nowait(np.asarray(raw, dtype=np.float64))
                    except queue.Full:
                        pass
                except Exception as exc:
                    if stop_osc.is_set():
                        break
                    print(f"[OSC] {exc}")
                    time.sleep(0.01)

    acq_t = threading.Thread(target=_acq, daemon=True)
    acq_t.start()

    # ── figure ────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(13, 7),
                              gridspec_kw={"height_ratios": [3, 1]})
    fig.patch.set_facecolor(_BG)
    fig.suptitle("  RAW OSCILLOSCOPE  ·  NI DAQ 6143  "
                 "(close window to exit)",
                 fontsize=11, fontweight="bold", color=_FG)

    ax_wave, ax_info = axes
    for ax in axes:
        ax.set_facecolor(_AX)
        ax.tick_params(colors=_DIM, labelcolor=_FG)
        for sp in ax.spines.values():
            sp.set_edgecolor(_DIM)

    ax_wave.grid(True, linestyle="--", color=_DIM, alpha=0.4)
    ax_wave.set_ylabel("Voltage (V)", color=_FG)
    ax_wave.set_xlabel("Sample index (rolling)", color=_FG)
    ax_wave.set_title("Raw ADC input", color=_FG)

    (ln_raw,)   = ax_wave.plot([], [], lw=0.7, color=_BLU, label="Raw signal")
    ln_thresh,  = ax_wave.plot([], [], lw=1.2, color=_RED,  ls="--",
                                label=f"threshold = {CFG.threshold_volts:.3f} V")
    ax_wave.legend(loc="upper right", fontsize=8,
                   facecolor="#0d1117", edgecolor=_DIM, labelcolor=_FG)

    ax_info.axis("off")
    info_txt = ax_info.text(
        0.01, 0.95, "Waiting for data …",
        transform=ax_info.transAxes,
        va="top", fontsize=9, fontfamily="monospace", color=_FG,
        linespacing=1.7,
    )

    pulse_count = [0]

    def _update(_frame):
        # Drain chunk queue into rolling buffer
        got_new = False
        while True:
            try:
                chunk_queue.get_nowait()
                raw_buf.extend(chunk_queue.get_nowait()
                               if not chunk_queue.empty() else [])
            except queue.Empty:
                break
        # Simpler drain:
        new_chunks = []
        while True:
            try:
                new_chunks.append(chunk_queue.get_nowait())
            except queue.Empty:
                break
        for c in new_chunks:
            raw_buf.extend(c)
            got_new = True

        if not raw_buf:
            return

        arr = np.array(raw_buf)
        xs  = np.arange(len(arr))

        ln_raw.set_data(xs, arr)
        ln_thresh.set_data([0, len(arr)-1],
                           [CFG.threshold_volts, CFG.threshold_volts])
        ax_wave.relim()
        ax_wave.autoscale_view()

        # Quick pulse count on current buffer
        above  = (arr >= CFG.threshold_volts).astype(np.int8)
        pulses = int(np.sum(np.diff(above) > 0))
        baseline_med = float(np.median(arr[arr < CFG.threshold_volts])
                             if np.any(arr < CFG.threshold_volts) else 0)
        peak_val = float(arr.max())
        pct_above = float(np.mean(arr >= CFG.threshold_volts) * 100)

        window_ms = len(arr) / CFG.sample_rate * 1e3
        info_txt.set_text(
            f"Samples in view : {len(arr):>8,d}   "
            f"Sample rate : {CFG.sample_rate/1e3:.0f} kS/s   "
            f"Window : {window_ms:.1f} ms\n"
            f"Baseline (median below thresh) : {baseline_med:>+8.4f} V     "
            f"Peak : {peak_val:>+8.4f} V     "
            f"Above threshold : {pct_above:.1f} %\n"
            f"Rising edges (pulses) in view  : {pulses:>6d}     "
            f"Threshold : {CFG.threshold_volts:.4f} V  "
            f"{'← threshold looks OK' if 0 < pct_above < 30 else '← ADJUST threshold_volts!'}"
        )

    ani = animation.FuncAnimation(
        fig, _update, interval=80, blit=False, cache_frame_data=False
    )

    try:
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()
    finally:
        stop_osc.set()
        acq_t.join(timeout=2.0)



# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║    LASER PULSE NOISE TRACKER  —  NI DAQ 6143        ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  nidaqmx  : {'found — hardware mode' if HW_AVAILABLE else 'not found — simulation mode'}")
    print(f"  Strategy : continuous acquisition + threshold detection")
    print(f"  Tip      : if nothing appears, run oscilloscope() first:")
    print(f"             python -c \"from laser_noise_tracker import oscilloscope; oscilloscope()\"")
    print(f"  Started  : {datetime.now():%Y-%m-%d  %H:%M:%S}")
    print()

    acq_fn = _acquire_hardware if HW_AVAILABLE else _acquire_simulation
    acq_thread = threading.Thread(target=acq_fn, daemon=True, name="acq")
    acq_thread.start()

    run_dashboard()

    _stop.set()
    acq_thread.join(timeout=3.0)
    print("  Done.")


if __name__ == "__main__":
    main()
