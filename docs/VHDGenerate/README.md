# VHDGenerate audio showcase

Static supplementary audio gallery at https://zhj12399.de/VHDGenerate/.

- `index.html`: 32 requested disease configurations, two generated clips each.
- `real.html`: 20 observed configurations, two real training clips each.
- Each example includes WAV playback and download, waveform, Log-Mel and MFCC.
- Teal marks configurations observed in the original database. Amber marks the
  12 exact complete configurations absent from the original database.
- Audio and PNG plots are embedded in per-configuration JS packs and loaded
  when the corresponding section enters the viewport. No external libraries or
  third-party audio hosting are required.

All source clips are 3 seconds at 2 kHz. Browser WAV copies are interpolated
to 8 kHz for playback compatibility, while features use the original sources.
Log-Mel: FFT 1024, Hann window 64, hop 32,
64 Slaney Mel bands, 0–1000 Hz, relative power in −80 to 0 dB. MFCC: 20
coefficients C1–C20 from the same Log-Mel matrix (C0 excluded), DCT type II
with orthonormal scaling.
Generated clips use the final compositional G1 sampling configuration.

Public metadata consists of condition labels, aggregated recording support,
and generic example IDs. Source recording identifiers and local provenance
are retained separately in the private build workspace.
