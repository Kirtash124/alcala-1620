#!/usr/bin/env python3
"""Mete en el juego una pieza pintada por ChatGPT encima de su maqueta.

    python3 herramientas/procesar_pieza.py casa_3 ~/Descargas/casa_3_pintada.png
    python3 herramientas/procesar_pieza.py casa_3 pintada.png --solo-comprobar

Qué hace:
  1. Quita el fondo magenta.
  2. Encaja la pintura sobre la silueta de la maqueta (busca escala y desplazamiento:
     ChatGPT a veces mueve o agranda un poco el dibujo) e informa de cuánto coincide.
  3. La pasa a la escala del juego y le pone la silueta exacta del render (incluidas
     las zonas que tapan las casas vecinas). Donde la pintura no cubra, deja el render.
  4. Guarda arte/piezas/<id>.png (el render anterior queda copiado en
     herramientas/datos/piezas/<id>_render.png) y una imagen de comprobación en
     pruebas/salida/piezas/<id>_comprobacion.png.

Si la coincidencia es baja (menos del 92 %), no sustituye nada: hay que pedir a
ChatGPT que respete la silueta.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from procesar_arte import quitar_fondo

RAIZ = Path(__file__).resolve().parent.parent
DIR_FICHAS = RAIZ / "herramientas/datos/piezas"
UMBRAL = 0.92


def iou(a, b):
    union = np.logical_or(a, b).sum()
    return np.logical_and(a, b).sum() / union if union else 0.0


def desplazamiento_fft(fija, movil):
    """Desplazamiento entero (dy, dx) que mejor lleva `movil` sobre `fija`."""
    F = np.fft.rfft2(fija.astype(np.float32))
    G = np.fft.rfft2(movil.astype(np.float32))
    corr = np.fft.irfft2(F * np.conj(G), s=fija.shape)
    dy, dx = np.unravel_index(np.argmax(corr), corr.shape)
    h, w = fija.shape
    return (dy - h if dy > h // 2 else dy), (dx - w if dx > w // 2 else dx)


def transformar(img, escala, dx, dy, tamano):
    """Escala alrededor del centro y desplaza (en píxeles de la maqueta)."""
    cx, cy = tamano[0] / 2, tamano[1] / 2
    # Imagen.transform pide la inversa: de la salida a la entrada.
    a = 1 / escala
    return img.transform(tamano, Image.AFFINE, (a, 0, cx - (cx + dx) * a, 0, a, cy - (cy + dy) * a),
                         resample=Image.BICUBIC)


def encajar(pintada, mascara):
    """Busca la escala y el desplazamiento que mejor encajan la pintura en la silueta."""
    tam = mascara.shape[::-1]
    alfa = pintada.split()[3]
    mejor = (0.0, 1.0, 0, 0)
    for escala in np.arange(0.94, 1.0601, 0.005):
        movida = np.asarray(transformar(alfa, escala, 0, 0, tam)) > 127
        dy, dx = desplazamiento_fft(mascara, movida)
        if abs(dx) > 80 or abs(dy) > 80:
            continue
        movida = np.asarray(transformar(alfa, escala, dx, dy, tam)) > 127
        puntos = iou(mascara, movida)
        if puntos > mejor[0]:
            mejor = (puntos, float(escala), int(dx), int(dy))
    return mejor


def main():
    args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args.add_argument("pieza")
    args.add_argument("pintada", type=Path)
    args.add_argument("--solo-comprobar", action="store_true", help="no sustituye la pieza del juego")
    args.add_argument("--tolerancia", type=float, default=90.0, help="tolerancia del color de fondo")
    args.add_argument("--forzar", action="store_true", help="sustituir aunque la coincidencia sea baja")
    a = args.parse_args()

    ficha = json.loads((DIR_FICHAS / f"{a.pieza}.json").read_text(encoding="utf-8"))
    maq = ficha["maqueta"]
    tam_maq = tuple(maq["tamano"])
    mascara_img = Image.open(DIR_FICHAS / f"{a.pieza}_mascara.png").convert("L")
    mascara = np.asarray(mascara_img) > 127

    pintada = quitar_fondo(Image.open(a.pintada), a.tolerancia)
    if pintada.size != tam_maq:
        # ChatGPT a veces devuelve otro tamaño: se ajusta por el lado que encaja.
        f = min(tam_maq[0] / pintada.width, tam_maq[1] / pintada.height)
        nueva = pintada.resize((round(pintada.width * f), round(pintada.height * f)), Image.LANCZOS)
        lienzo = Image.new("RGBA", tam_maq, (0, 0, 0, 0))
        lienzo.paste(nueva, ((tam_maq[0] - nueva.width) // 2, (tam_maq[1] - nueva.height) // 2))
        pintada = lienzo
        print(f"Aviso: la imagen venía a otro tamaño; ajustada ×{f:.3f}")

    puntos, escala, dx, dy = encajar(pintada, mascara)
    alineada = transformar(pintada, escala, dx, dy, tam_maq)
    cubre = (np.asarray(alineada.split()[3]) > 127) & mascara
    cobertura = cubre.sum() / max(1, mascara.sum())
    print(f"Coincidencia con la silueta: {puntos:.1%} (escala ×{escala:.3f}, desplazamiento {dx:+d}, {dy:+d} px)")
    print(f"La pintura cubre el {cobertura:.1%} de la pieza")

    # Paso a la escala del juego: recorte de la maqueta que corresponde a la imagen del juego.
    s = maq["escala"]
    ancho, alto = ficha["tamano"]
    x0 = maq["ancla"][0] - ficha["ancla"][0] * s
    y0 = maq["ancla"][1] - ficha["ancla"][1] * s
    caja = (x0, y0, x0 + ancho * s, y0 + alto * s)

    def a_juego(img, filtro=Image.LANCZOS):
        return img.transform((ancho, alto), Image.EXTENT, caja, resample=Image.BICUBIC) if s < 1.2 else \
            img.crop(tuple(round(v) for v in caja)).resize((ancho, alto), filtro)

    ruta_juego = RAIZ / "arte/piezas" / f"{a.pieza}.png"
    copia_render = DIR_FICHAS / f"{a.pieza}_render.png"
    if not copia_render.exists():
        shutil.copy(ruta_juego, copia_render)
    render = np.asarray(Image.open(copia_render).convert("RGBA")).astype(np.float32)
    pint = np.asarray(a_juego(alineada)).astype(np.float32)
    alfa_pint = pint[..., 3:4] / 255
    rgb = pint[..., :3] * alfa_pint + render[..., :3] * (1 - alfa_pint)
    resultado = np.dstack([rgb, render[..., 3]]).astype(np.uint8)

    # Comprobación: render, pintura y silueta de la maqueta encima.
    comp = Image.new("RGB", (ancho * 3 + 20, alto), (40, 40, 40))
    comp.paste(Image.fromarray(render.astype(np.uint8)).convert("RGB"), (0, 0))
    comp.paste(Image.fromarray(resultado).convert("RGB"), (ancho + 10, 0))
    capa = Image.fromarray(resultado).convert("RGB")
    borde = Image.fromarray((render[..., 3] > 127).astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)
    capa.paste((255, 0, 255), (0, 0), borde)
    comp.paste(capa, (2 * ancho + 20, 0))
    ImageDraw.Draw(comp).text((10, 10), f"{a.pieza}: coincide {puntos:.1%}, cubre {cobertura:.1%}", fill=(255, 255, 255))
    destino = RAIZ / "pruebas/salida/piezas"
    destino.mkdir(parents=True, exist_ok=True)
    comp.save(destino / f"{a.pieza}_comprobacion.png")
    print(f"Comprobación en {destino / (a.pieza + '_comprobacion.png')}")

    if a.solo_comprobar:
        return
    if puntos < UMBRAL and not a.forzar:
        print(f"No se sustituye: la pintura no respeta la silueta (menos del {UMBRAL:.0%}). "
              "Pide a ChatGPT que no mueva ni cambie el contorno, o usa --forzar.")
        sys.exit(1)
    Image.fromarray(resultado).save(ruta_juego, optimize=True)
    print(f"Pieza del juego actualizada: {ruta_juego.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
