#!/usr/bin/env python3
"""Cose los trozos del suelo pintados por ChatGPT y los mete en el juego.

    python3 herramientas/procesar_suelo.py suelo_1=~/Descargas/a.png suelo_3=b.png
    python3 herramientas/procesar_suelo.py            # con lo que ya hay en arte/entrada/suelo/

El suelo mide 3200 × 1800 y ChatGPT no pinta tanto de una vez, así que se pide en
cuatro trozos con solape (docs/arte/suelo/suelo_N_luz.png; ver docs/arte/suelo/README.md).

1. A cada trozo le quita el magenta (donde van las casas) y lo encaja sobre su silueta.
2. Iguala el color entre trozos: con lo que coincide en los solapes calcula, por canal,
   una ganancia para cada trozo, para que ninguno quede más claro o más cálido que su
   vecino.
3. Funde los trozos con una transición suave en mitad de cada solape.
4. Donde no hay pintura (un trozo aún sin pintar, o bajo las casas) queda el render
   (herramientas/datos/suelo_render.png).

Guarda arte/fondos/calle_mayor_suelo.png, copia cada pintura original en
arte/entrada/suelo/ y deja una comprobación en pruebas/salida/suelo_comprobacion.png.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from procesar_pieza import encajar, transformar

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "herramientas/datos"
ENTRADA = RAIZ / "arte/entrada/suelo"
TRANSICION = 140.0     # px del juego que dura el fundido entre dos trozos


def quitar_magenta(img):
    """Solo se quita el magenta: las esquinas de un trozo pueden ser calle, así que no
    vale tomar su color como fondo (lo que hace quitar_fondo con las figuras)."""
    px = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    sobra = np.clip((np.minimum(r, b) - g - 60) / 120, 0, 1) * np.clip((np.minimum(r, b) - 120) / 80, 0, 1)
    alfa = 1 - sobra
    # Quita el tinte magenta de los bordes que se quedan.
    limpio = np.clip((px - np.array([255, 0, 255]) * (1 - alfa[..., None])) / np.maximum(alfa[..., None], 0.05), 0, 255)
    rgb = np.where(alfa[..., None] > 0.02, limpio, px)
    return Image.fromarray(np.dstack([rgb, alfa * 255]).astype(np.uint8), "RGBA")


def cargar_pintura(ruta, mascara):
    pint = quitar_magenta(Image.open(ruta))
    if pint.size != mascara.shape[::-1]:
        pint = pint.resize(mascara.shape[::-1], Image.LANCZOS)
        print(f"  aviso: {ruta.name} venía a otro tamaño; se ajusta")
    puntos, escala, dx, dy = encajar(pint, mascara)
    return transformar(pint, escala, dx, dy, mascara.shape[::-1]), puntos, (escala, dx, dy)


def al_lienzo(img, rect, escala, lienzo):
    """Lleva un trozo (en píxeles de ChatGPT) a su sitio en el lienzo del juego."""
    x, y = rect[0], rect[1]
    capa = img.transform(lienzo, Image.AFFINE, (escala, 0, -x * escala, 0, escala, -y * escala),
                         resample=Image.BICUBIC)
    return np.asarray(capa).astype(np.float32) / 255.0


def ganancias(capas, rects):
    """Ganancia por canal de cada trozo (en logaritmos, de media cero) que iguala lo que
    se ve en los solapes. Mínimos cuadrados sobre las diferencias de cada par."""
    n = len(capas)
    filas, difs = [], []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = capas[i], capas[j]
            if a is None or b is None:
                continue
            ambos = (a[..., 3] > 0.9) & (b[..., 3] > 0.9)
            if ambos.sum() < 2000:
                continue
            fy, fx = np.where(ambos)
            caja = (slice(fy.min(), fy.max() + 1), slice(fx.min(), fx.max() + 1))
            dentro = ambos[caja]
            la = np.log(gaussian_filter(a[caja][..., :3], (6, 6, 0))[dentro] + 0.02).mean(0)
            lb = np.log(gaussian_filter(b[caja][..., :3], (6, 6, 0))[dentro] + 0.02).mean(0)
            fila = np.zeros(n)
            fila[i], fila[j] = 1.0, -1.0
            filas.append(fila)
            difs.append(lb - la)
    g = np.zeros((n, 3))
    if not filas:
        return np.exp(g)
    activos = [i for i in range(n) if capas[i] is not None]
    A = np.array(filas + [[1.0 if i in activos else 0.0 for i in range(n)]])
    for c in range(3):
        bvec = np.array([d[c] for d in difs] + [0.0])
        g[:, c] = np.linalg.lstsq(A, bvec, rcond=None)[0]
    return np.exp(g)


def pesos(rects, lienzo):
    """Reparto del lienzo entre los trozos: cada uno manda en su mitad del solape,
    con un fundido de TRANSICION px en el medio."""
    w, h = lienzo
    xs = sorted({r[0] for r in rects})
    ys = sorted({r[1] for r in rects})
    u = np.arange(w)[None, :]
    v = np.arange(h)[:, None]

    def corte(posiciones, tam, coord, idx):
        if len(posiciones) == 1:
            return np.ones_like(coord, dtype=np.float32)
        medio = (posiciones[0] + tam + posiciones[1]) / 2       # mitad del solape
        primero = np.clip((medio - coord) / TRANSICION + 0.5, 0, 1)
        return primero if idx == 0 else 1 - primero
    salida = []
    for r in rects:
        wx = corte(xs, r[2], u, xs.index(r[0]))
        wy = corte(ys, r[3], v, ys.index(r[1]))
        salida.append((wx * wy).astype(np.float32))
    return salida


def main():
    ficha = json.loads((DATOS / "suelo.json").read_text(encoding="utf-8"))
    lienzo = tuple(ficha["lienzo"])
    escala = ficha["escala"]
    teselas = ficha["teselas"]
    ENTRADA.mkdir(parents=True, exist_ok=True)

    # Pinturas nuevas pasadas como suelo_N=ruta: se guardan en arte/entrada/suelo.
    for arg in sys.argv[1:]:
        ident, ruta = arg.split("=", 1)
        if ident not in {t["id"] for t in teselas}:
            sys.exit(f"No hay ningún trozo llamado {ident}")
        shutil.copy(Path(ruta).expanduser(), ENTRADA / f"{ident}_pintada.png")

    render = np.asarray(Image.open(DATOS / "suelo_render.png").convert("RGB")).astype(np.float32) / 255.0
    capas, rects = [], []
    for t in teselas:
        rects.append(t["rect"])
        ruta = ENTRADA / f"{t['id']}_pintada.png"
        if not ruta.exists():
            print(f"{t['id']}: sin pintar (queda el render)")
            capas.append(None)
            continue
        mascara = np.asarray(Image.open(DATOS / f"{t['id']}_mascara.png").convert("L")) > 127
        img, puntos, (esc, dx, dy) = cargar_pintura(ruta, mascara)
        print(f"{t['id']}: coincide con la silueta un {puntos:.1%} (escala ×{esc:.3f}, desplazamiento {dx:+d}, {dy:+d})")
        if puntos < 0.9:
            print("  aviso: ChatGPT ha movido o cambiado el contorno; revisa la comprobación")
        capas.append(al_lienzo(img, t["rect"], escala, lienzo))

    g = ganancias(capas, rects)
    reparto = pesos(rects, lienzo)
    suma = np.zeros(lienzo[::-1], np.float32)
    color = np.zeros(lienzo[::-1] + (3,), np.float32)
    for capa, gan, w in zip(capas, g, reparto):
        if capa is None:
            continue
        peso = w * capa[..., 3]
        color += capa[..., :3] * gan * peso[..., None]
        suma += peso
    hay = suma > 1e-4
    final = render.copy()
    final[hay] = color[hay] / suma[hay, None]
    # Al borde de lo pintado (junto a las casas o a un trozo sin pintar), fundido con el render.
    borde = np.clip(suma, 0, 1)[..., None]
    final = final * borde + render * (1 - borde)
    salida = Image.fromarray((np.clip(final, 0, 1) * 255).astype(np.uint8))
    salida.save(RAIZ / "arte/fondos/calle_mayor_suelo.png", optimize=True)
    print("Ganancias por trozo (R, G, B): " + "; ".join(
        f"{t['id']} {gg[0]:.2f} {gg[1]:.2f} {gg[2]:.2f}" for t, gg, c in zip(teselas, g, capas) if c is not None))

    comp = salida.resize((lienzo[0] // 2, lienzo[1] // 2), Image.LANCZOS)
    d = ImageDraw.Draw(comp)
    for t in teselas:
        x, y, w, h = (v / 2 for v in t["rect"])
        d.rectangle((x, y, x + w, y + h), outline=(255, 0, 255), width=2)
        d.text((x + 8, y + 8), t["id"], fill=(255, 0, 255))
    destino = RAIZ / "pruebas/salida/suelo_comprobacion.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    comp.save(destino)
    print(f"Suelo del juego actualizado; comprobación en {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
