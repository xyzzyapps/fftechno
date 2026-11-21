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
| stoner_kit  | kick.wav       | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/kick-01.wav                            | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | snare.wav      | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/snare-01.wav                           | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | snare2.wav     | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/snare-02.wav                           | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | snare3.wav     | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/snare-03.wav                           | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | tom1.wav       | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/tom-01.wav                             | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | tom2.wav       | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/tom-02.wav                             | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | tom3.wav       | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/tom-03.wav                             | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | hat-closed.wav | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/hihat-closed.wav                       | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | hat-open.wav   | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/hihat-open.wav                         | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | ride.wav       | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/ride-01.wav                            | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | crash.wav      | https://oramics.github.io/sampled/DRUMS/pearl-master-studio/samples/crash-01.wav                           | CC-BY 3.0 (Pearl Master Studio by enoe / oramics) |
| stoner_kit  | bass.wav       | https://raw.githubusercontent.com/freepats/electric-bass-YR/main/samples/pick/C.flac                       | CC0 (FreePats electric-bass-YR) |
| stoner_kit  | gtr_c2.wav     | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-dist1/main/samples/bridge/C2_s1_02.flac     | CC0 (FreePats electric-guitar-FSBS-dist1) |
| stoner_kit  | gtr_c3.wav     | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-dist1/main/samples/bridge/C3_s2_02.flac     | CC0 (FreePats electric-guitar-FSBS-dist1) |
| stoner_kit  | gtr_f2.wav     | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-dist1/main/samples/bridge/F2_s1_01.flac     | CC0 (FreePats electric-guitar-FSBS-dist1) |
| stoner_kit  | gtr_g3.wav     | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-dist1/main/samples/bridge/G3_s4_01.flac     | CC0 (FreePats electric-guitar-FSBS-dist1) |
| stoner_kit  | bass_e2.wav    | https://raw.githubusercontent.com/freepats/electric-bass-YR/main/samples/pick/E2.flac                       | CC0 (FreePats electric-bass-YR) |
| stoner_kit  | di_c2.wav      | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-direct/main/samples/bridge/C2_s1_02.wav       | CC0 (FreePats electric-guitar-FSBS-direct) |
| stoner_kit  | di_e2.wav      | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-direct/main/samples/bridge/E2_s1_02.wav       | CC0 (FreePats electric-guitar-FSBS-direct) |
| stoner_kit  | di_a2.wav      | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-direct/main/samples/bridge/A2_s2_02.wav       | CC0 (FreePats electric-guitar-FSBS-direct) |
| stoner_kit  | di_c3.wav      | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-direct/main/samples/bridge/C3_s2_02.wav       | CC0 (FreePats electric-guitar-FSBS-direct) |
| stoner_kit  | di_g3.wav      | https://raw.githubusercontent.com/freepats/electric-guitar-FSBS-direct/main/samples/bridge/G3_s4_02.wav       | CC0 (FreePats electric-guitar-FSBS-direct) |

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
- **stoner_kit** is a real rock kit: the **Pearl Master Studio** acoustic drums
  (CC-BY 3.0, by enoe, via oramics/sampled) and **FreePats** electric guitar/bass
  (CC0): a pre-distorted Fender guitar (`FSBS-dist1`) and a picked electric bass.
  The guitar and bass sources are FLAC; `fetch` writes the source bytes under the
  local `.wav` name and `prepare` transcodes them to 48 kHz PCM, so the sampler
  always reads a canonical WAV. The Pearl samples are CC-BY, so keep the
  attribution above if the set is redistributed.
