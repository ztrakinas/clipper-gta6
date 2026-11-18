"""Lives que AINDA ESTÃO NO AR — YouTube, Twitch e Kick.

Cada site deixa voltar no tempo de um jeito (testado em 18/11/2026):
  YouTube  a live é dividida em pedaços numerados de ~2 s (".../sq/12345/..."); o player só mostra 15 min,
           mas os pedaços antigos continuam no ar (2 h+). Baixa pedaço por pedaço, em paralelo.
  Twitch   durante a live a Twitch já vai gravando o VOD (que cresce em tempo real). O yt-dlp baixa
           só um trecho dele (--download-sections). Não funciona se o streamer desligou os VODs.
  Kick     o player só volta 30 s, mas a Kick também grava o VOD durante a live: uma lista com a live
           inteira em pedaços de 10 s (0.ts, 1.ts…). Baixa só os pedaços do fim.

aovivo.json guarda onde começou o áudio baixado: tempo 0 da transcrição = esse ponto da live.
"""
import json
import math
import re
import subprocess
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from comum import TRABALHO, gravar_json, hms, ler_json, rodar, slug, ytdlp

YT_AUDIO = "233/234/ba"
YT_VIDEO = "312/311/231/230/229"   # 1080p60, 720p60, 480p… (só imagem)
SQ = re.compile(r"/sq/(\d+)/")
FORMATO = "bv*[height<=1080]+ba/b[height<=1080]/b"


# ---------------------------------------------------------------- utilidades
def site(url):
    u = url.lower()
    return "twitch" if "twitch.tv" in u else "kick" if "kick.com" in u else "youtube"


def meta(url):
    return json.loads(subprocess.run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", url],
                                     check=True, capture_output=True, text=True).stdout)


def link_hls(url, fmt):
    return subprocess.run(ytdlp() + ["-f", fmt, "-g", "--no-warnings", url],
                          check=True, capture_output=True, text=True).stdout.split()[0]


def ler(url):
    return urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "ignore")


def baixar_links(links, destino):
    """Baixa vários pedaços em paralelo e grava tudo junto, na ordem. Devolve quantos falharam."""
    def um(u):
        for t in range(4):
            try:
                return urllib.request.urlopen(u, timeout=30).read()
            except Exception:
                time.sleep(1 + t)
        return b""

    with ThreadPoolExecutor(16) as ex:
        partes = list(ex.map(um, links))
    with open(destino, "wb") as f:
        for p in partes:
            f.write(p)
    return sum(1 for p in partes if not p)


def para_mp4(bruto, destino, so_audio=False):
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", bruto, *(["-vn"] if so_audio else []), "-c", "copy",
           destino])
    bruto.unlink(missing_ok=True)


def cortar_bruto(v, a, desloc, dur, destino):
    entradas = ["-i", v] + (["-i", a] if a else [])
    mapas = ["-map", "0:v:0", "-map", "1:a:0" if a else "0:a:0?"]
    rodar(["ffmpeg", "-y", "-loglevel", "error", *entradas, "-ss", f"{desloc:.2f}", "-t", f"{dur:.2f}",
           *mapas, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k",
           destino])
    v.unlink(missing_ok=True)
    if a:
        a.unlink(missing_ok=True)


# ---------------------------------------------------------------- YouTube: pedaços numerados
def yt_manifesto(url, fmt):
    txt = ler(link_hls(url, fmt))
    segs = [linha for linha in txt.splitlines() if linha.startswith("http")]
    if not segs or not SQ.search(segs[-1]):
        raise RuntimeError("não achei os pedaços numerados dessa live")
    d = re.search(r"#EXTINF:([\d.]+)", txt)
    return segs[-1], int(SQ.search(segs[-1]).group(1)), float(d.group(1)) if d else 2.0


def yt_links(modelo, sq0, sq1):
    atual = SQ.search(modelo).group(1)
    return [modelo.replace(f"/sq/{atual}/", f"/sq/{sq}/") for sq in range(sq0, sq1 + 1)]


