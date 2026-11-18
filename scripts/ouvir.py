"""Passos 1 e 2: baixa só o áudio da live, escuta tudo no computador e separa em blocos de 12 minutos.

Cada bloco vira um .txt com a fala e duas marcas:
  [ALTO +11dB]   o streamer ficou bem mais alto que o normal daquele trecho (grito, surto)
  [CHAT 3.4x]    no replay do YouTube, o chat andou 3,4 vezes mais rápido que o normal
"""
import json
import time
import wave
from pathlib import Path

import numpy as np

from comum import (BLOCO_MIN, TRABALHO, gravar_json, hms, ler_json, rodar, slug, ytdlp)


# ---------------------------------------------------------------- download
def baixar(url):
    print(f"\n[1/4] Lendo a live: {url}")
    import subprocess
    meta = json.loads(subprocess.run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", url],
                                     check=True, capture_output=True, text=True).stdout)
    nome = slug(f"{meta.get('uploader') or meta.get('channel') or 'live'}-{meta.get('title', '')}")
    pasta = TRABALHO / nome
    pasta.mkdir(parents=True, exist_ok=True)
    info = {k: meta.get(k) for k in ("id", "title", "uploader", "channel", "duration", "view_count",
                                     "webpage_url", "extractor_key", "was_live", "live_status")}
    info["url"] = url
    gravar_json(pasta / "info.json", info)
    print(f"      {info['title']}  |  {info.get('uploader')}  |  {hms(info.get('duration') or 0)}")

    if not list(pasta.glob("audio.*")):
        print("      baixando só o áudio (uma live de 4h fica com algumas centenas de MB)…")
        rodar(ytdlp() + ["-f", "ba/b", "-x", "--no-playlist", "--no-warnings",
                         "-o", str(pasta / "audio.%(ext)s"), url])
    if (info.get("extractor_key") or "").lower().startswith("youtube") and not (pasta / "chat.feito").exists():
        print("      tentando o replay do chat (só existe em live que passou no YouTube)…")
        try:
            rodar(ytdlp() + ["--skip-download", "--write-subs", "--sub-langs", "live_chat", "--no-warnings",
                             "-o", str(pasta / "chat"), url], timeout=1200)
        except Exception as e:  # sem chat não é erro: só não tem a marca [CHAT]
            print(f"      sem replay de chat ({type(e).__name__})")
        (pasta / "chat.feito").write_text("ok")
    return pasta


def wav16k(pasta):
    w = pasta / "audio16k.wav"
    if not w.exists():
        audio = next(p for p in pasta.glob("audio.*"))
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000", w])
    return w


# ---------------------------------------------------------------- transcrição
def transcrever(pasta, modelo="base", idioma=None):
    saida = pasta / "transcricao.json"
    if saida.exists():
        return ler_json(saida)
    from faster_whisper import WhisperModel
    w = wav16k(pasta)
    dur = (pasta / "info.json").exists() and (ler_json(pasta / "info.json", {}).get("duration") or 0)
    print(f"\n[2/4] Escutando a live inteira aqui no computador (modelo {modelo})…")
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    # escuta em pedaços de 20 min: uma live de 6h inteira não cabe na memória de uma vez.
    # cada pedaço pronto fica salvo em parcial.json, então dá pra continuar de onde parou.
    PEDACO = 20 * 60
    parcial = ler_json(pasta / "parcial.json", {"idioma": idioma, "feito": 0, "segmentos": []})
    out, idioma = parcial["segmentos"], parcial["idioma"] or idioma
    t0 = time.time()
    with wave.open(str(w)) as f:
        sr, total = f.getframerate(), f.getnframes() / f.getframerate()
        ini = parcial["feito"]
        while ini < total:
            f.setpos(int(ini * sr))
            a = np.frombuffer(f.readframes(PEDACO * sr), dtype=np.int16).astype(np.float32) / 32768
            segs, inf = m.transcribe(a, language=idioma, vad_filter=True, beam_size=1,
                                     condition_on_previous_text=False)
            for s in segs:
                out.append([round(ini + s.start, 2), round(ini + s.end, 2), s.text.strip()])
            idioma = idioma or inf.language
            ini += PEDACO
            gravar_json(pasta / "parcial.json", {"idioma": idioma, "feito": ini, "segmentos": out})
            pct = f" ({min(100, 100 * ini / (dur or total)):.0f}%)"
            print(f"      {hms(min(ini, total))}{pct} escutado em {time.time() - t0:.0f}s", flush=True)
    dados = {"idioma": idioma, "segmentos": out}
    gravar_json(saida, dados)
    (pasta / "parcial.json").unlink(missing_ok=True)
    return dados


# ---------------------------------------------------------------- picos de volume
def picos_de_volume(pasta):
    saida = pasta / "volume.json"
    if saida.exists():
        return ler_json(saida)
    partes = []  # volume de cada segundo, lido 10 min por vez (o áudio inteiro não cabe na memória)
    with wave.open(str(wav16k(pasta))) as f:
        sr = f.getframerate()
        while True:
            a = np.frombuffer(f.readframes(600 * sr), dtype=np.int16).astype(np.float32)
            s = len(a) // sr
            if not s:
                break
            partes.append(np.sqrt(np.mean(a[: s * sr].reshape(s, sr) ** 2, axis=1) + 1e-6))
    rms = np.concatenate(partes)
    seg = len(rms)
    db = 20 * np.log10(rms / 32768 + 1e-9)
    fala = db > np.percentile(db, 20)                       # ignora silêncio no cálculo da base
    base = np.zeros_like(db)
    for i in range(0, seg, 60):                             # "normal" = mediana dos 5 min em volta
        j0, j1 = max(0, i - 150), min(seg, i + 150)
        janela = db[j0:j1][fala[j0:j1]]
        base[i:i + 60] = np.median(janela) if len(janela) else np.median(db)
    excesso = db - base
    corte = max(8.0, float(np.percentile(excesso, 98)))
    picos = [[int(i), round(float(excesso[i]), 1)] for i in np.where(excesso >= corte)[0]]
    gravar_json(saida, picos)
    return picos


