# vocals - minimal

**Not in the mix at the moment** - this track is instrumental for now. `vox.py`
only renders when `vox` is in `song.md`'s Stems table, so these lines are parked
here: add `vox` to the Stems table (and a `Levels` row) to bring the ticks back.

One word, once per kick: the count-in that opens the track. `trim_lead` removes the
leading silence the TTS pads onto every phrase, so each "tick" starts exactly on its
kick (without it the phrase lands about 0.15-0.65 s late, depending on the engine).

engine: flite
voice: slt
trim_lead: 1

## Lines

The same list becomes the on-screen lyric.

| text | time  |
|------|-------|
| tick | 0.000 |
| tick | 0.600 |
| tick | 1.200 |
| tick | 1.800 |
