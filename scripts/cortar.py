"""Passos 3 e 4: junta as notas que a IA deu, fica com os melhores e monta os cortes verticais.

Cada corte: câmera do streamer em cima, jogo embaixo, título de gancho, legenda palavra por palavra
e um .txt com a legenda do post e as hashtags.
"""
import json
import subprocess
from pathlib import Path

from comum import (CASA, CORTES, YUNET, gravar_json, hms, ler_json, rodar, segundos, ytdlp)  # noqa: F401

# vídeos de fundo (ex.: trailers do GTA 6, sem som) pra colocar embaixo quando a live é só câmera
FUNDOS = CASA / "fundos"

L, A = 1080, 1920          # vídeo vertical
CAM_H = 768                # faixa da câmera em cima
JOGO_H = A - CAM_H         # faixa do jogo embaixo
FUNDO_VC = CASA / "fundos" / "vicecity.png"  # fundo rosa/roxo atrás do jogo (gerado por fundo_vicecity.py)
CAMERA_PEQUENA_NO_MEIO = False  # True = câmera pequena sem esticar; False = câmera cheia em cima (pedido em 18/11)


# ================================================================ escolher
def escolher(pasta, manter=3, minimo=15, maximo=90):
    todos, ruins = [], []
    for arq in sorted((pasta / "momentos").glob("bloco_*.json")):
        dados = ler_json(arq)
        if dados is None:
            ruins.append(arq.name)
            continue
        for m in dados if isinstance(dados, list) else dados.get("momentos", []):
            try:
                s, e = segundos(m["inicio"]), segundos(m["fim"])
                m.update(_s=s, _e=e, nota=float(m.get("nota", 0)), _bloco=arq.stem)
                if e - s < minimo:
                    m["_e"] = s + minimo
                if e - s > maximo:
                    m["_e"] = s + maximo
                todos.append(m)
            except (KeyError, ValueError, TypeError):
                ruins.append(f"{arq.name}: {str(m)[:60]}")
    if ruins:
        print("ATENÇÃO, não consegui ler:", *ruins, sep="\n  ")
    todos.sort(key=lambda m: -m["nota"])
    escolhidos = []
    for m in todos:
        if any(m["_s"] < o["_e"] and o["_s"] < m["_e"] for o in escolhidos):
            continue  # sobrepõe um corte melhor
        escolhidos.append(m)
        if len(escolhidos) >= manter:
            break
    escolhidos.sort(key=lambda m: m["_s"])
    gravar_json(pasta / "escolhidos.json", {"possiveis": len(todos), "cortes": escolhidos})
    print(f"\nA IA achou {len(todos)} momentos possíveis e ficou com os {len(escolhidos)} melhores:")
    for i, m in enumerate(escolhidos, 1):
        print(f"  {i}. [{hms(m['_s'])}–{hms(m['_e'])}] nota {m['nota']:.0f}  {m.get('titulo', '')}")
    return escolhidos


