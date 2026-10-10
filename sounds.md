# fftechno - synth definitions

`python -m fftechno synth` renders each instrument below into `filters/<name>.txt`
by plugging these values into `templates/<template>` (a `{{key}}` placeholder file).
No defaults exist: every placeholder an instrument uses must be defined by the
globals here or its own `parameters`.

sr: 192000
dur: 240
lp: 19000
osr: 48000
bar: 1.714286
step: 0.107143
gold: 2.399963
vbase: 0.6
vamt: 0.4

## Instruments

| name   | template  | parameters |
|--------|-----------|------------|
| kick   | kick.txt  | amp=0.95, f0=48, sweep=220, rate=55, decay=24, click_amt=0.4, click_f=1200, click_decay=420, sub_amt=0.5, sub_f=45, sub_decay=18, noise_amt=0.3, noise_decay=300, eq_f=60, eq_g=3, clip=0.8 |
| clap   | clap.txt  | amp=0.55, decay1=20, tone_amt=0.5, tone_f=200, decay2=28, hp=900, lpc=9000 |
| hat    | noise.txt | amp=0.35, decay=95, hp=7000 |
| ohat   | noise.txt | amp=0.4, decay=15, hp=6500 |
| shaker | noise.txt | amp=0.28, decay=70, hp=9000 |
| perc   | tom.txt   | amp=0.7, pitch=147, sweep=1.1, rate=28, decay=16, hp=110, lpc=3500, a1=0.8, a2=0.7, ad=55, adc=0.25 |
| bongo  | tom.txt   | amp=0.5, pitch=294, sweep=1.1, rate=30, decay=20, hp=150, lpc=5000, a1=0.8, a2=0.7, ad=40, adc=0.2 |
| rim    | rim.txt   | amp=0.4, n_amt=0.5, tone_f=1500, decay=120, hp=1500 |
