#!/usr/bin/env python3
"""Prepara imágenes generadas (ChatGPT u otra fuente) para meterlas en el juego.

  Fondo de escenario: escala y recorta a 2560 × 1440.
    python3 herramientas/procesar_arte.py fondo  entrada.png arte/fondos/calle_x.png

  Personaje u objeto: quita el fondo liso, recorta y escala a la medida del juego.
    python3 herramientas/procesar_arte.py figura entrada.png arte/personajes/x_se.png --altura 1.92
    (--altura en metros: alto TOTAL de la figura, sombrero incluido. Persona con sombrero ≈ 1,92.)

  Las dos poses de un personaje en una imagen (frente a la izquierda, espaldas a la derecha):
    python3 herramientas/procesar_arte.py poses entrada.png arte/personajes/x
    (escribe x_se.png y x_ne.png con la misma escala)

Si la imagen ya trae transparencia, se respeta. Si no, se toma como fondo el color
de las esquinas y se borra todo lo que se le parezca y esté conectado con ellas.
"""
import argparse
import math
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from isometria import ZH, ANCHO_FONDO, ALTO_FONDO


def fondo(entrada: Path, salida: Path):
    img = Image.open(entrada).convert("RGB")
    escala = max(ANCHO_FONDO / img.width, ALTO_FONDO / img.height)
    if escala > 1.3:
        print(f"Aviso: la imagen se amplía ×{escala:.2f}; se notará blanda. Pide más resolución si puedes.")
    nueva = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    x0 = (nueva.width - ANCHO_FONDO) // 2
    y0 = (nueva.height - ALTO_FONDO) // 2
    nueva.crop((x0, y0, x0 + ANCHO_FONDO, y0 + ALTO_FONDO)).save(salida, optimize=True)
    print(f"Fondo guardado: {salida} ({ANCHO_FONDO} × {ALTO_FONDO})")


