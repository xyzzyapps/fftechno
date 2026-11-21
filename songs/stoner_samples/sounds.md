# fftechno - sampler definitions

Sample-based stoner rock, take 2. The first take used the FreePats *pre-distorted*
samples, which measured very dark (almost no 800-2500 Hz growl) and sounded muddy.
This take uses the **clean DI** samples (`FSBS-direct`) pitched naturally, then runs
a hard **Orange-style fuzz chain** per hit (pre-EQ -> tanh clip -> mid growl -> cab
low-pass) so the riff has bite. Guitars play **power chords** (`chord=1|1.5:0.7|2:0.45`
= root + fifth + octave) with **sustain** (trim 1.2 s), over a **2-bar riff**
(`pat_bars=2`) instead of a monotonous 1-bar loop.

Sources: Pearl Master Studio acoustic drums (CC-BY 3.0); FreePats DI electric guitar
(`FSBS-direct`) and picked electric bass (`electric-bass-YR`), both CC0. Drop-C riff,
C minor: bar 1 C-C-Eb-F / C-C-Eb-G, bar 2 C-C-Eb-F / Ab-Ab-G-F.

| name     | sample                          | params |
|----------|---------------------------------|--------|
| kick     | samples/stoner_kit/kick.wav     | pat=0\|6\|8\|14, jitter=8, trim=0.55, fx=highpass=f=35;equalizer=f=60:t=q:w=1:g=6;equalizer=f=300:t=q:w=1:g=-4;equalizer=f=3500:t=q:w=1:g=6;acompressor=threshold=0.3:ratio=4:attack=5:release=80, gain=1.7 |
| snare    | samples/stoner_kit/snare.wav    | rr=samples/stoner_kit/snare.wav\|samples/stoner_kit/snare2.wav\|samples/stoner_kit/snare3.wav, pat=4\|7\|12\|15, vel=1\|0.35\|1\|0.4, jitter=10, trim=0.5, fx=highpass=f=100;equalizer=f=200:t=q:w=1:g=5;equalizer=f=250:t=q:w=1:g=3;equalizer=f=4500:t=q:w=1:g=7;acompressor=threshold=0.25:ratio=4:attack=3:release=120, gain=1.7 |
| tom      | samples/stoner_kit/tom1.wav     | rr=samples/stoner_kit/tom1.wav\|samples/stoner_kit/tom2.wav\|samples/stoner_kit/tom3.wav, pat=0\|2\|4\|6\|8\|10\|12\|14, vel=1\|0.9\|1\|0.9\|1\|0.9\|1\|0.9, jitter=8, trim=0.5, fx=highpass=f=60;equalizer=f=150:t=q:w=1:g=4;equalizer=f=3000:t=q:w=1:g=4, gain=1.0 |
| hat      | samples/stoner_kit/hat-closed.wav | pat=0\|2\|4\|6\|8\|10\|12\|14, vel=1\|0.5\|0.8\|0.5\|1\|0.5\|0.8\|0.5, jitter=6, trim=0.2, fx=highpass=f=5500;equalizer=f=8000:t=q:w=1:g=3, gain=1.3 |
| ride     | samples/stoner_kit/ride.wav     | pat=0\|4\|8\|12, jitter=6, trim=0.7, fx=highpass=f=3000;equalizer=f=5000:t=q:w=1:g=3, gain=1.6 |
| crash    | samples/stoner_kit/crash.wav    | hits=0\|128\|256\|384\|512\|640\|768\|896\|1024\|1152, jitter=12, trim=1.8, fx=highpass=f=2000, gain=1.6 |
| bass     | samples/stoner_kit/bass.wav@65.41\|samples/stoner_kit/bass_e2.wav@82.41 | pat=0\|2\|4\|6\|8\|10\|12\|14\|16\|18\|20\|22\|24\|26\|28\|30, pat_bars=2, notes=65.41\|65.41\|77.78\|87.31\|65.41\|65.41\|77.78\|98\|65.41\|65.41\|77.78\|87.31\|103.83\|103.83\|98\|87.31, trim=0.8, fx=highpass=f=30;equalizer=f=400:t=q:w=1:g=4;asoftclip=type=tanh:threshold=0.45;equalizer=f=750:t=q:w=1:g=4;lowpass=f=1100, gain=0.5 |
| gtr_l    | samples/stoner_kit/di_c2.wav@65.41\|samples/stoner_kit/di_e2.wav@82.41\|samples/stoner_kit/di_a2.wav@110\|samples/stoner_kit/di_c3.wav@130.81 | pat=0\|2\|4\|6\|8\|10\|12\|14\|16\|18\|20\|22\|24\|26\|28\|30, pat_bars=2, notes=65.41\|65.41\|77.78\|87.31\|65.41\|65.41\|77.78\|98\|65.41\|65.41\|77.78\|87.31\|103.83\|103.83\|98\|87.31, chord=1\|1.5:0.7\|2:0.45, rate=1.003, trim=1.2, fx=highpass=f=90;equalizer=f=500:t=q:w=1:g=6;asoftclip=type=tanh:threshold=0.2;equalizer=f=900:t=q:w=1:g=7;equalizer=f=1800:t=q:w=1:g=5;lowpass=f=5200;highpass=f=100, gain=0.38 |
| gtr_r    | samples/stoner_kit/di_c2.wav@65.41\|samples/stoner_kit/di_e2.wav@82.41\|samples/stoner_kit/di_a2.wav@110\|samples/stoner_kit/di_c3.wav@130.81 | pat=0\|2\|4\|6\|8\|10\|12\|14\|16\|18\|20\|22\|24\|26\|28\|30, pat_bars=2, notes=65.41\|65.41\|77.78\|87.31\|65.41\|65.41\|77.78\|98\|65.41\|65.41\|77.78\|87.31\|103.83\|103.83\|98\|87.31, chord=1\|1.5:0.7\|2:0.45, rate=0.997, trim=1.2, fx=highpass=f=90;equalizer=f=520:t=q:w=1:g=6;asoftclip=type=tanh:threshold=0.2;equalizer=f=950:t=q:w=1:g=7;equalizer=f=1900:t=q:w=1:g=5;lowpass=f=5400;highpass=f=100, gain=0.38 |
| gtr_lead | samples/stoner_kit/di_c3.wav@130.81\|samples/stoner_kit/di_g3.wav@196 | pat=0\|4\|8\|12\|16\|20\|24\|28, pat_bars=2, notes=130.81\|155.56\|174.61\|196\|207.65\|196\|174.61\|155.56, trim=1.5, fx=highpass=f=200;equalizer=f=600:t=q:w=1:g=5;asoftclip=type=tanh:threshold=0.25;equalizer=f=1100:t=q:w=1:g=6;lowpass=f=5000;aphaser=in_gain=0.8:out_gain=0.6:delay=3:decay=0.35:speed=0.2:type=sinusoidal, gain=0.6 |
