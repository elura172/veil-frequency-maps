# Mirror Listener

A transparent Max Audio Effect that turns Mirror/Shimmer analysis OSC into stable, visible musical state.

The broader project-agnostic listening intelligence is defined in the
[canonical Mirror Listener specification](MIRROR-LISTENER-SPEC.md).

It listens on UDP `8000` and accepts:

```text
/mirror/dominant_freq <hz>
/mirror/frequency <hz>
/mirror/pitch <hz> [confidence]
/mirror/confidence <0..1>
/mirror/rms <0..1>
/mirror/centroid <hz>
/shimmer/rms <0..1>
/shimmer/centroid <hz>
/mirror/reset
/mirror/status
```

The legacy `/mirror/dominant_freq` and `/shimmer/*` addresses are retained. Frequency, fractional MIDI note, confidence, RMS, centroid, and connection health are smoothed and shown in the device. The same values are published inside Max as `mirror.frequency`, `mirror.note`, `mirror.confidence`, `mirror.rms`, `mirror.centroid`, and `mirror.connected`.

Status replies are sent to `127.0.0.1:8001` under `/mirror/listener/*`. The connection indicator times out after 2.5 seconds without input. Audio passes through unchanged.
