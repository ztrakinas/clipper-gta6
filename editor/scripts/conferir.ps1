# Confere se o número de palavras do whisper bate com o roteiro (sincronia da legenda)
param([string[]]$nomes)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Set-Location (Split-Path $PSScriptRoot -Parent)
foreach ($n in $nomes) {
  $t = (node scripts/render.mjs $n --texto) -split '\s+' | Where-Object { $_ }
  $vj = "roteiros\$n\voz.json"
  if (Test-Path $vj) {
    $w = ((Get-Content $vj -Raw -Encoding UTF8 | ConvertFrom-Json).characters -join '' -split '\s+' | Where-Object { $_ }).Count
    $ok = if ($w -eq $t.Count) { 'OK' } else { "DIFERENTE ($($w - $t.Count))" }
    "$n roteiro=$($t.Count) whisper=$w $ok"
  } else { "$n sem voz.json" }
}
