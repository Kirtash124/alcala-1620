#!/usr/bin/env python3
"""Iguala el color del suelo de los soportales entre las casas pintadas.

    python3 herramientas/igualar_soportales.py casa_2 --como casa_1 casa_3
    python3 herramientas/igualar_soportales.py            # vuelve a aplicar lo apuntado

Cada casa trae su tramo de soportal pintado aparte y ChatGPT no siempre lo pinta del
mismo color: en la casa 2 las losas salieron amarillentas y se notaba el corte con
las vecinas. En el render, en cambio, todas las losas son iguales (mismo material,
misma luna), así que se mide en cada casa la razón entre la pintura y el render en
las losas, y a la casa que se desvía se le aplica, solo en el suelo del soportal
(losas y bordillo, sin las columnas), la ganancia por canal que lleva su razón a la
media de las casas de referencia. El resto de la pintura no se toca.

Lo apuntado queda en herramientas/datos/soportales.json, y procesar_pieza.py lo vuelve
a aplicar cuando se mete otra vez una casa.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

from isometria import AX, AY, ZH

RAIZ = Path(__file__).resolve().parent.parent
DIR_FICHAS = RAIZ / "herramientas/datos/piezas"
APUNTES = RAIZ / "herramientas/datos/soportales.json"
# Medidas del soportal en coordenadas de la casa (las de kit_calle_mayor.py).
ANCHO_CASA, FONDO = 6.0, -2.0
LOSAS = (FONDO, 0.18)          # franja de losas que se mide (sin el bordillo)
SUELO = (FONDO - 0.02, 0.44)   # franja que se corrige (losas y bordillo)


def mascara(ident, franja):
    """Píxeles de la pieza que son suelo del soportal en esa franja de y, sin las
    columnas (sus recortes, ensanchados 4 px) ni lo que tapan las casas vecinas."""
    ficha = json.loads((DIR_FICHAS / f"{ident}.json").read_text(encoding="utf-8"))
    w, h = ficha["tamano"]
    ax, ay = ficha["ancla"]

    def p(x, y):
        return (ax + (x - y) * AX, ay + (x + y) * AY)
    y0, y1 = franja
    lienzo = Image.new("L", (w, h), 0)
    ImageDraw.Draw(lienzo).polygon([p(0, y0), p(ANCHO_CASA, y0), p(ANCHO_CASA, y1), p(0, y1)], fill=255)
    cols = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(cols)
    for r in ficha["recortes"]:
        d.polygon([tuple(q) for q in r["poligono"]], fill=255)
    return (np.asarray(lienzo) > 0) & ~binary_dilation(np.asarray(cols) > 0, iterations=4)


def razon(ident):
    """Pintura / render en las losas, por canal."""
    pint = np.asarray(Image.open(RAIZ / f"arte/piezas/{ident}.png").convert("RGBA")).astype(np.float64)
    rend = np.asarray(Image.open(DIR_FICHAS / f"{ident}_render.png").convert("RGBA")).astype(np.float64)
    sel = mascara(ident, LOSAS) & (pint[..., 3] > 250) & (rend[..., 3] > 250)
    return pint[..., :3][sel].mean(0) / rend[..., :3][sel].mean(0)


def igualar(ident, como):
    objetivo = np.mean([razon(c) for c in como], axis=0)
    propia = razon(ident)
    ganancia = objetivo / propia
    ruta = RAIZ / f"arte/piezas/{ident}.png"
    img = np.asarray(Image.open(ruta).convert("RGBA")).astype(np.float32)
    # Peso 1 en todo el suelo, que se apaga en unos 6 px por fuera (junto a las
    # columnas y el zócalo) para que no quede un borde.
    peso = np.clip(gaussian_filter(mascara(ident, SUELO).astype(np.float32), 3.0) * 2, 0, 1)
    # El borde de la pieza (los 3 o 4 px junto a lo transparente) se deja como está: son
    # píxeles a medias y, al subirles el azul, salían puntitos rosas y azules en el
    # bordillo.
    hasta_borde = distance_transform_edt(img[..., 3] > 8)
    peso = (peso * np.clip((hasta_borde - 1) / 3, 0, 1))[..., None]
    antes = img[..., :3].copy()
    nuevo = antes * (1 + peso * (ganancia - 1))
    # La ganancia sube mucho el azul; en los píxeles rojizos (juntas, el bordillo) eso
    # los volvía rosas. En ellos el azul no pasa del verde más lo que ya le sacaba.
    r, g, b = antes[..., 0], antes[..., 1], antes[..., 2]
    tope = nuevo[..., 1] + np.maximum(np.minimum(r, b) - g, 0)
    rojizo = nuevo[..., 0] > nuevo[..., 1]
    nuevo[..., 2] = np.where(rojizo, np.minimum(nuevo[..., 2], np.maximum(tope, b)), nuevo[..., 2])
    img[..., :3] = np.clip(nuevo, 0, 255)
    Image.fromarray(img.astype(np.uint8), "RGBA").save(ruta, optimize=True)
    print(f"{ident}: suelo del soportal ×({ganancia[0]:.2f}, {ganancia[1]:.2f}, {ganancia[2]:.2f}) "
          f"para parecerse a {', '.join(como)}")


def apuntes():
    return json.loads(APUNTES.read_text(encoding="utf-8")) if APUNTES.exists() else {}


def reaplicar(ident):
    """Lo llama procesar_pieza.py tras meter una casa: si estaba apuntada, se iguala."""
    como = apuntes().get(ident)
    if como:
        igualar(ident, como)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("casa", nargs="?", help="casa que se corrige (sin nada: vuelve a aplicar lo apuntado)")
    ap.add_argument("--como", nargs="+", help="casas de referencia")
    a = ap.parse_args()
    notas = apuntes()
    if a.casa:
        if not a.como:
            ap.error("hace falta --como con las casas de referencia")
        notas[a.casa] = a.como
        APUNTES.write_text(json.dumps(notas, ensure_ascii=False, indent=1), encoding="utf-8")
        igualar(a.casa, a.como)
    else:
        for ident, como in notas.items():
            igualar(ident, como)
    for ident in sorted(p.stem for p in DIR_FICHAS.glob("casa_*.json")):
        r = razon(ident)
        print(f"  {ident}: pintura/render en las losas {r[0]:.2f} {r[1]:.2f} {r[2]:.2f}")


if __name__ == "__main__":
    main()
