from __future__ import annotations

import math

from .model import FeatureFrame, clamp


def _band_power(power, frequencies, low: float, high: float) -> float:
    import numpy as np

    mask = (frequencies >= low) & (frequencies < high)
    return float(power[mask].sum()) if np.any(mask) else 0.0


def analyze_stereo(samples, sample_rate: int, previous_spectrum=None, previous_rms: float = 0.0):
    """Return a normalized music-oriented feature frame and current spectrum."""
    import numpy as np

    audio = np.asarray(samples, dtype=np.float32)
    if audio.ndim == 1:
        audio = audio[:, None]
    if audio.ndim != 2 or not len(audio):
        return FeatureFrame(), None
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)
    left, right = audio[:, 0], audio[:, 1]
    mono = (left + right) * .5
    rms_raw = float(np.sqrt(np.mean(mono * mono)))
    peak_raw = float(np.max(np.abs(mono)))
    energy = clamp(1.0 - math.exp(-rms_raw * 10.0))
    peak = clamp(1.0 - math.exp(-peak_raw * 6.0))
    crest = clamp((peak_raw / max(rms_raw, 1e-8) - 1.0) / 8.0)

    # A digitally silent route has no spectrum. Returning before the FFT keeps
    # its numerical floor from masquerading as brightness or density.
    if rms_raw < 1e-7:
        silent_spectrum = np.zeros(len(mono) // 2 + 1, dtype=np.float32)
        return FeatureFrame(rms_raw=rms_raw, rms=energy, peak=peak, crest=crest, silence=1.0), silent_spectrum

    windowed = mono * np.hanning(len(mono))
    magnitude = np.abs(np.fft.rfft(windowed)) + 1e-12
    power = magnitude * magnitude
    frequencies = np.fft.rfftfreq(len(mono), 1.0 / sample_rate)
    total = float(power.sum())
    nyquist = sample_rate * .5
    bands = [
        _band_power(power, frequencies, 20, 80),
        _band_power(power, frequencies, 80, 250),
        _band_power(power, frequencies, 250, 2000),
        _band_power(power, frequencies, 2000, 6000),
        _band_power(power, frequencies, 6000, nyquist + 1),
    ]
    band_total = max(sum(bands), 1e-12)
    bands = [clamp(value / band_total) for value in bands]
    centroid_hz = float((magnitude * frequencies).sum() / magnitude.sum())
    centroid = clamp(math.log1p(centroid_hz) / math.log1p(max(100.0, nyquist)))
    cumulative = np.cumsum(power)
    rolloff_index = int(np.searchsorted(cumulative, cumulative[-1] * .85)) if total else 0
    rolloff = clamp(frequencies[min(rolloff_index, len(frequencies) - 1)] / max(nyquist, 1.0))
    flatness = clamp(float(np.exp(np.mean(np.log(magnitude))) / np.mean(magnitude)))

    normalized = magnitude / max(float(np.linalg.norm(magnitude)), 1e-12)
    if previous_spectrum is None or len(previous_spectrum) != len(normalized):
        flux = 0.0
    else:
        flux = clamp(float(np.sqrt(np.mean(np.square(np.maximum(normalized - previous_spectrum, 0.0))))) * 18.0)
    onset = clamp(max(0.0, energy - previous_rms) * 4.0 + flux * .65)
    zero_crossing = clamp(float(np.mean(np.abs(np.diff(np.signbit(mono))))) * 3.0)

    mid, side = (left + right) * .5, (left - right) * .5
    mid_rms = float(np.sqrt(np.mean(mid * mid)))
    side_rms = float(np.sqrt(np.mean(side * side)))
    width = clamp(side_rms / max(mid_rms + side_rms, 1e-8) * 2.0)
    if float(np.std(left)) < 1e-8 or float(np.std(right)) < 1e-8:
        correlation = 1.0
    else:
        correlation = clamp((float(np.corrcoef(left, right)[0, 1]) + 1.0) * .5)

    frame = FeatureFrame(
        rms_raw=rms_raw, rms=energy, peak=peak, crest=crest,
        sub=bands[0], low=bands[1], low_mid=bands[2], high_mid=bands[3], high=bands[4],
        centroid=centroid, centroid_hz=centroid_hz, rolloff=rolloff, flatness=flatness, flux=flux, onset=onset,
        zero_crossing=zero_crossing, width=width, correlation=correlation,
        silence=clamp(1.0 - energy * 8.0),
    )
    return frame, normalized
