"""Gera voz.json (tempo de cada palavra) a partir de um mp3, com o faster-whisper local.

Uso: python scripts/tempos.py <audio.mp3> <saida.json> [texto do roteiro]
O JSON sai no mesmo formato de "alignment" da ElevenLabs, então o render.mjs usa direto.
"""
import json
import os
import sys

CASA = os.environ.get("CLIPPER_GTA6_HOME", os.path.join(os.path.expanduser("~"), "clipper-gta6"))
os.environ.setdefault("HF_HOME", os.path.join(CASA, "huggingface"))
from faster_whisper import WhisperModel  # noqa: E402

audio, saida = sys.argv[1], sys.argv[2]
texto = sys.argv[3] if len(sys.argv) > 3 else None

modelo = WhisperModel("small", device="cpu", compute_type="int8")
segs, _ = modelo.transcribe(audio, language="pt", word_timestamps=True, initial_prompt=texto, vad_filter=False)

chars, ini, fim, palavras = [], [], [], []
for s in segs:
    for w in s.words:
        p = w.word.strip()
        if not p:
            continue
        palavras.append(f"{p}[{w.start:.2f}-{w.end:.2f}]")
        passo = (w.end - w.start) / max(1, len(p))
        for i, ch in enumerate(p):
            chars.append(ch)
            ini.append(round(w.start + i * passo, 3))
            fim.append(round(w.start + (i + 1) * passo, 3))
        chars.append(" ")
        ini.append(round(w.end, 3))
        fim.append(round(w.end, 3))

with open(saida, "w", encoding="utf-8") as f:
    json.dump({"characters": chars, "character_start_times_seconds": ini, "character_end_times_seconds": fim}, f, ensure_ascii=False)

print(f"{len(palavras)} palavras:", " ".join(palavras))