# ---------------------------------------------------------------- velocidade do chat
def picos_do_chat(pasta):
    arq = next(iter(pasta.glob("chat*.live_chat.json")), None)
    if not arq:
        return []
    tempos = []
    for linha in arq.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            ms = json.loads(linha)["replayChatItemAction"]["videoOffsetTimeMsec"]
            tempos.append(int(ms) / 1000)
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
    if len(tempos) < 50:
        return []
    caixas = np.bincount((np.array(tempos) // 10).astype(int))   # mensagens a cada 10 s
    picos = []
    for i, c in enumerate(caixas):
        viz = caixas[max(0, i - 30): i + 30]
        normal = max(1.0, float(np.median(viz)))
        if c >= 8 and c / normal >= 2.5:
            picos.append([i * 10, round(c / normal, 1)])
    return picos


# ---------------------------------------------------------------- trechos quentes (economiza leitura)
def quentes(pasta, trans, volume, chat=(), maximo=8, antes=40, depois=30):
    """Em vez de ler a live inteira, junta só a fala em volta dos picos de grito/chat.
    Grava quentes.txt (mesmo formato de tempo dos blocos) e devolve quantos trechos achou."""
    pontos = sorted({s: e for s, e in volume}.items())
    pontos += [(int(c), 10.0 * r) for c, r in chat]
    pontos.sort()
    grupos = []
    for s, e in pontos:  # picos a menos de 20 s um do outro = mesmo momento
        if grupos and s - grupos[-1]["fim"] <= 20:
            g = grupos[-1]
            g["fim"], g["max"], g["n"] = s, max(g["max"], e), g["n"] + 1
        else:
            grupos.append({"ini": s, "fim": s, "max": e, "n": 1})
    for g in grupos:
        g["nota"] = g["max"] * (1 + min(g["n"], 10) / 5)
    top = sorted(sorted(grupos, key=lambda g: -g["nota"])[:maximo], key=lambda g: g["ini"])
    vol = dict((s, e) for s, e in volume)
    saida = [f"# TRECHOS QUENTES — {len(top)} momentos de grito/surto (só a fala em volta)",
             "# Escreva os momentos escolhidos em: momentos/bloco_01.json", ""]
    for k, g in enumerate(top, 1):
        a, b = g["ini"] - antes, g["fim"] + depois
        saida.append(f"## {k}. pico em {hms(g['ini'])} (+{g['max']:.0f}dB, {g['n']}s alto)")
        for s, e, t in trans["segmentos"]:
            if a <= s <= b:
                alto = max((vol.get(x, 0) for x in range(int(s), int(e) + 1)), default=0)
                saida.append(f"[{hms(s)}] {t}" + (f"  [ALTO +{alto:.0f}dB]" if alto else ""))
        saida.append("")
    (pasta / "quentes.txt").write_text("\n".join(saida), encoding="utf-8")
    return len(top)


# ---------------------------------------------------------------- blocos de 12 min
def blocos(pasta, trans, volume, chat):
    pb = pasta / "blocos"
    pb.mkdir(exist_ok=True)
    (pasta / "momentos").mkdir(exist_ok=True)
    vol = dict((s, e) for s, e in volume)
    segs = trans["segmentos"]
    fim = segs[-1][1] if segs else 0
    passo = BLOCO_MIN * 60
    n = 0
    for k, ini in enumerate(range(0, int(fim) + 1, passo), start=1):
        linhas = []
        for s, e, t in segs:
            if not (ini <= s < ini + passo):
                continue
            marca = ""
            alto = max((vol.get(x, 0) for x in range(int(s), int(e) + 1)), default=0)
            if alto:
                marca += f"  [ALTO +{alto:.0f}dB]"
            ch = max((r for c, r in chat if s - 10 <= c <= e), default=0)
            if ch:
                marca += f"  [CHAT {ch}x]"
            linhas.append(f"[{hms(s)}] {t}{marca}")
        if not linhas:
            continue
        n += 1
        cab = (f"# BLOCO {k:02d} — de {hms(ini)} a {hms(ini + passo)}\n"
               f"# Escreva os momentos deste bloco em: momentos/bloco_{k:02d}.json\n\n")
        (pb / f"bloco_{k:02d}.txt").write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return n


def preparar(url, modelo="base", idioma=None):
    pasta = baixar(url)
    trans = transcrever(pasta, modelo, idioma)
    print("\n[2/4] Marcando onde o streamer ficou alto e onde o chat acelerou…")
    volume = picos_de_volume(pasta)
    chat = picos_do_chat(pasta)
    n = blocos(pasta, trans, volume, chat)
    print(f"      {len(volume)} segundos de grito/surto, {len(chat)} picos de chat")
    print(f"\nPRONTO PRA ESCOLHER: {n} blocos em {pasta / 'blocos'}")
    print(f"Próximo: ler cada bloco e escrever {pasta / 'momentos'}/bloco_NN.json")
    return pasta
