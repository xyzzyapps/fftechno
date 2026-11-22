"""Render the ffmpeg-as-a-DAW cheat sheet PNG (social-media card).

One-off asset generator: draws a 1080x1350 dark card with the synthesis,
sequencing, filter, sampler and mastering techniques this project uses.
Uses the Windows system fonts (Times New Roman for the title, Consolas for
code) and Pillow, which is a render-only dependency.

    .venv\\Scripts\\python docs\\make_cheatsheet.py
    -> docs/ffmpeg_cheatsheet.png
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "ffmpeg_cheatsheet.png"
FONTS = Path("C:/Windows/Fonts")

W, H = 1080, 1350
BG = (10, 13, 18)
FG = (201, 209, 217)
LABEL = (110, 118, 129)
DIM = (139, 148, 158)
ACCENT = (126, 231, 135)
RULE = (31, 38, 48)
BORDER = (26, 32, 42)

TITLE = ImageFont.truetype(str(FONTS / "timesbd.ttf"), 78)
SUBTITLE = ImageFont.truetype(str(FONTS / "consola.ttf"), 22)
HEADER = ImageFont.truetype(str(FONTS / "consolab.ttf"), 24)
BODY = ImageFont.truetype(str(FONTS / "consola.ttf"), 17)
FOOT = ImageFont.truetype(str(FONTS / "consola.ttf"), 16)

X1, X2 = 40, 560
COLW = 480
LABW = 100
LINE = 24


def wrap(draw, text, font, max_w):
    """Greedy wrap, preferring spaces then : = , as break points."""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > max_w and cur:
            cut = max(cur.rfind(" "), cur.rfind(":"), cur.rfind("="), cur.rfind(","))
            if cut > 0:
                lines.append(cur[: cut + 1].rstrip())
                cur = cur[cut + 1 :].lstrip() + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def section(draw, x, y, title, rows, width=COLW):
    """Draw one titled section of label/code rows and return the next y."""
    draw.text((x, y), title, font=HEADER, fill=ACCENT)
    y += 38
    for label, code in rows:
        draw.text((x, y), label, font=BODY, fill=LABEL)
        for line in wrap(draw, code, BODY, width - LABW):
            draw.text((x + LABW, y), line, font=BODY, fill=FG)
            y += LINE
    return y + 14


def main():
    """Render the complete card to ``docs/ffmpeg_cheatsheet.png``."""
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle([22, 22, W - 23, H - 23], outline=BORDER)

    draw.text((50, 58), "FFMPEG AS A DAW", font=TITLE, fill=(236, 236, 236))
    draw.text(
        (52, 150),
        "synthesis · sequencing · filters · sampler · mastering",
        font=SUBTITLE,
        fill=DIM,
    )
    draw.line([50, 196, W - 50, 196], fill=RULE, width=1)

    col1 = [
        (
            "SYNTH · aevalsrc",
            [
                ("sine", "sin(2*PI*f*t)"),
                ("saw", "mod(f*t,1)*2-1"),
                ("square", "gt(mod(f*t,1),0.5)*2-1"),
                ("noise", "random(0)*2-1"),
                ("env", "exp(-k*mod(t,step))"),
                ("retrigger", "mod(t,bar) / mod(t,step)"),
                ("vibrato", "sin(2*PI*f*t+d*sin(2*PI*vf*t))"),
                ("FM", "sin(2*PI*fc*t+I*sin(2*PI*fm*t))"),
                ("detune", "saw(f*t)+det*saw(f*tune*t)"),
            ],
        ),
        (
            "SEQUENCING",
            [
                ("bar", "240/bpm"),
                ("step", "bar/16"),
                ("grid", "floor(mod(t,bar)/step)"),
                ("ladder", "if_steps(notes; grid; def)"),
                ("gate", "if_steps(gates; grid; 0)"),
                ("velocity", "if_steps(vel; grid; 1)"),
                ("ghost", "a low value in the vel list"),
                ("swing", "2*floor(mod(t,bar)/(2*step))"),
                ("", "+gt(mod(mod(t,bar),2*step)/(2*step),s)"),
                ("humanize", "0.5+0.5*sin(floor(t/step)*2.399963)"),
            ],
        ),
        (
            "DETERMINISM",
            [
                ("random(i)", "per-sample PRNG, i = 0..9"),
                ("st / ld", "ten scratch slots"),
                ("repeat", "same build -> same bytes"),
            ],
        ),
    ]
    col2 = [
        (
            "FILTERS",
            [
                ("filter", "lowpass=f=..:t=q:w=.."),
                ("EQ", "equalizer=f=..:t=q|h|s:g=.."),
                ("drive", "asoftclip=type=tanh:threshold=.."),
                ("crush", "acrusher=bits=..:mix=.."),
                ("sub", "asubboost=cutoff=..:boost=.."),
                ("delay", "aecho=in:out:taps:decays"),
                ("reverb", "afir=dry=0:wet=1  (IR wav)"),
                ("duck", "sidechaincompress=thr=..:ratio=.."),
                ("glue", "acompressor=threshold=..:ratio=.."),
                ("limit", "alimiter=limit=0.88:level=disabled"),
                ("loudness", "loudnorm=I=-13:TP=-1:LRA=11"),
                ("width", "extrastereo=m=1.3"),
                ("bus", "asplit + amix=inputs=N:normalize=0"),
                ("automate", "volume=volume='..':eval=frame"),
            ],
        ),
        (
            "SAMPLER",
            [
                ("source", "amovie=sample.wav"),
                ("pitch", "asetrate=48000*ratio,aresample=48000"),
                ("tempo", "atempo=1.25  (keeps pitch)"),
                ("place", "adelay=1234:all=1"),
                ("trim", "atrim=0:5.714"),
                ("loop", "apad=whole_len=N,aloop=loop=-1:size=N"),
            ],
        ),
        (
            "MASTER",
            [
                ("1", "loudnorm ... print_format=json"),
                ("2", "loudnorm measured_I=..:linear=true"),
                ("", "alimiter -> aresample -> dither"),
                ("out", "pcm_s16le 48 kHz stereo"),
            ],
        ),
    ]

    y1 = 225
    for title, rows in col1:
        y1 = section(draw, X1, y1, title, rows)
    y2 = 225
    for title, rows in col2:
        y2 = section(draw, X2, y2, title, rows)

    run_y = max(y1, y2) + 10
    section(
        draw,
        X1,
        run_y,
        "RUN",
        [
            ("render", 'ffmpeg -/filter_complex graph.txt -map "[out]" out.wav'),
            ("source", "ffmpeg -f lavfi -i \"aevalsrc='..':s=48000:d=240\""),
        ],
        width=W - 100,
    )
    extra_y = run_y + 38 + 2 * LINE + 14
    section(
        draw,
        X1,
        extra_y,
        "VIDEO",
        [
            ("pipe", "vspipe -c y4m clip.vpy - | ffmpeg -i -"),
            ("encode", "libx264 -crf 18 -pix_fmt yuv420p"),
        ],
    )
    section(
        draw,
        X2,
        extra_y,
        "CHECK",
        [
            ("levels", "astats · ebur128=peak=true"),
            ("probe", "ffprobe -show_entries stream=codec_name"),
        ],
    )

    draw.line([50, 1266, W - 50, 1266], fill=RULE, width=1)
    draw.text((50, 1284), "no DAW · no plugins · 100% ffmpeg", font=FOOT, fill=LABEL)
    right = "github.com/xyzzyapps/fftechno"
    draw.text(
        (W - 50 - draw.textlength(right, font=FOOT), 1284),
        right,
        font=FOOT,
        fill=LABEL,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, "PNG")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
