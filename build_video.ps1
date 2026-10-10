# build_video.ps1 - combine the VapourSynth visualizer with the techno track.
#
#   visualizer.vpy (VapourSynth, YUV420P8 y4m)  ->  ffmpeg (H.264 + AAC)  ->  MP4
#
# Video is drawn by VapourSynth; ffmpeg muxes the audio and encodes.
# Requires the local venv created with:  python -m venv .venv ; pip install vapoursynth numpy
# Run:  pwsh -File build_video.ps1

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$vspipe = ".venv\Scripts\vspipe.exe"
if (-not (Test-Path $vspipe)) { throw "vspipe not found at $vspipe - create the venv first." }
if (-not (Test-Path "output/techno.wav")) { throw "output/techno.wav missing - run build.ps1 first." }

New-Item -ItemType Directory -Force -Path output/logs | Out-Null

Write-Host "Rendering visualizer + encoding MP4 (this takes a few minutes)..."

# vspipe streams y4m to stdout; ffmpeg reads it, muxes the techno master and encodes.
& $vspipe -c y4m visualizer.vpy - 2> output/logs/vspipe.log |
    ffmpeg -hide_banner -y -f yuv4mpegpipe -i - -i output/techno.wav `
        -c:v libx264 -preset slow -crf 20 -tune film -pix_fmt yuv420p `
        -c:a aac -b:a 192k -shortest -movflags +faststart `
        output/techno_visualizer.mp4 2> output/logs/ffmpeg_video.log

if ($LASTEXITCODE -ne 0) { throw "video encode failed (exit $LASTEXITCODE)" }
Write-Host "Master done -> output/techno_visualizer.mp4"

Write-Host "Making web preview (720p)..."
ffmpeg -hide_banner -y -i output/techno_visualizer.mp4 `
    -vf scale=1280:720 -c:v libx264 -preset medium -crf 22 `
    -c:a aac -b:a 160k -movflags +faststart `
    output/techno_visualizer_720p.mp4 2> output/logs/ffmpeg_preview.log
if ($LASTEXITCODE -ne 0) { throw "preview encode failed (exit $LASTEXITCODE)" }
Write-Host "Done -> output/techno_visualizer.mp4 and output/techno_visualizer_720p.mp4"
