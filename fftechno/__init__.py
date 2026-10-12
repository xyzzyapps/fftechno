"""fftechno - build techno tracks with ffmpeg and a dancing-girl video.

Each track is a folder under ``songs/`` holding its arrangement and instrument
markdown (``song.md`` / ``sounds.md``), its TTS voice and lyric timings
(``vocals.md``) and its video settings (``video.md``). The code is generic:
``fftechno.song.Song`` exposes a track, and ``fftechno.looks`` supplies the
style-specific video looks, so nothing here is tied to a particular song.

Entry point::

    python -m fftechno audio --song basement    # stems -> mix -> master
    python -m fftechno girl  --song basement     # build the dancing-girl picture
    python -m fftechno video --song basement     # render + mux the video
    python -m fftechno all   --song basement     # all of the above
    python -m fftechno boost 2.0 --song basement # re-level the final MP4s
"""

__version__ = "0.2.0"
