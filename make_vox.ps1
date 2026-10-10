# make_vox.ps1 - female espeak-ng vocals ("speak to me" + more), pitched, robotic,
# reverbed, placed at section hits and padded to the track length. -> stems/vox.wav
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$esp  = "tools\espeak-ng\eSpeak NG\espeak-ng.exe"
$data = "tools\espeak-ng\eSpeak NG\espeak-ng-data"
if (-not (Test-Path $esp)) { throw "espeak-ng not found at $esp" }

New-Item -ItemType Directory -Force -Path output/logs,output/stems | Out-Null

Write-Host "espeak-ng: high, feminine club vocals"
& $esp --path $data -v en+f4 -w output/logs/vox_a.wav -s 132 -p 70 "speak to me"
& $esp --path $data -v en+f4 -w output/logs/vox_b.wav -s 138 -p 72 "come on"
& $esp --path $data -v en+f4 -w output/logs/vox_c.wav -s 132 -p 70 "feel it"
& $esp --path $data -v en+f4 -w output/logs/vox_d.wav -s 132 -p 72 "hard groove"

Write-Host "processing + placing vocals -> output/stems/vox.wav"
ffmpeg -hide_banner -v error -y `
  -i output/logs/vox_a.wav -i output/logs/vox_b.wav `
  -i output/logs/vox_c.wav -i output/logs/vox_d.wav `
  -filter_complex_script filters/vox.txt -map "[out]" -c:a pcm_f32le output/stems/vox.wav
if ($LASTEXITCODE -ne 0) { throw "vox processing failed ($LASTEXITCODE)" }
Write-Host "Done -> output/stems/vox.wav"