def quitar_fondo(img: Image.Image, tolerancia: float) -> Image.Image:
    rgba = np.asarray(img.convert("RGBA")).astype(np.float32)
    if (rgba[..., 3] < 250).mean() > 0.02:
        return img.convert("RGBA")  # ya tiene transparencia útil
    rgb = rgba[..., :3]
    h, w = rgb.shape[:2]
    esquinas = np.array([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]])
    color_fondo = np.median(esquinas, axis=0)
    distancia = np.sqrt(((rgb - color_fondo) ** 2).sum(axis=2))
    parecido = distancia < tolerancia

    # Relleno desde los bordes: solo se borra el fondo conectado con el exterior,
    # así no se agujerean zonas del dibujo que casualmente tengan ese color.
    fuera = np.zeros((h, w), bool)
    cola = deque()
    for x in range(w):
        for y in (0, h - 1):
            if parecido[y, x] and not fuera[y, x]:
                fuera[y, x] = True
                cola.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if parecido[y, x] and not fuera[y, x]:
                fuera[y, x] = True
                cola.append((y, x))
    while cola:
        y, x = cola.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and parecido[ny, nx] and not fuera[ny, nx]:
                fuera[ny, nx] = True
                cola.append((ny, nx))

    # Bordes: los píxeles junto al fondo son mezcla de dibujo y fondo (antialias).
    # Con fondo magenta o verde se mide cuánto «color de fondo» les sobra;
    # con cualquier otro fondo, cuánto se parecen a él.
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    fr, fg, fb = color_fondo
    croma = (fr > 180 and fb > 180 and fg < 90) or (fg > 180 and fr < 90 and fb < 140)
    if croma:
        # Con magenta o verde puro, los huecos encerrados (entre un brazo y el cuerpo,
        # dentro de un asa) también son fondo, aunque no toquen el borde.
        fuera |= distancia < tolerancia * 0.6
    cerca = np.asarray(Image.fromarray((fuera * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
    if fr > 180 and fb > 180 and fg < 90:      # magenta
        sobra = np.clip((np.minimum(r, b) - g) / max(1.0, min(fr, fb) - fg), 0, 1)
    elif fg > 180 and fr < 90 and fb < 140:    # verde
        sobra = np.clip((g - np.maximum(r, b)) / max(1.0, fg - max(fr, fb)), 0, 1)
    else:
        sobra = 1 - np.clip((distancia - tolerancia * 0.6) / (tolerancia * 1.8), 0, 1)
    a = np.where(fuera, 0.0, np.where(cerca, 1 - sobra, 1.0)).astype(np.float32)
    # Quita el tinte del fondo en esos bordes semitransparentes.
    mezcla = np.clip((rgb - color_fondo * (1 - a[..., None])) / np.maximum(a[..., None], 0.05), 0, 255)
    rgb_limpio = np.where(a[..., None] > 0.02, mezcla, rgb)
    salida = np.dstack([rgb_limpio, a * 255]).astype(np.uint8)
    return Image.fromarray(salida, "RGBA")


def recortar(img: Image.Image) -> Image.Image:
    caja = img.split()[3].point(lambda v: 255 if v > 24 else 0).getbbox()
    if caja is None:
        sys.exit("No queda nada tras quitar el fondo: prueba con más --tolerancia o un fondo más liso.")
    return img.crop(caja)


def centro_de_pies(img: Image.Image) -> float:
    """Columna de los pies: el centro de masa del quinto inferior de la figura (piernas
    y pies). Con capas o brazos que sobresalen de un lado, la caja no está centrada en
    los pies y el personaje parecería desplazado al girarlo en espejo."""
    alfa = np.asarray(img.split()[3]).astype(np.float32)
    abajo = alfa[int(alfa.shape[0] * 0.8):]
    xs = np.arange(alfa.shape[1], dtype=np.float32)
    return float((abajo.sum(0) * xs).sum() / max(abajo.sum(), 1.0))


def colocar(img: Image.Image, escala: float, salida: Path):
    """Escala la figura y la pone en un lienzo con los pies centrados en horizontal y
    5 px de margen bajo las suelas: el origen del Personaje (los pies) queda en
    (ancho / 2, alto − 5). Personaje.cs calcula el desplazamiento con esa regla."""
    alto = round(img.height * escala)
    img = img.resize((max(1, round(img.width * escala)), alto), Image.LANCZOS)
    pies = centro_de_pies(img)
    medio = math.ceil(max(pies, img.width - pies)) + 8
    lienzo = Image.new("RGBA", (2 * medio, alto + 6), (0, 0, 0, 0))
    lienzo.paste(img, (round(medio - pies), 0), img)
    lienzo.save(salida)
    print(f"Figura guardada: {salida} ({lienzo.width} × {lienzo.height}).")


def figura(entrada: Path, salida: Path, altura_m: float, tolerancia: float):
    img = recortar(quitar_fondo(Image.open(entrada), tolerancia))
    colocar(img, altura_m * ZH / img.height, salida)


def poses(entrada: Path, base: Path, altura_m: float, tolerancia: float):
    """Las dos poses de un personaje en una sola imagen (como las pide la guía): a la
    izquierda de frente (SE), a la derecha de espaldas (NE). Las dos llevan la misma
    escala, la de la más alta, para que el personaje no cambie de tamaño al girarse."""
    img = quitar_fondo(Image.open(entrada), tolerancia)
    mitad = img.width // 2
    frente = recortar(img.crop((0, 0, mitad, img.height)))
    espalda = recortar(img.crop((mitad, 0, img.width, img.height)))
    escala = altura_m * ZH / max(frente.height, espalda.height)
    if abs(frente.height - espalda.height) > 0.04 * max(frente.height, espalda.height):
        print(f"Aviso: las dos poses no miden lo mismo ({frente.height} y {espalda.height} px); revísalas.")
    colocar(frente, escala, base.with_name(base.name + "_se.png"))
    colocar(espalda, escala, base.with_name(base.name + "_ne.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tipo", choices=["fondo", "figura", "poses"])
    ap.add_argument("entrada", type=Path)
    ap.add_argument("salida", type=Path, help="con «poses», la base del nombre (arte/personajes/x → x_se.png y x_ne.png)")
    ap.add_argument("--altura", type=float, default=1.92, help="alto total de la figura en metros")
    ap.add_argument("--tolerancia", type=float, default=48.0, help="cuánto puede variar el color del fondo")
    a = ap.parse_args()
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    if a.tipo == "fondo":
        fondo(a.entrada, a.salida)
    elif a.tipo == "poses":
        poses(a.entrada, a.salida, a.altura, a.tolerancia)
    else:
        figura(a.entrada, a.salida, a.altura, a.tolerancia)


if __name__ == "__main__":
    main()
