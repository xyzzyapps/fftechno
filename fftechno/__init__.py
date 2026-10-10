"""fftechno - build a hardgroove techno track with ffmpeg and an ASCII visual.

The audio is synthesized entirely by ffmpeg (every sound is an ``aevalsrc``
expression or a filter graph under ``filters/``); this package only orchestrates
the ffmpeg/``vspipe``/``espeak-ng`` invocations.

Entry point::

    python -m fftechno audio      # stems -> mix -> master  (output/techno.wav)
    python -m fftechno video      # render + mux the ASCII video
    python -m fftechno all        # both
    python -m fftechno boost 2.0  # re-level the final MP4s
"""

__version__ = "1.0.0"
