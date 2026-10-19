#!/usr/bin/env python3
"""Genera los personajes y objetos PROVISIONALES del prototipo.

No es arte final: sirve para probar la tubería con las mismas medidas que tendrá el
arte real. El escenario ya no sale de aquí: lo modela y renderiza kit_calle_mayor.py.

Uso:  python3 herramientas/arte_provisional.py
Salida:
  arte/personajes/*.png              pesquisidor (SE, NE), alguacil (SE)
  arte/objetos/cadaver.png, sombra.png
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from isometria import AX, AY, ZH, ANCHO_FONDO, ALTO_FONDO, Proyeccion

RAIZ = Path(__file__).resolve().parent.parent
random.seed(1620)
np.random.seed(1620)

W, H = ANCHO_FONDO, ALTO_FONDO
PR = Proyeccion(603, 273)
p = PR.p

LARGO = 22.0          # longitud de la fachada con soportales (m)
FONDO_GALERIA = -2.0  # y del muro interior del soportal
ALTO_SOPORTAL = 3.6   # altura libre hasta la viga (m)
FRENTE = 0.25         # y de la fachada alta (sobre las columnas)
COLUMNAS_X = [1.5 + 3 * k for k in range(7)] + [22.0]
Z_HORNACINA = 1.0     # altura de la repisa de la hornacina (m)
# Borde izquierdo de la hornacina: centrada en pantalla entre las columnas de 16,5 y 19,5 m.
X_HORNACINA = 15.725


# --------------------------------------------------------------- utilidades

def color(hexa: str) -> tuple[int, int, int]:
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def ruido(ancho: int, alto: int, escala: float, desenfoque: float) -> np.ndarray:
    """Ruido suave en [-1, 1] para dar textura a superficies planas."""
    base = np.random.normal(0, 1, (max(1, int(alto / escala)), max(1, int(ancho / escala))))
    img = Image.fromarray(((base - base.min()) / (np.ptp(base) + 1e-9) * 255).astype(np.uint8))
    img = img.resize((ancho, alto), Image.BICUBIC).filter(ImageFilter.GaussianBlur(desenfoque))
    arr = np.asarray(img).astype(np.float32) / 127.5 - 1.0
    return arr


GRANO = ruido(W, H, 3, 0.6)      # grano fino de pintura
MANCHAS = ruido(W, H, 40, 12)    # manchas amplias de suciedad y humedad


def rellenar(lienzo: Image.Image, poligono, rgb, grano=0.08, manchas=0.10):
    """Rellena un polígono con color texturizado (grano + manchas)."""
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).polygon(poligono, fill=255)
    arr = np.asarray(lienzo).astype(np.float32)
    m = np.asarray(mascara).astype(np.float32)[..., None] / 255.0
    capa = np.ones_like(arr) * np.array(rgb, np.float32)
    factor = 1.0 + GRANO[..., None] * grano + MANCHAS[..., None] * manchas
    capa = np.clip(capa * factor, 0, 255)
    arr = arr * (1 - m) + capa * m
    lienzo.paste(Image.fromarray(arr.astype(np.uint8)))


def sombrear(lienzo: Image.Image, poligono, intensidad: float, desenfoque: float = 0):
    """Oscurece una zona (sombra u oclusión ambiental)."""
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).polygon(poligono, fill=int(255 * intensidad))
    if desenfoque:
        mascara = mascara.filter(ImageFilter.GaussianBlur(desenfoque))
    negro = Image.new("RGB", (W, H), (12, 10, 14))
    lienzo.paste(Image.composite(negro, lienzo, mascara))


def caja(x0, y0, x1, y1, z0, z1):
    """Caras visibles de un prisma: (frontal +y, lateral +x, tapa)."""
    frontal = [p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1)]
    lateral = [p(x1, y0, z0), p(x1, y1, z0), p(x1, y1, z1), p(x1, y0, z1)]
    tapa = [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
    return frontal, lateral, tapa


def envolvente(puntos):
    """Envolvente convexa de puntos 2D (cadena monótona de Andrew)."""
    pts = sorted(set((round(a, 2), round(b, 2)) for a, b in puntos))

    def giro(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    inferior, superior = [], []
    for q in pts:
        while len(inferior) >= 2 and giro(inferior[-2], inferior[-1], q) <= 0:
            inferior.pop()
        inferior.append(q)
    for q in reversed(pts):
        while len(superior) >= 2 and giro(superior[-2], superior[-1], q) <= 0:
            superior.pop()
        superior.append(q)
    return inferior[:-1] + superior[:-1]


def dibujar_caja(lienzo, x0, y0, x1, y1, z0, z1, rgb, grano=0.06):
    frontal, lateral, tapa = caja(x0, y0, x1, y1, z0, z1)
    r, g, b = rgb
    rellenar(lienzo, tapa, (min(255, r * 1.12), min(255, g * 1.12), min(255, b * 1.12)), grano)
    rellenar(lienzo, frontal, rgb, grano)
    rellenar(lienzo, lateral, (r * 0.72, g * 0.72, b * 0.74), grano)  # luz desde la izquierda


# --------------------------------------------------------------- fondo

ESC = 4  # se dibuja a 4x y se reduce, para bordes suaves


def lienzo_personaje(ancho=120, alto=196):
    img = Image.new("RGBA", (ancho * ESC, alto * ESC), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def S(*pts):
    return [(a * ESC, b * ESC) for a, b in pts]


def reducir(img, ancho=120, alto=196):
    return img.resize((ancho, alto), Image.LANCZOS)


def pesquisidor(de_espaldas: bool) -> Image.Image:
    img, d = lienzo_personaje()
    cx = 60
    capa = (24, 22, 26, 255)
    jubon = (46, 44, 52, 255)
    piel = (214, 172, 140, 255)
    # Piernas y botas.
    d.polygon(S((cx - 13, 140), (cx - 3, 140), (cx - 4, 188), (cx - 15, 188)), fill=(30, 26, 24, 255))
    d.polygon(S((cx + 3, 140), (cx + 13, 140), (cx + 16, 188), (cx + 5, 188)), fill=(30, 26, 24, 255))
    d.polygon(S((cx - 16, 182), (cx - 3, 182), (cx + 1, 192), (cx - 17, 192)), fill=(18, 15, 14, 255))
    d.polygon(S((cx + 4, 182), (cx + 16, 182), (cx + 21, 192), (cx + 4, 192)), fill=(18, 15, 14, 255))
    # Calzas acuchilladas.
    d.polygon(S((cx - 17, 112), (cx + 17, 112), (cx + 15, 145), (cx - 15, 145)), fill=(52, 40, 46, 255))
    # Jubón.
    if not de_espaldas:
        d.polygon(S((cx - 18, 62), (cx + 18, 62), (cx + 16, 118), (cx - 16, 118)), fill=jubon)
        for by in range(68, 116, 7):
            d.ellipse(S((cx + 1, by), (cx + 3, by + 2)), fill=(170, 150, 100, 255))
    # Capa: cae desde los hombros, más larga por detrás.
    if de_espaldas:
        d.polygon(S((cx - 21, 60), (cx + 21, 60), (cx + 28, 150), (cx - 28, 152)), fill=capa)
    else:
        d.polygon(S((cx - 21, 60), (cx - 8, 62), (cx - 12, 140), (cx - 27, 146)), fill=capa)
        d.polygon(S((cx + 17, 60), (cx + 22, 62), (cx + 26, 138), (cx + 17, 132)), fill=capa)
    # Cabeza.
    d.ellipse(S((cx - 10, 30), (cx + 10, 56)), fill=piel if not de_espaldas else (40, 30, 26, 255))
    if not de_espaldas:
        d.polygon(S((cx + 8, 42), (cx + 13, 47), (cx + 8, 48)), fill=(196, 150, 120, 255))        # nariz
        d.polygon(S((cx - 4, 50), (cx + 8, 50), (cx + 3, 62)), fill=(40, 30, 26, 255))           # perilla
        d.ellipse(S((cx + 1, 41), (cx + 4, 43)), fill=(30, 24, 22, 255))                         # ojo
    # Lechuguilla (cuello de lienzo plisado, aún en uso en 1620).
    d.ellipse(S((cx - 17, 52), (cx + 17, 66)), fill=(236, 232, 220, 255))
    for k in range(-15, 16, 4):
        d.line(S((cx + k, 54), (cx + k, 64)), fill=(190, 186, 176, 255), width=ESC)
    # Sombrero de ala ancha.
    d.ellipse(S((cx - 27, 24), (cx + 27, 38)), fill=(22, 20, 22, 255))
    d.polygon(S((cx - 12, 30), (cx + 12, 30), (cx + 10, 12), (cx - 10, 12)), fill=(28, 26, 28, 255))
    d.line(S((cx - 12, 27), (cx + 12, 27)), fill=(70, 50, 40, 255), width=2 * ESC)
    # Espada ropera asomando bajo la capa.
    if not de_espaldas:
        d.line(S((cx - 18, 112), (cx - 34, 160)), fill=(150, 150, 160, 255), width=2 * ESC)
        d.ellipse(S((cx - 21, 106), (cx - 13, 114)), fill=(120, 100, 60, 255))
    return reducir(img)


def alguacil() -> Image.Image:
    img, d = lienzo_personaje()
    cx = 58
    piel = (206, 160, 128, 255)
    d.polygon(S((cx - 12, 140), (cx - 3, 140), (cx - 4, 190), (cx - 14, 190)), fill=(48, 34, 26, 255))
    d.polygon(S((cx + 3, 140), (cx + 12, 140), (cx + 15, 190), (cx + 5, 190)), fill=(48, 34, 26, 255))
    d.polygon(S((cx - 19, 64), (cx + 19, 64), (cx + 20, 146), (cx - 20, 146)), fill=(104, 44, 34, 255))   # ropilla
    d.polygon(S((cx - 22, 62), (cx - 10, 64), (cx - 16, 120), (cx - 25, 118)), fill=(58, 40, 30, 255))     # capotillo
    d.line(S((cx - 19, 112), (cx + 19, 112)), fill=(30, 22, 18, 255), width=3 * ESC)                       # cinto
    d.ellipse(S((cx - 10, 32), (cx + 10, 58)), fill=piel)
    d.polygon(S((cx - 9, 48), (cx + 9, 48), (cx + 7, 60), (cx - 7, 60)), fill=(70, 56, 46, 255))          # barba
    d.polygon(S((cx + 8, 43), (cx + 13, 48), (cx + 8, 49)), fill=(186, 140, 112, 255))
    d.ellipse(S((cx + 1, 42), (cx + 4, 44)), fill=(30, 24, 22, 255))
    d.ellipse(S((cx - 15, 56), (cx + 15, 66)), fill=(220, 214, 200, 255))
    d.ellipse(S((cx - 24, 26), (cx + 24, 38)), fill=(26, 22, 22, 255))
    d.polygon(S((cx - 11, 31), (cx + 11, 31), (cx + 9, 15), (cx - 9, 15)), fill=(32, 28, 28, 255))
    # Vara de justicia en la mano izquierda.
    d.line(S((cx - 26, 46), (cx - 22, 186)), fill=(28, 24, 22, 255), width=3 * ESC)
    d.ellipse(S((cx - 29, 42), (cx - 22, 49)), fill=(190, 160, 80, 255))
    d.ellipse(S((cx - 28, 96), (cx - 19, 106)), fill=piel)
    # Farol en la mano derecha.
    d.ellipse(S((cx + 17, 96), (cx + 26, 106)), fill=piel)
    d.line(S((cx + 22, 104), (cx + 24, 114)), fill=(40, 34, 26, 255), width=2 * ESC)
    d.polygon(S((cx + 16, 114), (cx + 32, 114), (cx + 30, 138), (cx + 18, 138)), fill=(70, 58, 36, 255))
    d.polygon(S((cx + 19, 117), (cx + 29, 117), (cx + 28, 135), (cx + 20, 135)), fill=(255, 210, 120, 255))
    return reducir(img)


def cadaver() -> Image.Image:
    """Cuerpo tendido a lo largo del eje x del mundo, con la capa abierta."""
    ancho, alto = 220, 130
    img = Image.new("RGBA", (ancho * ESC, alto * ESC), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    loc = Proyeccion(ancho / 2, alto / 2 + 8)
    q = lambda x, y, z=0.0: (loc.p(x, y, z)[0] * ESC, loc.p(x, y, z)[1] * ESC)
    # Charco oscuro.
    charco = [q(0.15 + 0.55 * math.cos(a) * (1 + 0.25 * math.sin(3 * a)), 0.1 + 0.4 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)]
    d.polygon(charco, fill=(40, 12, 14, 215))
    # Capa extendida.
    d.polygon([q(-0.55 + 0.75 * math.cos(a) * (1 + 0.12 * math.sin(5 * a)) + 0.6, 0.42 * math.sin(a) * (1 + 0.15 * math.cos(4 * a))) for a in np.linspace(0, 2 * math.pi, 40)], fill=(26, 26, 32, 255))
    # Cuerpo: torso, piernas y cabeza.
    d.polygon([q(-0.45, -0.18, 0.18), q(0.15, -0.2, 0.18), q(0.15, 0.2, 0.18), q(-0.45, 0.18, 0.18)], fill=(60, 54, 62, 255))
    d.polygon([q(0.15, -0.16, 0.12), q(0.8, -0.1, 0.1), q(0.8, 0.02, 0.1), q(0.15, 0.0, 0.12)], fill=(44, 36, 40, 255))
    d.polygon([q(0.15, 0.04, 0.12), q(0.78, 0.12, 0.1), q(0.78, 0.24, 0.1), q(0.15, 0.18, 0.12)], fill=(44, 36, 40, 255))
    cab = q(-0.62, 0.0, 0.12)
    d.ellipse([cab[0] - 9 * ESC, cab[1] - 7 * ESC, cab[0] + 9 * ESC, cab[1] + 7 * ESC], fill=(196, 176, 158, 255))
    lech = q(-0.5, 0.0, 0.18)
    d.ellipse([lech[0] - 8 * ESC, lech[1] - 5 * ESC, lech[0] + 8 * ESC, lech[1] + 5 * ESC], fill=(222, 218, 206, 255))
    mano = q(-0.2, 0.42, 0.06)
    d.ellipse([mano[0] - 5 * ESC, mano[1] - 3 * ESC, mano[0] + 5 * ESC, mano[1] + 3 * ESC], fill=(200, 180, 164, 255))
    # Gotas de cera negra junto a la mano: la primera pista.
    for gx, gy in [(-0.05, 0.62), (0.1, 0.7), (-0.15, 0.75), (0.2, 0.58)]:
        g = q(gx, gy, 0.01)
        d.ellipse([g[0] - 2.5 * ESC, g[1] - 1.5 * ESC, g[0] + 2.5 * ESC, g[1] + 1.5 * ESC], fill=(12, 10, 12, 255))
    # Sombrero caído.
    sm = q(-0.95, -0.5, 0.03)
    d.ellipse([sm[0] - 16 * ESC, sm[1] - 6 * ESC, sm[0] + 16 * ESC, sm[1] + 6 * ESC], fill=(22, 20, 22, 255))
    return img.resize((ancho, alto), Image.LANCZOS)


def sombra() -> Image.Image:
    img = Image.new("RGBA", (96, 40), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([8, 6, 88, 34], fill=(0, 0, 0, 120))
    return img.filter(ImageFilter.GaussianBlur(5))


def main():
    (RAIZ / "arte/personajes").mkdir(parents=True, exist_ok=True)
    (RAIZ / "arte/objetos").mkdir(parents=True, exist_ok=True)

    pesquisidor(False).save(RAIZ / "arte/personajes/pesquisidor_se.png")
    pesquisidor(True).save(RAIZ / "arte/personajes/pesquisidor_ne.png")
    alguacil().save(RAIZ / "arte/personajes/alguacil_se.png")
    cadaver().save(RAIZ / "arte/objetos/cadaver.png")
    sombra().save(RAIZ / "arte/objetos/sombra.png")
    print("Arte provisional generado.")


if __name__ == "__main__":
    main()
