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
  4. Luz: por defecto se respeta la pintura tal cual (--luz pintura; decisión de
     Esteban con la casa de la hornacina). Con --luz render se queda con la textura
     de la pintura y toma del render la luz y el color de conjunto, por si alguna
     pieza se desvía demasiado de la noche de las demás.
  5. Si la casa está apuntada en herramientas/datos/soportales.json, iguala el color del
     suelo de su soportal con el de sus vecinas (ver igualar_soportales.py).
  6. Guarda arte/piezas/<id>.png, copia la pintura original en
     arte/entrada/piezas/<id>_pintada.png y deja una imagen de comprobación en
     pruebas/salida/piezas/<id>_comprobacion.png. El render sin pintar está siempre en
     herramientas/datos/piezas/<id>_render.png.

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
RADIO_LUZ = 10      # px del juego: por encima de este tamaño manda la luz del render


def _lineal(x):
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _srgb(x):
    x = np.maximum(x, 0)
    return np.clip(np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055), 0, 1) * 255


def _desenfoque(x, radio):
    from scipy.ndimage import gaussian_filter
    return np.stack([gaussian_filter(x[..., c], radio) for c in range(x.shape[-1])], -1)


def luz_del_render(pintura, render, radio=RADIO_LUZ):
    """Textura de la pintura con la luz del render: se multiplica la pintura por el
    cociente entre la versión borrosa del render y la de la pintura (en luz lineal).
    Lo pequeño (grietas, vetas, pinceladas) viene de la pintura; lo grande (luna,
    sombras, color de conjunto), del render. Donde el render tiene luz cálida y viva
    (una vela, una ventana encendida) se deja la pintura tal cual."""
    P, R = _lineal(pintura), _lineal(render)
    Pb, Rb = _desenfoque(P, radio), _desenfoque(R, radio)
    transferida = P * (Rb + 1e-3) / (Pb + 1e-3)
    lum = render @ np.array([0.299, 0.587, 0.114]) / 255
    calidez = (render[..., 0] - render[..., 2]) / 255
    calida = np.clip((calidez - 0.12) / 0.18, 0, 1) * np.clip((lum - 0.3) / 0.2, 0, 1)
    calida = _desenfoque(calida[..., None], 3)
    return _srgb(transferida * (1 - calida) + P * calida)


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
    args.add_argument("--luz", choices=("pintura", "render"), default="pintura",
                      help="pintura: tal cual (por defecto); render: textura de la pintura con la luz del render")
    a = args.parse_args()

    ficha = json.loads((DIR_FICHAS / f"{a.pieza}.json").read_text(encoding="utf-8"))
    maq = ficha["maqueta"]
    tam_maq = tuple(maq["tamano"])
    mascara_img = Image.open(DIR_FICHAS / f"{a.pieza}_mascara.png").convert("L")
    mascara = np.asarray(mascara_img) > 127

    pintada = quitar_fondo(Image.open(a.pintada), a.tolerancia)
    # Restos de magenta dentro de la pieza (ChatGPT a veces deja rayitas junto a los
    # bordes): se tratan como huecos y ahí queda el render.
    px = np.asarray(pintada).astype(np.int16)
    restos = (np.minimum(px[..., 0], px[..., 2]) - px[..., 1] > 90) & (px[..., 0] > 150) & (px[..., 2] > 150)
    if restos.any():
        px[..., 3][restos] = 0
        pintada = Image.fromarray(px.astype(np.uint8), "RGBA")
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
    copia_render = DIR_FICHAS / f"{a.pieza}_render.png"     # lo escribe kit_calle_mayor.py
    if not copia_render.exists():
        shutil.copy(ruta_juego, copia_render)
    render = np.asarray(Image.open(copia_render).convert("RGBA")).astype(np.float32)
    pint = np.asarray(a_juego(alineada)).astype(np.float32)
    alfa_pint = pint[..., 3:4] / 255
    rgb = pint[..., :3] * alfa_pint + render[..., :3] * (1 - alfa_pint)
    if a.luz == "render":
        rgb = luz_del_render(rgb, render[..., :3])
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
    # Si el suelo del soportal de esta casa se igualó con el de sus vecinas, se rehace.
    from igualar_soportales import reaplicar
    reaplicar(a.pieza)
    # Se guarda la pintura original: si la pieza se vuelve a renderizar, basta con
    # pasar otra vez esta herramienta con ella.
    original = RAIZ / "arte/entrada/piezas" / f"{a.pieza}_pintada.png"
    original.parent.mkdir(parents=True, exist_ok=True)
    if a.pintada.resolve() != original.resolve():
        shutil.copy(a.pintada, original)
    print(f"Pieza del juego actualizada: {ruta_juego.relative_to(RAIZ)} (pintura guardada en "
          f"{original.relative_to(RAIZ)})")


if __name__ == "__main__":
    main()
