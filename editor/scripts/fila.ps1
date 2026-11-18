# Renderiza (e comprime pra upload) todo roteiro que tem voz.mp3 mas ainda não tem vídeo em <CLIPPER_GTA6_HOME>\edits
# Uso: powershell -File scripts\fila.ps1
$ErrorActionPreference = 'Continue'
$casa = if ($env:CLIPPER_GTA6_HOME) { $env:CLIPPER_GTA6_HOME } else { Join-Path $HOME 'clipper-gta6' }
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:npm_config_cache = (Join-Path $casa 'npm-cache')
$env:TEMP = (Join-Path $casa 'tmp'); $env:TMP = $env:TEMP
$up = (Join-Path $casa 'upload'); New-Item -ItemType Directory -Force $up | Out-Null
foreach ($d in Get-ChildItem 'roteiros' -Directory) {
  $n = $d.Name
  if (-not (Test-Path "$($d.FullName)\voz.mp3")) { continue }
  $mp4 = (Join-Path $casa "edits\$n.mp4")
  if (-not (Test-Path $mp4)) {
    "=== render $n"
    node scripts/render.mjs $n 2>&1 | Select-String 'palavras|Pronto|rror'
  }
  $u = "$up\$n.mp4"
  if ((Test-Path $mp4) -and -not (Test-Path $u)) {
    if ((Get-Item $mp4).Length -lt 9.5MB) { Copy-Item $mp4 $u }
    else {
      $dur = [double](ffprobe -v error -show_entries format=duration -of csv=p=0 $mp4)
      $vk = [math]::Min(3500, [math]::Floor(9.2 * 8192 / $dur - 128))
      ffmpeg -v error -y -i $mp4 -c:v libx264 -preset slow -b:v "${vk}k" -maxrate "${vk}k" -bufsize "$($vk*2)k" -c:a aac -b:a 128k -movflags +faststart $u
    }
    "upload pronto: $n ($([math]::Round((Get-Item $u).Length/1MB,1)) MB)"
  }
}
"FILA OK"
