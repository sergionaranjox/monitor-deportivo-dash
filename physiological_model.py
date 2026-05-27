"""
Physiological model for SnowTrack simulation.

ECG template source (priority order):
  1. Disk cache — assets/ecg_template.npy
  2. PhysioNet MIT-BIH record 100 via wfdb (ambulatory monitoring, MLII lead,
     360 Hz — recorded during patient activity, giving exercise-like morphology)
  3. Synthetic PQRST model tuned for intense aerobic exercise morphology

HR model:
  - calculate_session_params()  — called at session START; locks in the max HR
    the ECG will ramp toward and the summary will display.
  - finalize_session_biometrics() — called at session END; applies cardiac drift
    and computes SpO2 from actual duration; uses the pre-locked max HR.
  - hr_at_elapsed()  — instantaneous HR for real-time ECG, ramps to locked max HR.

SpO2: altitude lookup table from published data (Severinghaus 1979;
      Roach & Hackett 2001) with exercise hypoxia penalty.
"""

import os
import random
import logging
import numpy as np
from scipy.signal import resample as scipy_resample

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SpO2 altitude table  (alt_m, low%, high%)
# ---------------------------------------------------------------------------
_SPO2_TABLE = [
    ( 500, 98, 99),
    (1000, 97, 98),
    (1500, 96, 98),
    (2000, 95, 97),
    (2500, 93, 96),
    (3000, 91, 94),
    (3500, 88, 92),
    (4000, 86, 90),
]


def get_spo2_range(altitud: int):
    """Linearly interpolated SpO2 range for the given altitude (metres)."""
    for i in range(len(_SPO2_TABLE) - 1):
        a0, lo0, hi0 = _SPO2_TABLE[i]
        a1, lo1, hi1 = _SPO2_TABLE[i + 1]
        if a0 <= altitud <= a1:
            f = (altitud - a0) / (a1 - a0)
            return int(lo0 + f * (lo1 - lo0)), int(hi0 + f * (hi1 - hi0))
    if altitud < _SPO2_TABLE[0][0]:
        return _SPO2_TABLE[0][1], _SPO2_TABLE[0][2]
    return _SPO2_TABLE[-1][1], _SPO2_TABLE[-1][2]


# ---------------------------------------------------------------------------
# Session biometrics — two-phase model
# ---------------------------------------------------------------------------

def calculate_session_params(modalidad: str, altitud: int, age: int) -> dict:
    """
    Pre-calculate session HR parameters at session START and return a dict
    that must be persisted in dcc.Store.  This is the single source of truth
    for max_hr — the same value the ECG will ramp toward and the summary shows.

    Karvonen formula + altitude VO2max correction (West 2012).
    """
    hr_rest = random.randint(54, 68)
    hr_max  = max(150, 220 - age) if age > 0 else 190

    intensity = random.uniform(0.65, 0.80) if modalidad == "esqui" else random.uniform(0.70, 0.85)
    target_hr = hr_rest + (hr_max - hr_rest) * intensity

    if altitud > 1500:
        vo2_drop  = min(0.32, (altitud - 1500) / 1000 * 0.07)
        target_hr += vo2_drop * (hr_max - hr_rest) * 0.28

    avg_hr = int(min(target_hr,              hr_max * 0.97))
    max_hr = int(min(avg_hr + random.randint(12, 22), hr_max))
    min_hr = int(max(avg_hr - random.randint(15, 25), hr_rest + 10))

    return {
        "hr_rest":      hr_rest,
        "hr_max_limit": hr_max,
        "avg_hr":       avg_hr,
        "max_hr":       max_hr,
        "min_hr":       min_hr,
    }


def finalize_session_biometrics(stored: dict, altitud: int, duration_sec: int):
    """
    Finalize biometrics at session END using pre-locked HR values.
    max_hr reported = HR actually reached at session end (same exponential
    ramp used by the ECG display), so summary matches what was shown on screen.
    Returns (avg_hr, max_hr, min_hr, avg_spo2, min_spo2).
    """
    hr_rest      = stored.get("hr_rest", 63)
    max_hr_limit = stored["max_hr"]
    min_hr       = stored["min_hr"]
    tau          = 90.0

    # HR reached at the end of the session — mirrors hr_at_elapsed() without noise
    T           = max(duration_sec, 1)
    max_hr      = int(hr_rest + (max_hr_limit - hr_rest) * (1.0 - np.exp(-T / tau)))
    max_hr      = min(max_hr, max_hr_limit)

    # Average HR = analytic integral of the ramp divided by T
    avg_integral = hr_rest * T + (max_hr_limit - hr_rest) * (T - tau * (1.0 - np.exp(-T / tau)))
    avg_hr       = max(hr_rest, min(int(avg_integral / T), max_hr))

    # Cardiac drift: +1 bpm per 2 min after first 20 min
    if duration_sec > 1200:
        drift  = min(12, (duration_sec - 1200) / 120)
        avg_hr = int(min(avg_hr + drift, max_hr))

    spo2_lo, spo2_hi = get_spo2_range(altitud)
    penalty  = 2 if altitud > 2500 else (1 if altitud > 1500 else 0)
    avg_spo2 = max(70, random.randint(spo2_lo, spo2_hi) - penalty)
    min_spo2 = max(70, avg_spo2 - random.randint(1, 4))

    return avg_hr, max_hr, min_hr, avg_spo2, min_spo2


# ---------------------------------------------------------------------------
# Real-time HR during session
# ---------------------------------------------------------------------------

