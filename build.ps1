# build.ps1 - build the ffmpeg_techno track using ffmpeg only (no Python).
#
#   Techno beat + granular robotic growl.
#
# Pipeline: render 5 stems -> mix + sidechain duck -> master (2-pass linear loudnorm).
# Run from anywhere:  pwsh -File build.ps1

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

New-Item -ItemType Directory -Force -Path 'output/stems','output/logs' | Out-Null

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "ffmpeg not found on PATH."
}

$stems = @('kick','clap','hat','ohat','perc','bass','growl')
foreach ($s in $stems) {
    Write-Host "Rendering stem: $s"
    ffmpeg -hide_banner -v error -filter_complex_script "filters/$s.txt" `
        -map "[out]" -c:a pcm_f32le "output/stems/$s.wav" -y
    if ($LASTEXITCODE -ne 0) { throw "render of stem '$s' failed (exit $LASTEXITCODE)" }
}

Write-Host "Mixing stems -> output/mix_pre.wav"
ffmpeg -hide_banner -v error `
    -i output/stems/kick.wav -i output/stems/clap.wav -i output/stems/hat.wav `
    -i output/stems/ohat.wav -i output/stems/perc.wav `
    -i output/stems/bass.wav -i output/stems/growl.wav `
    -filter_complex_script filters/mix.txt -map "[out]" -c:a pcm_f32le output/mix_pre.wav -y
if ($LASTEXITCODE -ne 0) { throw "mix failed (exit $LASTEXITCODE)" }

Write-Host "Mastering -> output/techno.wav"
ffmpeg -hide_banner -v error -i output/mix_pre.wav `
    -filter_complex_script filters/master.txt -map "[out]" -c:a pcm_s16le output/techno.wav -y
if ($LASTEXITCODE -ne 0) { throw "master failed (exit $LASTEXITCODE)" }

Write-Host "Done -> output/techno.wav"
