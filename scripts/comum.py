"""Coisas que todos os passos do clipper usam: pastas, tempo e chamadas de programas."""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

# Pasta de trabalho: ~/clipper-gta6 por padrão. Pra usar outro disco, defina CLIPPER_GTA6_HOME.
CASA = Path(os.environ.get("CLIPPER_GTA6_HOME", str(Path.home() / "clipper-gta6")))
# modelos de escuta e cache de pacotes também ficam no D (o C não tem espaço)
os.environ.setdefault("HF_HOME", str(CASA / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("PIP_CACHE_DIR", str(CASA / "pip-cache"))
TRABALHO = CASA / "trabalho"   # áudio, transcrição e trechos de cada live
CORTES = CASA / "cortes"       # os vídeos prontos pra postar
MODELOS = CASA / "modelos"     # o detector de rosto (baixado no setup)
YUNET = MODELOS / "face_detection_yunet_2023mar.onnx"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")
BLOCO_MIN = 12  # a IA lê a transcrição 12 minutos por vez


def slug(texto, limite=60):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t[:limite].strip("-") or "live"


def hms(seg):
    seg = max(0, int(round(seg)))
    return f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}"


def segundos(valor):
    """Aceita 3723, '3723', '1:02:03' ou '62:03'."""
    if isinstance(valor, (int, float)):
        return float(valor)
    partes = [float(p) for p in str(valor).strip().split(":")]
    total = 0.0
    for p in partes:
        total = total * 60 + p
    return total


def rodar(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd[:6]), "…" if len(cmd) > 6 else "", flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def tem(programa):
    return shutil.which(programa) is not None


def ytdlp():
    """yt-dlp do ambiente do clipper (sempre atualizado pelo setup) ou o do sistema."""
    local = Path(sys.executable).parent / ("yt-dlp.exe" if os.name == "nt" else "yt-dlp")
    cmd = [str(local)] if local.exists() else [sys.executable, "-m", "yt_dlp"]
    if tem("deno") or tem("node"):  # o YouTube precisa de um JavaScript pra liberar todos os formatos
        cmd += ["--js-runtimes", "deno" if tem("deno") else "node"]
    return cmd


def ler_json(caminho, padrao=None):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def gravar_json(caminho, dados):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def pasta_da_live(nome):
    """Aceita o nome da pasta, um pedaço dele ou o link original."""
    if (TRABALHO / nome).is_dir():
        return TRABALHO / nome
    for p in sorted(TRABALHO.glob("*")):
        info = ler_json(p / "info.json", {})
        if nome in (info.get("url"), info.get("webpage_url")) or nome.lower() in p.name:
            return p
    sys.exit(f"Não achei a live '{nome}' em {TRABALHO}. Rode antes: clip.py preparar LINK")