def hr_at_elapsed(seconds: float, target_max_hr: int, hr_rest: int = 63,
                  tau: float = 90.0) -> int:
    """
    Instantaneous HR estimate ramping from hr_rest toward target_max_hr.
    Uses exponential kinetics with time constant tau = 90 s (typical
    aerobic warm-up constant).  Adds ±1.5 bpm gaussian HRV noise.
    At ~5 min (300 s) the HR reaches 97 % of target_max_hr.
    """
    hr_now  = hr_rest + (target_max_hr - hr_rest) * (1.0 - np.exp(-seconds / tau))
    hr_now += random.gauss(0, 1.5)
    return max(40, min(int(hr_now), target_max_hr))


# ---------------------------------------------------------------------------
# ECG template — real PhysioNet data, cached to disk
# ---------------------------------------------------------------------------

_TEMPLATE_PATH = "assets/ecg_template.npy"
_beat_template = None   # normalised single-beat array (~250 samples)


def _exercise_synthetic_beat(n: int = 250) -> np.ndarray:
    """
    PQRST model tuned for intense aerobic exercise morphology:
    - Taller, broader T wave (sympathetic activation → ↑ contractility)
    - Peaked P wave (increased atrial pressure / sympathetic tone)
    - Short PR interval (0.12 s, typical during exercise)
    - Sharp, narrow QRS (well-trained ventricle)
    - Shortened QT relative to rest
    """
    t = np.linspace(0, 1, n)

    def g(center, width, amp):
        return amp * np.exp(-0.5 * ((t - center) / width) ** 2)

    beat = (
        g(0.09,  0.018,  0.18) +   # P  — peaked, sympathetic
        g(0.20,  0.007, -0.14) +   # Q
        g(0.24,  0.005,  1.50) +   # R  — tall, narrow
        g(0.28,  0.007, -0.28) +   # S
        g(0.58,  0.055,  0.52)     # T  — tall & broad (exercise)
    )
    beat += np.random.normal(0, 0.015, n)
    return beat


def _load_template() -> None:
    """
    Load ECG beat template (priority):
      1. Disk cache
      2. PhysioNet MIT-BIH record 100 — ambulatory MLII lead (360 Hz),
         recorded during patient activity → exercise-like QRS morphology.
      3. Synthetic exercise beat (fallback)
    """
    global _beat_template

    if os.path.exists(_TEMPLATE_PATH):
        _beat_template = np.load(_TEMPLATE_PATH)
        log.info("[ECG] Template loaded from disk cache.")
        return

    try:
        import wfdb
        from wfdb.processing import gqrs_detect

        log.info("[ECG] Downloading exercise ECG template from PhysioNet (mitdb/100)…")
        # Record 100: ambulatory monitoring (MLII + V5), fs=360 Hz, 30 min
        # Taking the first 10 s (3 600 samples) — enough for several beats
        rec = wfdb.rdrecord("100", sampfrom=0, sampto=3600, pn_dir="mitdb")
        sig = rec.p_signal[:, 0].astype(float)   # MLII lead
        fs  = rec.fs  # 360 Hz

        qrs = gqrs_detect(sig=sig, fs=fs)

        if len(qrs) > 3:
            mid  = qrs[len(qrs) // 2]
            half = (qrs[1] - qrs[0]) // 2
            raw  = sig[max(0, mid - half): mid + half]

            beat = scipy_resample(raw, 250).astype(float)
            beat -= beat.min()
            if beat.max() > 0:
                beat = beat / beat.max() * 1.5 - 0.30   # normalise to [-0.3, 1.2]

            _beat_template = beat
            os.makedirs("assets", exist_ok=True)
            np.save(_TEMPLATE_PATH, _beat_template)
            log.info("[ECG] Real PhysioNet (mitdb/100) template cached.")
            return

    except Exception as exc:
        log.warning(f"[ECG] PhysioNet unavailable ({exc}). Using exercise synthetic model.")

    _beat_template = _exercise_synthetic_beat()
    log.info("[ECG] Using synthetic exercise PQRST model.")


def preload_template() -> None:
    """Call once at app startup to avoid first-render latency."""
    _load_template()


def _get_template() -> np.ndarray:
    if _beat_template is None:
        _load_template()
    return _beat_template


# ---------------------------------------------------------------------------
# ECG window generation  (called every 500 ms by the Dash interval)
# ---------------------------------------------------------------------------

def generate_ecg_window(n_points: int, seconds_elapsed: float,
                         hr: int, noise: float = 0.04):
    """
    Return (x_vals, y_vals) for one ECG display window.

    Resamples the beat template to match the current HR, tiles it to fill
    the window, then adds respiratory baseline wander and muscle noise.
    """
    template    = _get_template()
    beat_period = 60.0 / max(hr, 20)
    window_sec  = 2.4
    fs_virtual  = n_points / window_sec

    beat_samples = max(1, int(beat_period * fs_virtual))
    beat_hr      = scipy_resample(template, beat_samples)

    n_beats = int(np.ceil(n_points / beat_samples)) + 2
    tiled   = np.tile(beat_hr, n_beats)

    phase = int((seconds_elapsed % beat_period) * fs_virtual) % beat_samples
    tiled = np.roll(tiled, -phase)
    ecg   = tiled[:n_points].copy()

    t_win  = np.linspace(0, window_sec, n_points)
    ecg   += 0.05 * np.sin(2 * np.pi * 0.25 * t_win + seconds_elapsed * 0.8)
    ecg   += np.random.normal(0, noise, n_points)

    return list(range(n_points)), ecg.tolist()
