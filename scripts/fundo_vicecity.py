"""Desenha o fundo "vibe Vice City" (pôr do sol rosa/roxo, sol listrado, palmeiras) usado atrás do jogo
quando o corte não tem câmera cheia. Uso: python fundo_vicecity.py [saida.png]"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SO_CORES = True


def mistura(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def gradiente(img):
    paradas = ([(0.0, (40, 8, 80)), (0.45, (120, 24, 150)), (0.8, (230, 50, 150)), (1.0, (255, 110, 130))]
               if SO_CORES else
               [(0.0, (24, 6, 58)), (0.40, (110, 20, 130)), (0.72, (236, 56, 140)), (0.86, (255, 140, 120)),
                (1.0, (40, 10, 70))])
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        for (t0, c0), (t1, c1) in zip(paradas, paradas[1:]):
            if t0 <= t <= t1:
                c = mistura(c0, c1, (t - t0) / (t1 - t0))
                break
        for x in range(W):
            px[x, y] = c


def sol(img, cx, cy, r):
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for y in range(cy - r, cy + r):
        t = (y - (cy - r)) / (2 * r)
        meia = int(math.sqrt(max(r * r - (y - cy) ** 2, 0)))
        cor = mistura((255, 230, 120), (255, 60, 150), t)
        # listras horizontais na metade de baixo (estilo synthwave)
        if t > 0.5 and int((y - cy) / 14) % 2 == 0 and (y - cy) % 14 < 4 + int(t * 8):
            continue
        d.line([(cx - meia, y), (cx + meia, y)], fill=cor + (255,))
    brilho = camada.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(brilho)
    img.alpha_composite(camada)


def palmeira(d, x, base, altura, curva, escala, cor=(20, 4, 36, 255)):
    pontos = []
    for i in range(41):
        t = i / 40
        pontos.append((x + curva * t * t, base - altura * t))
    for (x0, y0), (x1, y1) in zip(pontos, pontos[1:]):
        w = int((26 - 14 * ((base - y0) / altura)) * escala)
        d.line([(x0, y0), (x1, y1)], fill=cor, width=max(w, 4))
    tx, ty = pontos[-1]
    for ang in (-170, -140, -110, -70, -40, -10, 15):
        a = math.radians(ang)
        comp = random.uniform(170, 240) * escala
        folha = []
        for i in range(21):
            t = i / 20
            px_ = tx + math.cos(a) * comp * t
            py_ = ty + math.sin(a) * comp * t + (t * t) * 90 * escala
            folha.append((px_, py_))
        for (x0, y0), (x1, y1) in zip(folha, folha[1:]):
            d.line([(x0, y0), (x1, y1)], fill=cor, width=int(18 * escala * (1 - 0.7 * (folha.index((x0, y0)) / 20))) + 3)


def grade(d, horizonte):
    cor = (255, 80, 200, 120)
    for i in range(-14, 15):
        d.line([(W / 2 + i * 40, horizonte), (W / 2 + i * 260, H)], fill=cor, width=2)
    y, passo = horizonte, 8
    while y < H:
        d.line([(0, y), (W, y)], fill=cor, width=2)
        passo *= 1.25
        y += passo


def desenhar(saida):
    random.seed(6)
    img = Image.new("RGB", (W, H))
    gradiente(img)
    img = img.convert("RGBA")
    if SO_CORES:  # versão limpa (pedido de 18/11): só o degradê roxo → rosa, sem sol/estrada/palmeira
        img.convert("RGB").save(saida)
        print("fundo salvo em", saida)
        return
    # o jogo fica no meio (y ~650–1270): sol e grade embaixo, copas das palmeiras em cima
    sol(img, W // 2, 1560, 250)
    d = ImageDraw.Draw(img)
    horizonte = 1660
    d.rectangle([(0, horizonte), (W, H)], fill=(30, 6, 52, 255))
    grade(d, horizonte)
    palmeira(d, 70, 1800, 1330, 140, 1.0)
    palmeira(d, 1010, 1840, 1380, -160, 1.05)
    palmeira(d, 250, 1700, 1150, 70, 0.65)
    palmeira(d, 840, 1720, 1180, -80, 0.7)
    # estrelinhas no céu
    for _ in range(90):
        x, y = random.randint(0, W), random.randint(0, 650)
        s = random.choice((1, 1, 2, 3))
        d.ellipse([(x, y), (x + s, y + s)], fill=(255, 220, 255, random.randint(120, 255)))
    img.convert("RGB").save(saida)
    print("fundo salvo em", saida)


if __name__ == "__main__":
    desenhar(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fundo_vicecity.png"))
