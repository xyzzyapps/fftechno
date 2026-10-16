# fftechno - sample manifest

Every audio file the *sampler* songs read. `python -m fftechno samples` downloads
any that are missing and then normalises each one to 48 kHz PCM (see
`fftechno/samples.py`). The downloaded files live under `samples/<set>/<file>` and
are **not** committed (`.gitignore`), so a clone reproduces them from here. Keep the
`url` and `license` columns honest; a licence with a `|` in it must be reworded.

Add a row, run `python -m fftechno samples`, then reference `samples/<set>/<file>`
in a song's `sounds.md` `## Samplers` table.

| set         | file           | url                                                                                                        | license |
|-------------|----------------|------------------------------------------------------------------------------------------------------------|---------|
| triphop_kit | kick.wav       | https://oramics.github.io/sampled/DM/TR-909/SP/samples/kick.wav                                            | public-domain-like (oramics/sampled) |
| triphop_kit | kick-2.wav     | https://oramics.github.io/sampled/DM/TR-909/SP/samples/kick-2.wav                                          | public-domain-like (oramics/sampled) |
| triphop_kit | snare.wav      | https://oramics.github.io/sampled/DM/TR-909/SP/samples/snare.wav                                           | public-domain-like (oramics/sampled) |
| triphop_kit | snare-short.wav| https://oramics.github.io/sampled/DM/TR-909/SP/samples/snare-short.wav                                     | public-domain-like (oramics/sampled) |
| triphop_kit | hat-closed.wav | https://oramics.github.io/sampled/DM/TR-909/SP/samples/hihat-closed-1.wav                                  | public-domain-like (oramics/sampled) |
| triphop_kit | hat-open.wav   | https://oramics.github.io/sampled/DM/TR-909/SP/samples/hihat-open-1.wav                                    | public-domain-like (oramics/sampled) |
| triphop_kit | clap.wav       | https://oramics.github.io/sampled/DM/TR-909/SP/samples/clap1.wav                                            | public-domain-like (oramics/sampled) |
| triphop_kit | rim.wav        | https://oramics.github.io/sampled/DM/TR-909/SP/samples/rim.wav                                             | public-domain-like (oramics/sampled) |
| breaks      | amen.wav       | https://raw.githubusercontent.com/schollz/amen/main/samples/amenbreak_bpm136.wav                            | MIT (schollz/amen) |

## Notes

- **triphop_kit** is the *TR-909 SP* set from [oramics/sampled](https://oramics.github.io/sampled/DM/TR-909/SP/):
  a 909 kit recorded through an E-mu SP-1200, then re-sampled. oramics/sampled states
  "public domain or similar", but this kit carries no explicit per-kit licence (the
  upstream is a free F9 Audio 909 pack). Treat as royalty-free; the repo is
  non-commercial anyway.
- **breaks/amen.wav** is the full Amen break (`amenbreak_bpm136.wav`, 136 BPM) from
  [schollz/amen](https://github.com/schollz/amen), released under the MIT licence.
  This is a licensed copy, *not* a rip of The Winstons' 1969 recording.
- Some of the source WAVs are 24-bit with a short trailing packet that makes ffmpeg
  print `Invalid PCM packet`; it is harmless (verified bit-identical) and disappears
  after `python -m fftechno samples` normalises them.
