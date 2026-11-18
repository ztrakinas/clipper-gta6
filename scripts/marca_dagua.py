"""Gera a marca d'água (foto redonda do seu perfil + @seuperfil) em PNG transparente.
Uso: python marca_dagua.py @seuperfil foto.png [saida.png]
Sem a marca (fundos/marca.png), os cortes saem sem marca d'água."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import os

if len(sys.argv) < 3:
    sys.exit("Uso: python marca_dagua.py @seuperfil foto.png [saida.png]")
CASA = Path(os.environ.get("CLIPPER_GTA6_HOME", str(Path.home() / "clipper-gta6")))
TEXTO = sys.argv[1]
foto = Path(sys.argv[2])
saida = Path(sys.argv[3]) if len(sys.argv) > 3 else CASA / "fundos" / "marca.png"
saida.parent.mkdir(parents=True, exist_ok=True)

TAM = 96
fonte = None
for nome in [r"C:\Windows\Fonts\ariblk.ttf", "/System/Library/Fonts/Supplemental/Arial Black.ttf", "DejaVuSans-Bold.ttf"]:
    try:
        fonte = ImageFont.truetype(nome, 40)
        break
    except OSError:
        pass
fonte = fonte or ImageFont.load_default(40)
larg_txt = int(fonte.getlength(TEXTO))
W, H = TAM + 18 + larg_txt + 12, TAM + 12
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# foto redonda com borda branca
f = Image.open(foto).convert("RGBA").resize((TAM, TAM), Image.LANCZOS)
masc = Image.new("L", (TAM, TAM), 0)
ImageDraw.Draw(masc).ellipse([0, 0, TAM - 1, TAM - 1], fill=255)
img.paste(f, (6, 6), masc)
ImageDraw.Draw(img).ellipse([5, 5, TAM + 6, TAM + 6], outline=(255, 255, 255, 255), width=4)

# texto branco com sombra escura (legível em qualquer fundo)
sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
y = (H - 48) // 2
ImageDraw.Draw(sombra).text((TAM + 18, y + 2), TEXTO, font=fonte, fill=(0, 0, 0, 230))
img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(3)))
ImageDraw.Draw(img).text((TAM + 18, y), TEXTO, font=fonte, fill=(255, 255, 255, 255))
img.save(saida)
print("marca salva em", saida, img.size)