def yt_audio(url, minutos, destino):
    modelo, sq_fim, seg = yt_manifesto(url, YT_AUDIO)
    sq_ini = max(0, sq_fim - int(minutos * 60 / seg) + 1)
    bruto = destino.with_name("audio_bruto.mp4")
    faltou = baixar_links(yt_links(modelo, sq_ini, sq_fim), bruto)
    para_mp4(bruto, destino, so_audio=True)
    # Algumas lives (ex.: Davy Jones) só guardam ~8 min no YouTube: já baixa a IMAGEM da janela inteira agora,
    # pra o corte não depender de o pedaço ainda estar no ar depois.
    try:
        vmod = yt_manifesto(url, YT_VIDEO)[0]
        vbruto = destino.with_name("video_bruto.mp4")
        vf = baixar_links(yt_links(vmod, sq_ini, sq_fim), vbruto)
        para_mp4(vbruto, destino.with_name("video_janela.mp4"))
        print(f"      imagem da janela guardada" + (f" ({vf} pedaços falharam)" if vf else ""))
    except Exception as erro:
        print(f"      (não guardei a imagem da janela: {erro})")
    return {"tipo": "youtube", "sq_ini": sq_ini, "sq_fim": sq_fim, "seg": seg}, (sq_fim - sq_ini + 1) * seg, faltou


