# make_vox.ps1 - female espeak-ng vocals (multiple phrases), pitched, reverbed,
# placed at section hits and padded to the track length. -> output/stems/vox.wav
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$esp  = "tools\espeak-ng\eSpeak NG\espeak-ng.exe"
$data = "tools\espeak-ng\eSpeak NG\espeak-ng-data"
if (-not (Test-Path $esp)) { throw "espeak-ng not found at $esp" }

New-Item -ItemType Directory -Force -Path output/logs,output/stems | Out-Null

$phrases = @(
    "speak to me", "come on", "feel it", "hard groove", "let go",
    "trust me", "lock in", "take me higher", "hands up"
)

Write-Host "espeak-ng: female vocals ($($phrases.Count) phrases)"
$inputs = @()
for ($i = 0; $i -lt $phrases.Count; $i++) {
    $wav = "output/logs/vox_$i.wav"
    & $esp --path $data -v en+f4 -w $wav -s 132 -p 70 $phrases[$i]
    if ($LASTEXITCODE -ne 0) { throw "espeak failed on '$($phrases[$i])'" }
    $inputs += @("-i", $wav)
}

Write-Host "processing + placing vocals -> output/stems/vox.wav"
ffmpeg -hide_banner -v error -y @inputs `
  -filter_complex_script filters/vox.txt -map "[out]" -c:a pcm_f32le output/stems/vox.wav
if ($LASTEXITCODE -ne 0) { throw "vox processing failed ($LASTEXITCODE)" }
Write-Host "Done -> output/stems/vox.wav"
