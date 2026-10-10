# fftechno - instrument definitions

Define instruments here and run `python -m fftechno synth` to write
`filters/<name>.txt` (one ffmpeg filtergraph per instrument). Available `type`s
and their parameters live in `fftechno/synth.py`.

- `kick`  - amp, f0, sweep, rate, decay, click_freq, click_decay, click_amt, bpm
- `noise` - amp, decay, hp, lp, period

## Instruments

| name    | type | parameters |
|---------|------|------------|
| kick909 | kick | amp=0.9, f0=50, sweep=180, rate=50, decay=8, click_freq=1500, click_decay=250, click_amt=0.25 |
