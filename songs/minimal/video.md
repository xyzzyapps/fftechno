# video - minimal

The song-specific visual settings read by `python -m fftechno girl|video`.

The **source** is a still photo (no dancing-girl loop) and the **effects** are an
ordered chain: `squares` draws white outline squares that vibrate with the
instruments, `grain` adds film grain. Everything else has a default.

The output is **horizontal** (`1920x1080`, the default) to match the 16:9 photo, and
the photo **fills** the frame, so there are no black bars.

source: Gemini_Generated_Image_51i77351i77351i7.png
look: photo
effects: squares, grain

## Parameters

Per-look and per-effect overrides (the first column is the look *or* effect name).
Sizes are in low-res pixels - half the output size, so 960x540 here.

| name    | key         | value |
|---------|-------------|-------|
| photo   | framing     | fill  |
| photo   | focus       | 0.324 |
| photo   | shift_x     | -50   |
| photo   | shift_y     | -60   |
| squares | halves      | 245\|217\|133\|161\|189\|105 |
| squares | thickness   | 2     |
| squares | circles     | rim   |
| squares | skip        | vox\|blow |
| squares | swell       | 0.2   |
| squares | drift       | 30    |
| squares | rotate      | 0.35  |
| squares | knock       | 16    |
| squares | level       | 1.0   |
| squares | presence    | 3.0   |
| squares | decay       | 0.22  |
| grain   | amount      | 0.035 |
