# fftechno - synth definitions

`python -m fftechno synth` renders each instrument below into `filters/<name>.txt`
by plugging these values into `templates/<template>`. `bar`, `step`, `beat` and
`dur` come from `song.md`. Every other placeholder must be defined by the globals
here or by the instrument's `parameters`.

Scalar values are single tokens. List values (used by `{{if_steps(...)}}`) are
`\|`-separated inside the table cell (the backslash escapes the markdown pipe).

sr: 192000
lp: 19000
osr: 48000
gold: 2.399963
vbase: 0.6
vamt: 0.4
grid: floor(mod(t,{{bar}})/{{step}})

## Instruments

Seven stems, all dry and steady (no room/delay and no randomness): a 4-on-4 kick, a
closed hat (`hat_step`) and an open hat (`ohat_dyn`) on the offbeats, a backbeat
snare and rim, and a one-note bass under a resonant low-pass.

- `hat_step` hits are set by `gates` and accented by `vel`.
- `ohat_dyn` adds dynamism: every hit's **decay** is scaled by
  `dmin + dspan*(...)` and its **velocity** by `vbase + vamt*(...)`, both indexed by
  the golden-ratio sequence over the whole track - deterministic, never a fixed loop.
- The bass low-pass (`lowpass=f=320:t=q:w=1.4`) is a resonant 12 dB/oct - lower and
  more resonant than the plain 900 Hz one it replaced.

| name | template     | parameters |
|------|--------------|------------|
| kick | kick.txt     | amp=0.95, beat=0.6, f0=45, sweep=190, rate=48, decay=20, click_amt=0.35, click_f=1100, click_decay=420, sub_amt=0.6, sub_f=42, sub_decay=14, noise_amt=0.22, noise_decay=260, eq_f=52, eq_g=4, clip=0.85 |
| hat  | hat_step.txt | amp=0.8, decay=140, hp=8000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, vel=1.0\|0.0\|0.72\|0.0\|0.92\|0.0\|0.72\|0.0\|1.0\|0.0\|0.72\|0.0\|0.92\|0.0\|0.72\|0.0 |
| ohat | ohat_dyn.txt | amp=0.5, decay=22, dmin=0.35, dspan=1.3, gold2=0.7320508075688772, hp=6500, gates=0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0 |
| snare| snare.txt   | amp=0.7, tone_amt=0.7, f1=185, f2=330, tmix=0.6, decay=26, noise_amt=0.9, ndecay=28, hp=200, lpc=8500, gates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0 |
| rim  | rim.txt      | amp=0.7, n_amt=0.5, tone_f=1500, decay=120, hp=1600, gates=0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1 |
| bass | bass.txt     | amp1=0.5, amp2=0.4, amp3=0.3, decay1=16, decay2=12, detune=1.003, note_def=55, notes=55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55\|55, lp_bass=320, lp_q=1.4, eq_f=45, eq_g=6, sub_cut=70, sub_boost=7, sub_dry=0.5, sub_wet=1, clip=0.85 |
| blow | blow.txt     | amp=0.6, at=120, period=4.8, attack=25, decay=14, hp=280, lp_hi=7000, peak_f=800, peak_q=1.1, peak_g=5, clip=0.8, dry_l=0.25, dry_r=0.75, ltaps=375\|1125\|1875, ldec=0.5\|0.24\|0.11, rtaps=750\|1500\|2250, rdec=0.34\|0.16\|0.07 |
