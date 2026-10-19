#!/usr/bin/env python3
"""Genera el arte PROVISIONAL del prototipo y los datos de la escena.

No es arte final: sirve para probar la tubería (fondo plano + oclusores +
zona transitable + personajes) con las mismas medidas que tendrá el arte real.

Uso:  python3 herramientas/arte_provisional.py
Salida:
  arte/fondos/calle_mayor.png        fondo 2560x1440
  arte/personajes/*.png              pesquisidor (SE, NE), alguacil (SE)
  arte/objetos/cadaver.png, sombra.png
  herramientas/datos/calle_mayor.json   coordenadas para montar la escena
"""
import json
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

def fondo() -> tuple[Image.Image, dict]:
    lienzo = Image.new("RGB", (W, H), color("#2b3140"))
    d = ImageDraw.Draw(lienzo)

    # Cielo de anochecer arriba: degradado vertical.
    for yy in range(0, 700):
        t = yy / 700
        d.line([(0, yy), (W, yy)], fill=(int(28 + 30 * t), int(32 + 30 * t), int(48 + 30 * t)))

    # Suelo de la calle y de la plaza: toda la mitad inferior.
    suelo = [p(-20, -12), p(50, -12), p(50, 32), p(-20, 32)]
    rellenar(lienzo, suelo, color("#5c5246"), 0.10, 0.18)

    # Empedrado: cantos irregulares sobre una base oscura.
    for gx in np.arange(-12, 38, 0.36):
        for gy in np.arange(-2.6, 22, 0.36):
            if FONDO_GALERIA < gy < 0.35 and gx < LARGO + 0.3:
                continue  # dentro del soportal hay losas, no cantos
            cx, cy = gx + random.uniform(-0.08, 0.08), gy + random.uniform(-0.08, 0.08)
            rx, ry = random.uniform(0.11, 0.16), random.uniform(0.11, 0.16)
            pts = [p(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)]
            tono = random.randint(-14, 14)
            base = color("#7a7062")
            d.polygon(pts, fill=(base[0] + tono, base[1] + tono, base[2] + tono - 3))

    # Canalillo central de la calle, típico de las calles castellanas.
    canal = [p(-10, 3.65), p(38, 3.65), p(38, 3.95), p(-10, 3.95)]
    rellenar(lienzo, canal, color("#463f37"), 0.12, 0.2)

    # Suelo del soportal: losas de piedra.
    galeria = [p(0, FONDO_GALERIA), p(LARGO, FONDO_GALERIA), p(LARGO, 0.3), p(0, 0.3)]
    rellenar(lienzo, galeria, color("#8c8170"), 0.07, 0.12)
    for lx in np.arange(0, LARGO, 0.9):
        d.line([p(lx, FONDO_GALERIA), p(lx, 0.3)], fill=color("#5e564b"), width=2)
    for ly in np.arange(FONDO_GALERIA, 0.3, 0.9):
        d.line([p(0, ly), p(LARGO, ly)], fill=color("#5e564b"), width=2)

    # Muro interior del soportal (planta baja), encalado y sucio por abajo.
    muro = [p(0, FONDO_GALERIA, 0), p(LARGO, FONDO_GALERIA, 0), p(LARGO, FONDO_GALERIA, ALTO_SOPORTAL), p(0, FONDO_GALERIA, ALTO_SOPORTAL)]
    rellenar(lienzo, muro, color("#b9ae97"), 0.06, 0.16)
    zocalo = [p(0, FONDO_GALERIA, 0), p(LARGO, FONDO_GALERIA, 0), p(LARGO, FONDO_GALERIA, 0.6), p(0, FONDO_GALERIA, 0.6)]
    rellenar(lienzo, zocalo, color("#6f665a"), 0.08, 0.2)

    # Puertas de tiendas y casas en el muro del soportal.
    for px_ in [2.4, 8.2, 13.6, 19.6]:
        hoja = [p(px_, FONDO_GALERIA, 0), p(px_ + 1.3, FONDO_GALERIA, 0),
                p(px_ + 1.3, FONDO_GALERIA, 2.4), p(px_, FONDO_GALERIA, 2.4)]
        rellenar(lienzo, hoja, color("#4a3426"), 0.1, 0.1)
        dintel = [p(px_ - 0.1, FONDO_GALERIA, 2.4), p(px_ + 1.4, FONDO_GALERIA, 2.4),
                  p(px_ + 1.4, FONDO_GALERIA, 2.6), p(px_ - 0.1, FONDO_GALERIA, 2.6)]
        rellenar(lienzo, dintel, color("#5e4632"), 0.08, 0.1)
        d.line([p(px_ + 0.65, FONDO_GALERIA, 0.05), p(px_ + 0.65, FONDO_GALERIA, 2.35)], fill=color("#2c1f16"), width=3)

    # Hornacina con su vela. La repisa va a 1 m: más arriba la taparía la viga.
    hx, z0 = X_HORNACINA, Z_HORNACINA
    nicho = [p(hx, FONDO_GALERIA, z0), p(hx + 0.55, FONDO_GALERIA, z0)]
    for a in np.linspace(0, math.pi, 12):
        nicho.append(p(hx + 0.275 + 0.275 * math.cos(a), FONDO_GALERIA, z0 + 0.4 + 0.275 * math.sin(a)))
    rellenar(lienzo, nicho, color("#3a3029"), 0.05, 0.05)
    cruz_v = [p(hx + 0.26, FONDO_GALERIA, z0 + 0.2), p(hx + 0.29, FONDO_GALERIA, z0 + 0.2), p(hx + 0.29, FONDO_GALERIA, z0 + 0.55), p(hx + 0.26, FONDO_GALERIA, z0 + 0.55)]
    cruz_h = [p(hx + 0.17, FONDO_GALERIA, z0 + 0.42), p(hx + 0.38, FONDO_GALERIA, z0 + 0.42), p(hx + 0.38, FONDO_GALERIA, z0 + 0.46), p(hx + 0.17, FONDO_GALERIA, z0 + 0.46)]
    rellenar(lienzo, cruz_v, color("#b8955a"), 0.02, 0)
    rellenar(lienzo, cruz_h, color("#b8955a"), 0.02, 0)
    vela = [p(hx + 0.23, FONDO_GALERIA + 0.05, z0), p(hx + 0.32, FONDO_GALERIA + 0.05, z0),
            p(hx + 0.32, FONDO_GALERIA + 0.05, z0 + 0.23), p(hx + 0.23, FONDO_GALERIA + 0.05, z0 + 0.23)]
    rellenar(lienzo, vela, color("#e8dfc8"), 0.02, 0)
    llama = p(hx + 0.275, FONDO_GALERIA + 0.06, z0 + 0.29)
    d.ellipse([llama[0] - 4, llama[1] - 9, llama[0] + 4, llama[1] + 3], fill=color("#ffd27a"))
    hornacina_centro = p(hx + 0.275, FONDO_GALERIA, z0 + 0.35)

    # Sombra del soportal: el muro y el suelo bajo la galería quedan en penumbra.
    sombrear(lienzo, muro, 0.35, 6)
    sombrear(lienzo, galeria, 0.30, 10)

    # Columnas de piedra con zapatas de madera, de atrás hacia delante.
    oclusores = []
    for cx in COLUMNAS_X:
        dibujar_caja(lienzo, cx - 0.26, -0.26, cx + 0.26, 0.26, 0, 0.32, color("#9b927f"))
        dibujar_caja(lienzo, cx - 0.17, -0.17, cx + 0.17, 0.17, 0.32, 3.12, color("#a59c88"))
        dibujar_caja(lienzo, cx - 0.25, -0.25, cx + 0.25, 0.25, 3.12, 3.35, color("#9b927f"))
        dibujar_caja(lienzo, cx - 0.65, -0.18, cx + 0.65, 0.18, 3.35, 3.6, color("#5a4330"))
        # Polígono que tapa la columna: contorno de su silueta en pantalla.
        silueta = [p(cx - 0.27, 0.27, -0.02), p(cx + 0.27, 0.27, -0.02), p(cx + 0.27, -0.27, -0.02),
                   p(cx + 0.27, -0.27, 3.37), p(cx - 0.27, -0.27, 3.37), p(cx - 0.27, 0.27, 3.37)]
        oclusores.append({
            "nombre": f"Columna{COLUMNAS_X.index(cx) + 1}",
            "poligono": [list(map(round, pt)) for pt in silueta],
            "linea_base": round(p(cx + 0.26, 0.26)[1]),
            "siempre_delante": False,
        })
        # Oclusión ambiental al pie de la columna.
        sombrear(lienzo, [p(cx - 0.45, 0.25), p(cx + 0.45, 0.25), p(cx + 0.45, 0.6), p(cx - 0.45, 0.6)], 0.35, 6)

    # Viga corrida sobre las zapatas.
    viga = [p(0, FRENTE, 3.6), p(LARGO + 0.3, FRENTE, 3.6), p(LARGO + 0.3, FRENTE, 3.85), p(0, FRENTE, 3.85)]
    rellenar(lienzo, viga, color("#4c3828"), 0.1, 0.1)

    # Fachada alta, por tramos de casas con colores distintos.
    tramos = [(0, 5.5, "#b89b6e"), (5.5, 11, "#cfc6b0"), (11, 16.5, "#a8735a"), (16.5, LARGO + 0.3, "#c2a97a")]
    for x0, x1, c in tramos:
        cara = [p(x0, FRENTE, 3.85), p(x1, FRENTE, 3.85), p(x1, FRENTE, 7.0), p(x0, FRENTE, 7.0)]
        rellenar(lienzo, cara, color(c), 0.07, 0.18)
        d.line([p(x1, FRENTE, 3.85), p(x1, FRENTE, 7.0)], fill=color("#5e5446"), width=3)
        for vx in (x0 + 1.4, x0 + 3.8):
            if vx + 1.0 > x1:
                continue
            encendida = random.random() < 0.3
            hueco = [p(vx, FRENTE, 4.6), p(vx + 1.0, FRENTE, 4.6), p(vx + 1.0, FRENTE, 6.1), p(vx, FRENTE, 6.1)]
            rellenar(lienzo, hueco, color("#d9a650") if encendida else color("#2a2420"), 0.05, 0.05)
            postigo_i = [p(vx - 0.32, FRENTE, 4.6), p(vx, FRENTE, 4.6), p(vx, FRENTE, 6.1), p(vx - 0.32, FRENTE, 6.1)]
            rellenar(lienzo, postigo_i, color("#3d4a3a"), 0.08, 0.08)
            # Balcón de forja: barandilla delante del hueco.
            for bx in np.arange(vx - 0.1, vx + 1.12, 0.12):
                d.line([p(bx, FRENTE + 0.35, 4.4), p(bx, FRENTE + 0.35, 5.05)], fill=color("#1c1a1a"), width=2)
            d.line([p(vx - 0.12, FRENTE + 0.35, 5.05), p(vx + 1.12, FRENTE + 0.35, 5.05)], fill=color("#1c1a1a"), width=3)
            losa = [p(vx - 0.15, FRENTE, 4.35), p(vx + 1.15, FRENTE, 4.35), p(vx + 1.15, FRENTE + 0.4, 4.35), p(vx - 0.15, FRENTE + 0.4, 4.35)]
            rellenar(lienzo, losa, color("#6a6052"), 0.06, 0.06)

    # Alero y tejado de teja árabe.
    alero = [p(0, FRENTE, 7.0), p(LARGO + 0.3, FRENTE, 7.0), p(LARGO + 0.3, FRENTE + 0.5, 6.92), p(0, FRENTE + 0.5, 6.92)]
    rellenar(lienzo, alero, color("#4a3a2c"), 0.08, 0.08)
    tejado = [p(0, FRENTE + 0.5, 6.92), p(LARGO + 0.3, FRENTE + 0.5, 6.92), p(LARGO + 0.3, -4.5, 9.1), p(0, -4.5, 9.1)]
    rellenar(lienzo, tejado, color("#8a4a32"), 0.1, 0.2)
    for fila in np.linspace(0, 1, 16):
        y_t = (FRENTE + 0.5) + (-4.5 - FRENTE - 0.5) * fila
        z_t = 6.92 + (9.1 - 6.92) * fila
        d.line([p(0, y_t, z_t), p(LARGO + 0.3, y_t, z_t)], fill=color("#5e3022"), width=2)
    for cx_ in np.arange(0, LARGO + 0.3, 0.32):
        d.line([p(cx_, FRENTE + 0.5, 6.92), p(cx_, -4.5, 9.1)], fill=color("#743c29"), width=1)

    # Fachada lateral del último edificio (x = 22,3), por encima de la galería.
    lateral = [p(LARGO + 0.3, FONDO_GALERIA, 3.6), p(LARGO + 0.3, FRENTE + 0.5, 3.6),
               p(LARGO + 0.3, FRENTE + 0.5, 6.92), p(LARGO + 0.3, -2.0, 8.1), p(LARGO + 0.3, -4.5, 9.1),
               p(LARGO + 0.3, -4.5, 3.6)]
    rellenar(lienzo, lateral, color("#9c8a68"), 0.07, 0.16)

    # Carro de madera en el lado cercano de la calle.
    cx0, cx1, cy0, cy1 = 6.2, 9.1, 6.1, 7.0
    dibujar_caja(lienzo, cx0, cy0, cx1, cy1, 0.65, 1.1, color("#6b4c33"))
    for vx in (6.75, 8.05):
        rueda = [p(vx + 0.55 * math.cos(a), cy1 + 0.06, 0.58 + 0.55 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28)]
        d.polygon(rueda, outline=color("#2e2116"))
        d.line(rueda + [rueda[0]], fill=color("#3b2a1c"), width=6)
        for a in np.linspace(0, math.pi, 4, endpoint=False):
            d.line([p(vx + 0.52 * math.cos(a), cy1 + 0.06, 0.58 + 0.52 * math.sin(a)),
                    p(vx - 0.52 * math.cos(a), cy1 + 0.06, 0.58 - 0.52 * math.sin(a))], fill=color("#3b2a1c"), width=3)
    d.line([p(cx0, cy0 + 0.2, 0.9), p(cx0 - 2.0, cy0 + 0.2, 0.25)], fill=color("#4a3524"), width=5)
    d.line([p(cx0, cy1 - 0.2, 0.9), p(cx0 - 2.0, cy1 - 0.2, 0.25)], fill=color("#4a3524"), width=5)
    sombrear(lienzo, [p(cx0 - 0.2, cy0, 0), p(cx1 + 0.4, cy0, 0), p(cx1 + 0.4, cy1 + 0.6, 0), p(cx0 - 0.2, cy1 + 0.6, 0)], 0.35, 10)
    silueta_carro = [p(cx0 - 2.05, cy0, 0.3), p(cx0, cy0, 1.15), p(cx1, cy0, 1.15), p(cx1 + 0.05, cy0, 1.15),
                     p(cx1 + 0.05, cy1 + 0.1, 1.15), p(cx1 + 0.05, cy1 + 0.1, 0.0), p(6.15, cy1 + 0.1, -0.02),
                     p(cx0 - 2.05, cy1, 0.2)]
    oclusores.append({"nombre": "Carro", "poligono": [list(map(round, pt)) for pt in silueta_carro],
                      "linea_base": round(p(cx1, cy1 + 0.1)[1]), "siempre_delante": False})

    # Barriles junto a la plaza.
    for bx, by in [(19.0, 6.55), (19.75, 6.85)]:
        r = 0.33
        lado = [p(bx + r * math.cos(a), by + r * math.sin(a), 0) for a in np.linspace(-math.pi / 4, 3 * math.pi / 4, 12)]
        lado += [p(bx + r * math.cos(a), by + r * math.sin(a), 0.95) for a in np.linspace(3 * math.pi / 4, -math.pi / 4, 12)]
        rellenar(lienzo, lado, color("#6e4f35"), 0.08, 0.1)
        tapa = [p(bx + r * math.cos(a), by + r * math.sin(a), 0.95) for a in np.linspace(0, 2 * math.pi, 20)]
        rellenar(lienzo, tapa, color("#8a6a4a"), 0.06, 0.05)
        for zz in (0.18, 0.77):
            aro = [p(bx + r * math.cos(a), by + r * math.sin(a), zz) for a in np.linspace(-math.pi / 4, 3 * math.pi / 4, 12)]
            d.line(aro, fill=color("#2a2826"), width=4)
    # Silueta exacta de los dos barriles: envolvente de sus círculos de base y de tapa.
    contorno = [p(bx + 0.345 * math.cos(a), by + 0.345 * math.sin(a), z)
                for bx, by in [(19.0, 6.55), (19.75, 6.85)] for z in (-0.02, 0.97)
                for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
    silueta_barriles = envolvente(contorno)
    oclusores.append({"nombre": "Barriles", "poligono": [list(map(round, pt)) for pt in silueta_barriles],
                      "linea_base": round(max(q[1] for q in silueta_barriles)), "siempre_delante": False})

    # Viñeteado suave para centrar la mirada.
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vin = np.clip(1.08 - 0.28 * dist ** 2, 0.6, 1.0)[..., None]
    arr = np.asarray(lienzo).astype(np.float32) * vin
    lienzo = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # Zona transitable (contorno exterior y huecos), en píxeles del fondo.
    exterior = [p(0.5, -1.65), p(21.9, -1.65), p(21.9, 0.55), p(23.8, 0.55), p(23.8, 7.5), p(0.5, 7.5)]
    huecos = []
    for cx in COLUMNAS_X[:-1]:
        huecos.append([p(cx - 0.32, -0.32), p(cx + 0.32, -0.32), p(cx + 0.32, 0.32), p(cx - 0.32, 0.32)])
    huecos.append([p(6.1, 5.95), p(9.25, 5.95), p(9.25, 7.2), p(6.1, 7.2)])            # carro
    huecos.append([p(18.55, 6.15), p(20.15, 6.15), p(20.15, 7.25), p(18.55, 7.25)])  # barriles
    huecos.append([p(10.25, 0.75), p(12.0, 0.75), p(12.0, 1.75), p(10.25, 1.75)])    # cadáver
    huecos.append([p(12.2, 2.15), p(12.85, 2.15), p(12.85, 2.85), p(12.2, 2.85)])    # alguacil

    def r2(pts):
        return [[round(a, 1), round(b, 1)] for a, b in pts]

    datos = {
        "fondo": "res://arte/fondos/calle_mayor.png",
        "tamano": [W, H],
        "transitable": {"exterior": r2(exterior), "huecos": [r2(h) for h in huecos]},
        "oclusores": oclusores,
        "jugador_inicio": r2([p(3.5, 4.2)])[0],
        "alguacil": {"pies": r2([p(12.5, 2.5)])[0], "farol": r2([p(12.78, 2.62, 0.82)])[0]},
        "cadaver": {"centro": r2([p(11.1, 1.25)])[0]},
        "hornacina": {"centro": r2([hornacina_centro])[0], "llama": r2([llama])[0]},
        "ventanas_luz": [],
        "puntos": {
            "alguacil": {"zona": r2([p(12.15, 2.15, 0), p(12.95, 2.15, 0), p(12.95, 2.95, 0), p(12.95, 2.95, 1.95),
                                    p(12.15, 2.15, 1.95)]),
                         "llegada": r2([p(12.3, 3.9)])[0]},
            "cadaver": {"zona": r2([p(10.2, 0.7), p(12.05, 0.7), p(12.05, 1.8), p(10.2, 1.8)]),
                        "llegada": r2([p(10.9, 2.55)])[0]},
            "hornacina": {"zona": r2([p(X_HORNACINA - 0.15, FONDO_GALERIA, Z_HORNACINA - 0.15),
                                      p(X_HORNACINA + 0.7, FONDO_GALERIA, Z_HORNACINA - 0.15),
                                      p(X_HORNACINA + 0.7, FONDO_GALERIA, Z_HORNACINA + 0.75),
                                      p(X_HORNACINA - 0.15, FONDO_GALERIA, Z_HORNACINA + 0.75)]),
                          "llegada": r2([p(X_HORNACINA + 0.3, -1.3)])[0]},
            "salida": {"zona": r2([p(22.6, 1.0), p(24.6, 1.0), p(24.6, 6.5), p(22.6, 6.5)]),
                       "llegada": r2([p(23.4, 3.6)])[0]},
        },
    }
    return lienzo, datos


# --------------------------------------------------------------- personajes

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
    (RAIZ / "arte/fondos").mkdir(parents=True, exist_ok=True)
    (RAIZ / "arte/personajes").mkdir(parents=True, exist_ok=True)
    (RAIZ / "arte/objetos").mkdir(parents=True, exist_ok=True)
    (RAIZ / "herramientas/datos").mkdir(parents=True, exist_ok=True)

    img, datos = fondo()
    img.save(RAIZ / "arte/fondos/calle_mayor.png", optimize=True)
    pesquisidor(False).save(RAIZ / "arte/personajes/pesquisidor_se.png")
    pesquisidor(True).save(RAIZ / "arte/personajes/pesquisidor_ne.png")
    alguacil().save(RAIZ / "arte/personajes/alguacil_se.png")
    cadaver().save(RAIZ / "arte/objetos/cadaver.png")
    sombra().save(RAIZ / "arte/objetos/sombra.png")
    with open(RAIZ / "herramientas/datos/calle_mayor.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print("Arte provisional generado.")


if __name__ == "__main__":
    main()