def yt_trecho(url, av, s, e, destino):
    seg, base = av["seg"], av["sq_ini"]
    sq0, sq1 = base + int(s // seg), base + int(math.ceil(e / seg))
    print(f"      baixando os pedaços {sq0}–{sq1} da live (imagem + som)…")
    v, a = destino.with_name("v_bruto.mp4"), destino.with_name("a_bruto.mp4")
    for tentativa in range(3):  # o YouTube às vezes recusa por alguns segundos: pega manifesto novo e tenta de novo
        f = baixar_links(yt_links(yt_manifesto(url, YT_VIDEO)[0], sq0, sq1), v)
        f += baixar_links(yt_links(yt_manifesto(url, YT_AUDIO)[0], sq0, sq1), a)
        if not f:
            break
        print(f"      atenção: {f} pedaços falharam (tentativa {tentativa + 1}/3)")
        time.sleep(10)
    if f and (not v.exists() or v.stat().st_size == 0):
        raise RuntimeError("esse pedaço da live já saiu do ar no YouTube (a live só guarda ~1 h)")
    cortar_bruto(v, a, s - (sq0 - base) * seg, e - s, destino)


# ---------------------------------------------------------------- Twitch: VOD que está sendo gravado
def twitch_vod(canal_url):
    login = re.search(r"twitch\.tv/([^/?#]+)", canal_url).group(1)
    r = subprocess.run(ytdlp() + ["--flat-playlist", "--playlist-end", "3", "-J", "--no-warnings",
                                  f"https://www.twitch.tv/{login}/videos?filter=archive&sort=time"],
                       capture_output=True, text=True)
    for item in (json.loads(r.stdout or "{}").get("entries") or []):
        vod = f"https://www.twitch.tv/videos/{str(item['id']).lstrip('v')}"
        m = meta(vod)
        fim = (m.get("timestamp") or 0) + (m.get("duration") or 0)
        if time.time() - fim < 15 * 60:  # termina "agora": é o da live atual
            return vod, m
    raise RuntimeError("esse streamer não deixa a Twitch gravar o VOD durante a live (VODs desligados ou só pra inscritos)")


def twitch_audio(canal_url, minutos, destino):
    vod, m = twitch_vod(canal_url)
    dur = float(m["duration"])
    ini = max(0.0, dur - minutos * 60)
    rodar(ytdlp() + ["-f", "audio_only/worst", "--no-warnings", "-q", "--download-sections",
                     f"*{ini:.0f}-{dur:.0f}", "-o", str(destino.with_name("audio_bruto.%(ext)s")), vod])
    bruto = next(destino.parent.glob("audio_bruto.*"))
    para_mp4(bruto, destino, so_audio=True)
    return {"tipo": "twitch", "vod": vod, "ini": ini}, dur - ini, 0


def twitch_trecho(av, s, e, destino):
    a, b = av["ini"] + s, av["ini"] + e
    print(f"      baixando {hms(a)}–{hms(b)} do VOD da Twitch…")
    # o --download-sections do yt-dlp regrava em mpeg2 de baixa qualidade: corta direto com o ffmpeg em H.264
    m3u8 = link_hls(av["vod"], "best[height<=1080]/best")
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.2f}", "-i", m3u8, "-t", f"{b - a:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", destino])


# ---------------------------------------------------------------- Kick: VOD que está sendo gravado
def kick_vod(canal_url):
    login = re.search(r"kick\.com/([^/?#]+)", canal_url).group(1)
    r = subprocess.run(ytdlp() + ["--flat-playlist", "--playlist-end", "3", "-J", "--no-warnings",
                                  f"https://kick.com/{login}/videos"], capture_output=True, text=True)
    for item in (json.loads(r.stdout or "{}").get("entries") or []):
        vod = item["url"].split("#")[0]
        m = meta(vod)
        if m.get("live_status") == "is_live" or m.get("is_live"):
            return vod, m
    raise RuntimeError("não achei o VOD da live atual na Kick")


def kick_pedacos(vod, fmt):
    """Lista (link, início, duração) de todos os pedaços do VOD que está sendo gravado."""
    m3u8 = link_hls(vod, fmt)
    txt, t, out, dur = ler(m3u8), 0.0, [], None
    for linha in txt.splitlines():
        if linha.startswith("#EXTINF:"):
            dur = float(linha[8:].split(",")[0])
        elif linha and not linha.startswith("#") and dur is not None:
            out.append((urllib.parse.urljoin(m3u8, linha), t, dur))
            t += dur
            dur = None
    return out


def kick_baixar(pedacos, a, b, destino):
    sel = [p for p in pedacos if p[1] + p[2] > a and p[1] < b]
    faltou = baixar_links([p[0] for p in sel], destino)
    return sel[0][1], faltou


def kick_audio(canal_url, minutos, destino):
    # PENDENTE: a Kick responde 403 ao baixar os pedaços direto por aqui (testado 18/11). Só a Twitch e o
    # YouTube estão liberados no modo ao vivo; pra Kick, esperar a live acabar e usar `preparar`.
    raise RuntimeError("Kick ao vivo ainda não liberado: espere a live acabar e use o modo normal (preparar)")
    vod, _ = kick_vod(canal_url)
    peds = kick_pedacos(vod, "160p/360p/worst")
    total = peds[-1][1] + peds[-1][2]
    ini = max(0.0, total - minutos * 60)
    bruto = destino.with_name("audio_bruto.ts")
    t0, faltou = kick_baixar(peds, ini, total, bruto)
    para_mp4(bruto, destino, so_audio=True)
    return {"tipo": "kick", "vod": vod, "ini": t0}, total - t0, faltou


def kick_trecho(av, s, e, destino):
    a, b = av["ini"] + s, av["ini"] + e
    print(f"      baixando {hms(a)}–{hms(b)} do VOD da Kick…")
    peds = kick_pedacos(av["vod"], "1080p60/1080p/720p60/720p/best")
    v = destino.with_name("v_bruto.ts")
    t0, faltou = kick_baixar(peds, a, b, v)
    if faltou:
        print(f"      atenção: {faltou} pedaços falharam")
    cortar_bruto(v, None, a - t0, b - a, destino)


# ---------------------------------------------------------------- comandos
def preparar(url, minutos=60, modelo="base", idioma="pt"):
    from ouvir import blocos, picos_de_volume, picos_do_chat, transcrever
    s = site(url)
    print(f"\n[1/4] Lendo a live AO VIVO ({s}): {url}")
    mt = meta(url)
    if not (mt.get("is_live") or mt.get("live_status") == "is_live"):
        print("      essa live não está no ar: usando o modo normal")
        from ouvir import preparar as normal
        return normal(url, modelo, idioma)
    quem = mt.get("uploader") or mt.get("channel") or mt.get("display_id") or "live"
    titulo = mt.get("description") if s == "twitch" else mt.get("title")
    nome = slug(f"{quem}-aovivo-{datetime.now():%d%m-%Hh%M}-{titulo or ''}", 80)
    pasta = TRABALHO / nome
    pasta.mkdir(parents=True, exist_ok=True)

    print(f"      baixando o áudio dos últimos {minutos} min…")
    t0 = time.time()
    fn = {"youtube": yt_audio, "twitch": twitch_audio, "kick": kick_audio}[s]
    av, dur, faltou = fn(url, minutos, pasta / "audio.m4a")
    av["baixado_em"] = datetime.now().isoformat(timespec="seconds")
    gravar_json(pasta / "aovivo.json", av)
    gravar_json(pasta / "info.json", {
        "id": mt.get("id"), "title": titulo or mt.get("title"), "uploader": quem, "channel": mt.get("channel"),
        "duration": dur, "view_count": mt.get("concurrent_view_count"), "webpage_url": mt.get("webpage_url") or url,
        "extractor_key": mt.get("extractor_key"), "live_status": "is_live", "url": url})
    print(f"      {titulo}  |  {quem}  |  {hms(dur)} de áudio em {time.time() - t0:.0f}s"
          + (f" ({faltou} pedaços falharam)" if faltou else ""))
    (pasta / "chat.feito").write_text("ao vivo: sem replay de chat")

    trans = transcrever(pasta, modelo, idioma)
    print("\n[2/4] Marcando onde o streamer ficou alto…")
    volume = picos_de_volume(pasta)
    nb = blocos(pasta, trans, volume, picos_do_chat(pasta))
    print(f"      {len(volume)} segundos de grito/surto")
    print(f"\nPRONTO PRA ESCOLHER: {nb} blocos em {pasta / 'blocos'}")
    print(f"PASTA: {pasta.name}")
    return pasta


def baixar_trecho(pasta, url, s, e, destino):
    """Corte de live aberta: baixa só o pedaço do corte (s e e em segundos da transcrição)."""
    av = ler_json(pasta / "aovivo.json")
    tipo = av.get("tipo", "youtube")
    if tipo == "twitch":
        twitch_trecho(av, s, e, destino)
    elif tipo == "kick":
        kick_trecho(av, s, e, destino)
    else:
        janela = pasta / "video_janela.mp4"
        if janela.exists() and janela.stat().st_size > 0:
            try:
                rodar(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.2f}", "-i", janela,
                       "-ss", f"{s:.2f}", "-i", pasta / "audio.m4a", "-t", f"{e - s:.2f}",
                       "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                       "-c:a", "aac", "-b:a", "192k", destino])
                if Path(destino).exists() and Path(destino).stat().st_size > 100000:
                    print("      cortei da imagem guardada da janela")
                    return
            except Exception as erro:
                print(f"      (imagem guardada falhou: {erro}; tentando baixar da live)")
        yt_trecho(url, av, s, e, destino)


# ---------------------------------------------------------------- rodada automática
RODADAS = TRABALHO.parent / "rodadas.json"     # quando cada live foi pega por último
RESUMO = TRABALHO.parent / "rodada_atual.txt"  # o que a IA precisa ler (curto)
CANAIS = TRABALHO.parent / "canais.txt"        # canais da Twitch/Kick/YouTube pra checar sempre


def lives_youtube(termos, quantas=10):
    from clip import GTA5, GTA6
    vistos = {}
    for termo in termos:
        url = f"https://www.youtube.com/results?search_query={termo.replace(' ', '+')}&sp=EgJAAQ%253D%253D"
        r = subprocess.run(ytdlp() + ["--flat-playlist", "-J", "--playlist-end", "30", "--no-warnings", url],
                           capture_output=True, text=True)
        try:
            itens = json.loads(r.stdout).get("entries") or []
        except json.JSONDecodeError:
            itens = []
        for v in itens:
            t = v.get("title") or ""
            if v.get("id") and v.get("live_status") == "is_live" and GTA6.search(t) and not GTA5.search(t):
                vistos[v["id"]] = {"url": f"https://www.youtube.com/watch?v={v['id']}", "titulo": t,
                                   "canal": v.get("channel") or v.get("uploader") or ""}
    return list(vistos.values())[:30]


def assistindo(link):
    r = subprocess.run(ytdlp() + ["-J", "--no-warnings", link], capture_output=True, text=True)
    try:
        m = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(m, dict) or not (m.get("is_live") or m.get("live_status") == "is_live"):
        return None
    titulo = (m.get("description") if site(link) == "twitch" else m.get("title")) or ""
    return {"url": link, "titulo": titulo, "canal": m.get("uploader") or m.get("channel") or "",
            "n": m.get("concurrent_view_count") or 0}


def rodada(links=None, max_lives=2, minutos_max=60, minimo=15, todas=False, termos=None):
    """Uma rodada: acha as maiores lives de GTA 6 abertas, pega só os minutos NOVOS de cada uma,
    escuta e grava quentes.txt. O resumo pra IA fica em rodada_atual.txt (curto de propósito)."""
    from clip import GTA6
    from ouvir import quentes
    termos = termos or ["GTA 6 ao vivo", "jogando GTA 6", "GTA 6 gameplay", "GTA VI ao vivo"]
    if links:
        cands = [{"url": u} for u in links]
    else:
        cands = lives_youtube(termos)
        if CANAIS.exists():  # canais da lista têm prioridade (a Twitch não diz quantos assistem)
            cands += [{"url": x, "vip": True, "ordem": i} for i, x in enumerate(
                      x.strip() for x in CANAIS.read_text(encoding="utf-8").splitlines()
                      if x.strip() and not x.strip().startswith("#"))]

    def checa(c):
        v = assistindo(c["url"])
        if v:
            v["vip"] = c.get("vip", False)
            v["ordem"] = c.get("ordem", 999)
        return v

    with ThreadPoolExecutor(10) as ex:
        vivas = [v for v in ex.map(checa, cands) if v]
    if not (links or todas):
        vivas = [v for v in vivas if GTA6.search(v["titulo"])]
    vivas.sort(key=lambda v: (not v["vip"], v["ordem"], -v["n"]))  # lista = ordem de prioridade
    estado = ler_json(RODADAS, {})
    agora = time.time()
    linhas = [f"# RODADA {datetime.now():%d/%m %H:%M} — {len(vivas)} lives de GTA 6 abertas", ""]
    feitas, canais_feitos = 0, set()
    for v in vivas:
        if feitas >= max_lives:
            break
        chave = re.sub(r"[^a-z0-9]", "", v["canal"].lower())
        if chave in canais_feitos:  # mesmo streamer na Twitch e no YouTube ao mesmo tempo: pega só uma
            continue
        canais_feitos.add(chave)
        ultimo = estado.get(v["url"], 0)
        minutos = min(minutos_max, int((agora - ultimo) / 60) + 2) if ultimo else minutos_max
        if minutos < minimo:
            linhas.append(f"- pulei {v['canal']}: pega há {int((agora - ultimo) / 60)} min")
            continue
        try:
            pasta = preparar(v["url"], minutos)
        except Exception as e:
            linhas.append(f"- ERRO em {v['canal']} ({v['url']}): {str(e)[:150]}")
            continue
        trans = ler_json(pasta / "transcricao.json")
        nq = quentes(pasta, trans, ler_json(pasta / "volume.json", []))
        estado[v["url"]] = agora
        gravar_json(RODADAS, estado)
        feitas += 1
        linhas += [f"## {v['canal']} — {v['n']:,} assistindo".replace(",", "."), f"   {v['titulo'][:100]}",
                   f"   PASTA: {pasta.name}", f"   LER: {pasta / 'quentes.txt'}  ({nq} trechos)", ""]
    if not feitas:
        linhas.append("Nada novo pra cortar nesta rodada.")
    RESUMO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


def checar_canais(canais):
    """Diz quais canais (Twitch/Kick/YouTube) estão ao vivo agora e com que título."""
    def um(c):
        r = subprocess.run(ytdlp() + ["-J", "--no-warnings", c], capture_output=True, text=True)
        try:
            m = json.loads(r.stdout)
        except json.JSONDecodeError:
            return c, None
        if not isinstance(m, dict) or not (m.get("is_live") or m.get("live_status") == "is_live"):
            return c, None
        return c, (m.get("description") if site(c) == "twitch" else m.get("title")) or "", \
            m.get("concurrent_view_count") or 0

    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(um, canais))
    vivos = sorted([r for r in res if r[1] is not None], key=lambda r: -(r[2] or 0))
    print(f"{len(vivos)} de {len(canais)} canais ao vivo agora:\n")
    for c, titulo, n in vivos:
        print(f"  {c}\n     {titulo[:90]} | {n:,} assistindo\n".replace(",", "."))