# ================================================================ câmera do streamer
def achar_camera(video):
    """Procura o rosto em 14 quadros do trecho e devolve a caixa (x, y, l, a) do rosto mais frequente."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(video))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    esc = 960 / W
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (960, int(H * esc)), 0.75)
    caixas, quadros = [], 0
    for k in range(14):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (k + 0.5) / 14))
        ok, q = cap.read()
        if not ok:
            continue
        quadros += 1
        _, rostos = det.detect(cv2.resize(q, (960, int(H * esc))))
        for r in rostos if rostos is not None else []:
            if r[14] >= 0.75 and r[3] / esc > H * 0.05:
                caixas.append([v / esc for v in r[:4]])
    cap.release()
    if len(caixas) < 3:
        return W, H, None
    c = np.array(caixas)
    centros = c[:, :2] + c[:, 2:] / 2
    med = np.median(centros, axis=0)
    perto = c[np.linalg.norm(centros - med, axis=1) < W * 0.08]
    if len(perto) < 3:
        return W, H, None
    # cena aberta (live na rua/quintal): várias pessoas ou rosto que some e aparece.
    # o zoom fixo pegaria a pessoa errada, então mostra a cena inteira.
    if len(c) > quadros * 1.15 or len(perto) < quadros * 0.6:
        return W, H, None
    return W, H, np.median(perto, axis=0)


def _par(v):
    return int(v) // 2 * 2


def so_camera(H, rosto):
    """Rosto grande = a live é só a câmera (sem tela de jogo): não dá pra separar câmera e jogo."""
    return rosto is not None and rosto[3] > H * 0.15


def escolher_fundo(i, dur):
    """Pega um vídeo de fundos/ e um ponto de início diferente pra cada corte (pula logo do começo e do fim)."""
    import random
    vids = sorted(FUNDOS.glob("*.mp4")) if FUNDOS.exists() else []
    if not vids:
        return None, 0
    rnd = random.Random(i)
    v = vids[(i - 1) % len(vids)]
    tam = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(v)], capture_output=True, text=True).stdout.strip() or 0)
    folga = max(0.0, tam - 18 - min(dur, tam - 18))
    return v, 8 + rnd.uniform(0, folga) if folga else 8


MARCA = CASA / "fundos" / "marca.png"  # sua foto + @perfil (gerada por marca_dagua.py); sem ela, sai sem marca
MARCA_TROCA = 7  # segundos em cada lugar


def filtro(W, H, rosto, com_fundo=False):
    f = _filtro(W, H, rosto, com_fundo)
    if not MARCA.exists():
        return f
    # marca d'água meio transparente que muda de lugar a cada 7 s (dificulta recortar/copiar)
    i = f"mod(floor(t/{MARCA_TROCA}),3)"
    x = f"if(eq({i},1),W-w-30,30)"
    y = f"if(eq({i},0),150,if(eq({i},1),{A // 2 + 80},{A - 330}))"
    return f.replace("ass=legenda.ass[v]",
                     "ass=legenda.ass[pre];movie=marca.png,format=rgba,colorchannelmixer=aa=0.6[wm];"
                     f"[pre][wm]overlay=x='{x}':y='{y}':eval=frame[v]")


def _filtro(W, H, rosto, com_fundo=False):
    if so_camera(H, rosto) and com_fundo:  # só câmera + fundo: streamer em cima, trailer (sem som) embaixo
        ch = H
        cw = min(W, ch * L / CAM_H)
        ch = cw * CAM_H / L
        cx = min(max(rosto[0] + rosto[2] / 2 - cw / 2, 0), W - cw)
        cy = min(max(rosto[1] + rosto[3] * 0.5 - ch / 2, 0), H - ch)
        return (f"[0:v]crop={_par(cw)}:{_par(ch)}:{_par(cx)}:{_par(cy)},scale={L}:{CAM_H},setsar=1[cam];"
                f"[1:v]scale={L}:{JOGO_H}:force_original_aspect_ratio=increase,crop={L}:{JOGO_H},setsar=1,"
                f"fps=30[jogo];[cam][jogo]vstack=inputs=2,format=yuv420p,ass=legenda.ass[v]")
    if so_camera(H, rosto):  # só câmera: corta em pé, centrado no rosto, tela inteira
        cw = min(W, H * L / A)
        cx = min(max(rosto[0] + rosto[2] / 2 - cw / 2, 0), W - cw)
        return (f"[0:v]crop={_par(cw)}:{_par(H)}:{_par(cx)}:0,scale={L}:{A},setsar=1,"
                f"format=yuv420p,ass=legenda.ass[v]")
    if rosto is None and FUNDO_VC.exists():  # sem câmera: jogo no meio, fundo "vibe Vice City" (rosa/roxo)
        return ("movie=vicecity.png,loop=-1:1:0,scale=1080:1920,setsar=1[bg];"
                "[0:v]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,setsar=1,"
                "format=yuv420p,ass=legenda.ass[v]")
    if rosto is None:  # sem câmera: jogo inteiro no meio, fundo desfocado
        return ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3[bg];"
                "[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p,ass=legenda.ass[v]")
    fx, fy, fw, fh = rosto
    cw = min(W, max(fw * 3.2, 200))
    ch = cw * CAM_H / L
    if ch > H:
        ch, cw = H, H * L / CAM_H
    cx = min(max(fx + fw / 2 - cw / 2, 0), W - cw)
    cy = min(max(fy + fh * 0.65 - ch / 2, 0), H - ch)
    if CAMERA_PEQUENA_NO_MEIO and L / cw > 2.0:  # desligado: a pessoa prefere a câmera cheia em cima, mesmo borrada
        k = min(2.3, CAM_H / ch, L / cw)  # aumenta no máximo 2.3x; jogo embaixo sem esticar; fundo desfocado
        sw, sh = _par(cw * k), _par(ch * k)
        jh = _par(min(H, JOGO_H * 0.8))
        return (f"[0:v]scale={L}:{A}:force_original_aspect_ratio=increase,crop={L}:{A},boxblur=30:3[bg];"
                f"[0:v]crop={_par(cw)}:{_par(ch)}:{_par(cx)}:{_par(cy)},scale={sw}:{sh}:flags=lanczos[cam];"
                f"[0:v]scale=-2:{jh}:flags=lanczos,crop={L}:{jh}[fg];"
                f"[bg][cam]overlay=(W-w)/2:({CAM_H}-h)/2[t];[t][fg]overlay=0:{CAM_H}+({JOGO_H}-h)/2,"
                f"setsar=1,format=yuv420p,ass=legenda.ass[v]")
    gw = min(W, H * L / JOGO_H)
    gx = (W - gw) / 2
    return (f"[0:v]crop={_par(cw)}:{_par(ch)}:{_par(cx)}:{_par(cy)},scale={L}:{CAM_H}:flags=lanczos,setsar=1[cam];"
            f"[0:v]crop={_par(gw)}:{_par(H)}:{_par(gx)}:0,scale={L}:{JOGO_H},setsar=1[jogo];"
            f"[cam][jogo]vstack=inputs=2,drawbox=x=0:y={CAM_H - 4}:w={L}:h=8:color=white:t=fill,"
            f"format=yuv420p,ass=legenda.ass[v]")


# ================================================================ legenda
def _ass_tempo(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _limpo(txt):
    return txt.replace("{", "(").replace("}", ")").replace("\\", "/").strip()


def palavras_do_trecho(video, idioma, modelo="small"):
    from faster_whisper import WhisperModel
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(video), language=idioma, word_timestamps=True, vad_filter=True,
                           vad_parameters={"threshold": 0.25, "min_silence_duration_ms": 400},  # fala por cima do jogo
                           condition_on_previous_text=False)
    # o whisper às vezes "estica" uma palavra por 20 s quando vem silêncio/música: limita a 1,2 s
    return [(w.start, min(w.end, w.start + 1.2), w.word.strip())
            for s in segs for w in (s.words or []) if w.word.strip()]


LEGENDA_PALAVRAS = False  # legenda gigante palavra por palavra (desligada em 18/11 pra testar o estilo limpo)


def _titulo_rosa(titulo):
    import re
    t = _limpo(titulo).upper()
    return re.sub(r"(GTA\s*(6|VI)|VICE CITY|LEONIDA)", r"{\\c&HD62BE0&}\1{\\c&H000000&}", t)


def escrever_ass(caminho, titulo, palavras, dur, com_camera, tela_cheia=False):
    y_titulo = 230 if tela_cheia else (CAM_H if com_camera else 520)
    y_leg = 1520 if tela_cheia else (CAM_H + int(JOGO_H * 0.62) if com_camera else 1480)
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L}", f"PlayResY: {A}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        # título: caixa BRANCA com letra preta grossa e "GTA 6" em rosa (estilo dos cortes que viralizam)
        "Style: Gancho,Arial Black,56,&H00000000,&H00000000,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,3,20,0,5,"
        "50,50,0,1",
        "Style: Leg,Arial,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 1,{_ass_tempo(0)},{_ass_tempo(dur)},Gancho,,0,0,0,,{{\\pos(540,{y_titulo})}}{_titulo_rosa(titulo)}",
    ]
    if not LEGENDA_PALAVRAS:
        palavras = []
    grupos = [palavras[i:i + 3] for i in range(0, len(palavras), 3)]
    for g, grupo in enumerate(grupos):
        prox = grupos[g + 1][0][0] if g + 1 < len(grupos) else dur
        for k, (s, e, _) in enumerate(grupo):
            fim = grupo[k + 1][0] if k + 1 < len(grupo) else (prox if prox - e < 0.6 else e + 0.25)
            txt = " ".join(("{\\c&H00E5FF&}" if j == k else "{\\c&HFFFFFF&}") + _limpo(w).upper()
                           for j, (_, _, w) in enumerate(grupo))
            linhas.append(f"Dialogue: 0,{_ass_tempo(s)},{_ass_tempo(fim)},Leg,,0,0,0,,{{\\pos(540,{y_leg})}}{txt}")
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


# ================================================================ abertura com a reação
GANCHO_DUR = 2.8


def abrir_com_gancho(m, s, trecho):
    """Se o momento tem "gancho" (HH:MM:SS do grito/reação), o vídeo abre com ~3 s dessa reação e depois
    volta pro começo do corte (mostrando o que causou). Prende quem está rolando o feed."""
    if not m.get("gancho"):
        return
    original = trecho.with_name("sem_gancho.mp4")
    if original.exists():
        return  # já montado
    try:
        g = segundos(m["gancho"]) - s
    except (ValueError, TypeError):
        return
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(trecho)], capture_output=True, text=True).stdout.strip() or 0)
    a = max(0.0, g - 0.4)
    b = min(dur, a + GANCHO_DUR)
    if b - a < 1.5 or a < 3:  # reação logo no começo: não precisa de abertura
        return
    trecho.rename(original)
    print(f"      abertura com a reação ({hms(s + a)})")
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original), "-filter_complex",
           f"[0:v]split[v0][v1];[0:a]asplit[a0][a1];"
           f"[v0]trim={a:.2f}:{b:.2f},setpts=PTS-STARTPTS[gv];[a0]atrim={a:.2f}:{b:.2f},asetpts=PTS-STARTPTS[ga];"
           f"[v1]setpts=PTS-STARTPTS[tv];[a1]asetpts=PTS-STARTPTS[ta];"
           f"[gv][ga][tv][ta]concat=n=2:v=1:a=1[v][a]",
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
           "-c:a", "aac", "-b:a", "192k", str(trecho)])


# ================================================================ baixar só o pedaço
FORMATO = "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b"


def tem_video(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    n = r.stdout.strip().split(",")[0].strip()  # às vezes vem "1500," com vírgula no fim
    return n.isdigit() and int(n) > 10


def baixar_trecho(pasta, url, s, e, destino):
    """Tenta baixar só os minutos do corte. Alguns sites (hoje o YouTube) não entregam a imagem desse jeito:
    aí baixa o vídeo da live uma vez só (até 1080p) e recorta aqui no computador."""
    if (pasta / "aovivo.json").exists():  # live ainda no ar: pedaço por pedaço
        from aovivo import baixar_trecho as ao_vivo
        try:
            ao_vivo(pasta, url, s, e, destino)
            if destino.exists() and tem_video(destino):
                return
        except Exception as erro:
            raise SystemExit(f"      não consegui baixar esse corte da live aberta ({erro})")
        # live aberta: o modo normal ia gravar a live inteira em tempo real e nunca terminar
        raise SystemExit("      não consegui baixar esse corte da live aberta (o arquivo saiu vazio)")
    print("      baixando só esse pedaço do vídeo…")
    try:
        rodar(ytdlp() + ["-f", FORMATO, "--no-playlist", "--no-warnings", "-q", "--download-sections",
                         f"*{s:.2f}-{e:.2f}", "--force-keyframes-at-cuts", "--merge-output-format", "mp4",
                         "-o", str(destino), url])
    except subprocess.CalledProcessError:
        pass
    if destino.exists() and tem_video(destino):
        return
    destino.unlink(missing_ok=True)
    inteiro = next(iter(pasta.glob("video_inteiro.*")), None)
    if not inteiro or not tem_video(inteiro):
        print("      esse site não deixa baixar só um pedaço da imagem: baixando o vídeo uma vez (até 1080p)…")
        rodar(ytdlp() + ["-f", FORMATO, "--no-playlist", "--no-warnings", "--merge-output-format", "mp4",
                         "-o", str(pasta / "video_inteiro.%(ext)s"), url])
        inteiro = next(iter(pasta.glob("video_inteiro.*")))
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.2f}", "-i", inteiro, "-t", f"{e - s:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", destino])


# ================================================================ fazer
def fazer(pasta, modelo_legenda="small"):
    info = ler_json(pasta / "info.json", {})
    escolhidos = ler_json(pasta / "escolhidos.json", {}).get("cortes")
    if not escolhidos:
        raise SystemExit("Nenhum corte escolhido ainda. Rode antes: clip.py escolher " + pasta.name)
    idioma = ler_json(pasta / "transcricao.json", {}).get("idioma")
    destino = CORTES / pasta.name
    destino.mkdir(parents=True, exist_ok=True)
    feitos = []
    for i, m in enumerate(escolhidos, 1):
        s, e = m["_s"], m["_e"]
        print(f"\n[4/4] Corte {i}/{len(escolhidos)}: {m.get('titulo', '')}  ({hms(s)}–{hms(e)})")
        tdir = pasta / f"corte_{i:02d}"
        tdir.mkdir(exist_ok=True)
        trecho = tdir / "trecho.mp4"
        if trecho.exists() and not tem_video(trecho):
            trecho.unlink()
        if not trecho.exists():
            baixar_trecho(pasta, info["url"], s, e, trecho)
        abrir_com_gancho(m, s, trecho)
        import shutil
        for extra in (FUNDO_VC, MARCA):  # o ffmpeg lê essas imagens da pasta do corte
            if extra.exists():
                shutil.copy(extra, tdir / extra.name)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "csv=p=0", str(trecho)], capture_output=True, text=True).stdout.strip())
        print("      procurando a câmera do streamer…")
        W, H, rosto = achar_camera(trecho)
        cheia = so_camera(H, rosto)
        fundo, ini_fundo = escolher_fundo(i, dur) if cheia else (None, 0)
        print(f"      live só de câmera: streamer em cima, {fundo.name} embaixo (sem som)" if fundo else
              "      live só de câmera: streamer em tela cheia" if cheia else
              "      câmera achada" if rosto is not None else "      sem câmera: jogo inteiro com fundo desfocado")
        palavras = []
        if LEGENDA_PALAVRAS:
            print("      legenda palavra por palavra…")
            palavras = palavras_do_trecho(trecho, idioma, modelo_legenda)
        escrever_ass(tdir / "legenda.ass", m.get("titulo", ""), palavras, dur, rosto is not None,
                     cheia and not fundo)
        saida = destino / f"corte_{i:02d}.mp4"
        extra = (["-stream_loop", "-1", "-ss", f"{ini_fundo:.2f}", "-an", "-i", str(fundo)] if fundo else [])
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", "trecho.mp4", *extra, "-filter_complex",
               filtro(W, H, rosto, bool(fundo)), "-map", "[v]", "-map", "0:a?", "-t", f"{dur:.2f}",
               "-c:v", "libx264", "-preset", "medium",
               "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
               str(saida.resolve())], cwd=tdir)
        post = (f"{m.get('titulo', '')}\n\n{m.get('post', '').strip()}\n\n"
                f"Corte da live de {info.get('uploader') or info.get('channel')}: {info.get('webpage_url') or info['url']}\n")
        saida.with_suffix(".txt").write_text(post, encoding="utf-8")
        feitos.append(saida)
        if (pasta / "aovivo.json").exists():  # corte de live aberta: entra na fila pra postar
            fila = ler_json(CASA / "fila_postar.json", [])
            if not any(f["mp4"] == str(saida) for f in fila):
                from datetime import datetime
                fila.append({"mp4": str(saida), "txt": str(saida.with_suffix(".txt")),
                             "titulo": m.get("titulo", ""), "nota": m.get("nota", 0),
                             "criado": f"{datetime.now():%d/%m %H:%M}"})
                gravar_json(CASA / "fila_postar.json", fila)
        print(f"      PRONTO: {saida}")
    print(f"\n{len(feitos)} cortes prontos pra postar em {destino}")
    return feitos
