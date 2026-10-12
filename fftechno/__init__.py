"""fftechno - build a hardgroove techno track with ffmpeg and a dancing-girl video.

The audio is synthesized entirely by ffmpeg (every sound is an ``aevalsrc``
expression or a filter graph under ``filters/``); the voice uses ffmpeg's built-in
``flite`` filter; the video is an edge-detected, beat-locked dancing girl matted
with RVM. This package only orchestrates the ffmpeg/``vspipe`` invocations.

Entry point::

    python -m fftechno audio      # stems -> mix -> master  (output/techno.wav)
    python -m fftechno girl       # build the B/W dancing-girl loop
    python -m fftechno video      # render + mux the dancing-girl video
    python -m fftechno all        # all of the above
    python -m fftechno boost 2.0  # re-level the final MP4s
"""

__version__ = "0.2.0"
