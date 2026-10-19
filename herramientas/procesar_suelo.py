#!/usr/bin/env python3
"""Cose los trozos del suelo pintados por ChatGPT y los mete en el juego.

    python3 herramientas/procesar_suelo.py suelo_1=~/Descargas/a.png suelo_3=b.png
    python3 herramientas/procesar_suelo.py            # con lo que ya hay en arte/entrada/suelo/

El suelo mide 3200 × 1800 y ChatGPT no pinta tanto de una vez, así que se pide en
cuatro trozos con solape (docs/arte/suelo/suelo_N_luz.png; ver docs/arte/suelo/README.md).

1. A cada trozo le quita el magenta (donde van las casas), lo encaja sobre su silueta y
   limpia la pelusa morada que ChatGPT deja junto a las casas.
2. Iguala el color entre trozos: con lo que coincide en los solapes calcula, por canal,
   una ganancia para cada trozo, para que ninguno quede más claro o más cálido que su
   vecino.
3. Los cose por una costura de coste mínimo dentro de cada solape: el camino por donde
   los dos trozos más se parecen (como en el «image quilting» de Efros y Freeman, 2001),
   con un fundido corto. Un fundido ancho dejaba fantasmas, porque ChatGPT no pinta
   igual el mismo charco en dos trozos.
4. Ajusta el brillo a la noche de la escena (ajustar_a_la_noche; --tal-cual para no
   hacerlo): solo la luz, no el color de la pintura.
5. Donde no hay pintura (un trozo aún sin pintar, o bajo las casas) queda el render
   (herramientas/datos/suelo_render.png). Las sombras del carro, los barriles y las
   casas no hacen falta en la pintura: las pone el juego (Pieza.Sombra).

Guarda arte/fondos/calle_mayor_suelo.png, copia cada pintura original en
arte/entrada/suelo/ y deja una comprobación en pruebas/salida/suelo_comprobacion.png.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

from procesar_pieza import encajar, transformar

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "herramientas/datos"
ENTRADA = RAIZ / "arte/entrada/suelo"
FUNDIDO = 5.0          # sigma, en px del juego, del fundido a lo largo de la costura
# Brillo de la pintura respecto al render. Medido en las losas de los soportales: las
# casas que pintó ChatGPT quedaron un 20-25 % más oscuras que el render, y el suelo
# tiene que ir con ellas.
NOCHE = 0.8
CONTRASTE_MAX = 1.4    # exponente máximo de la curva de ajustar_a_la_noche


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


def limpiar_bordes(pint, mascara):
    """ChatGPT deja junto al magenta una franja de unos 5 px con pelusa morada que no es
    magenta puro (quitar_magenta no la borra entera) y en el juego se ve como un ribete
    a lo largo de las casas. Esos píxeles se rellenan con el color de la pintura limpia
    más cercana, y la silueta pasa a ser la de la máscara del render (exacta), ensanchada
    12 px bajo las casas: el pie de las casas sale dentado en el render (lo mordían las
    piedras de Blender) y por esas muescas no debe asomar el negro de debajo."""
    px = np.asarray(pint).astype(np.float32)
    rgb, alfa = px[..., :3], px[..., 3] / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # En el barro y la piedra el verde nunca queda por debajo del rojo y el azul a la
    # vez; en la pelusa morada, sí.
    sucio = binary_dilation((np.minimum(r, b) - g > 10) | (alfa < 0.98), iterations=1)
    limpio = mascara & ~sucio
    zona = binary_dilation(mascara, iterations=12)
    _, (iy, ix) = distance_transform_edt(~limpio, return_indices=True)
    relleno = np.where((zona & ~limpio)[..., None], rgb[iy, ix], rgb)
    salida = np.dstack([relleno, zona * 255.0]).astype(np.uint8)
    print(f"  bordes: {int((zona & ~limpio).sum())} px rellenados")
    return Image.fromarray(salida, "RGBA")


def cargar_pintura(ruta, mascara):
    pint = quitar_magenta(Image.open(ruta))
    if pint.size != mascara.shape[::-1]:
        pint = pint.resize(mascara.shape[::-1], Image.LANCZOS)
        print(f"  aviso: {ruta.name} venía a otro tamaño; se ajusta")
    puntos, escala, dx, dy = encajar(pint, mascara)
    pint = limpiar_bordes(transformar(pint, escala, dx, dy, mascara.shape[::-1]), mascara)
    return pint, puntos, (escala, dx, dy)


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


def camino_minimo(coste):
    """Costura de arriba abajo de coste mínimo (programación dinámica): la columna de
    cada fila, moviéndose como mucho un píxel a un lado entre fila y fila."""
    h, w = coste.shape
    acum = coste.astype(np.float64).copy()
    for y in range(1, h):
        prev = acum[y - 1]
        acum[y] += np.minimum(np.minimum(np.r_[np.inf, prev[:-1]], prev), np.r_[prev[1:], np.inf])
    camino = np.empty(h, int)
    camino[-1] = int(np.argmin(acum[-1]))
    for y in range(h - 2, -1, -1):
        x = camino[y + 1]
        lo = max(0, x - 1)
        camino[y] = lo + int(np.argmin(acum[y, lo:x + 2]))
    return camino


def coser(capas, rects, lienzo):
    """Une los trozos pintados de uno en uno, empezando por el que más calle pinta. En el
    solape de cada trozo nuevo con lo ya cosido busca la costura por donde los dos se
    parecen más (bajo las casas no cuesta nada, porque no se ve) y reparte a cada lado.
    Devuelve el color y la cobertura de la pintura en el lienzo."""
    w, h = lienzo
    color = np.zeros((h, w, 3), np.float32)
    alfa = np.zeros((h, w), np.float32)
    cubierto = np.zeros((h, w), bool)
    orden = sorted((i for i, c in enumerate(capas) if c is not None), key=lambda i: -capas[i][..., 3].sum())
    margen = int(3 * FUNDIDO) + 2
    for i in orden:
        capa, r = capas[i], rects[i]
        # Rectángulo del trozo, sin los 2 px del borde (allí el remuestreo lo deja a medias).
        x0, y0 = int(np.ceil(r[0])) + (2 if r[0] > 0.5 else 0), int(np.ceil(r[1])) + (2 if r[1] > 0.5 else 0)
        x1 = int(np.floor(r[0] + r[2])) - (2 if r[0] + r[2] < w - 0.5 else 0)
        y1 = int(np.floor(r[1] + r[3])) - (2 if r[1] + r[3] < h - 0.5 else 0)
        suyo = np.zeros((h, w), bool)
        suyo[y0:y1, x0:x1] = True
        lado = suyo & ~cubierto
        solape = suyo & cubierto
        if solape.any():
            ys, xs = np.where(solape)
            oy0, oy1, ox0, ox1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            caja = (slice(oy0, oy1), slice(ox0, ox1))
            a = gaussian_filter(capa[caja][..., :3], (1.5, 1.5, 0))
            b = gaussian_filter(color[caja], (1.5, 1.5, 0))
            ambos = (capa[caja][..., 3] > 0.5) & (alfa[caja] > 0.5)
            coste = np.where(ambos, np.abs(a - b).sum(-1), 0.0) + 1e-3
            coste[~solape[caja]] = 1e3
            vertical = (oy1 - oy0) >= (ox1 - ox0)
            if not vertical:
                coste = coste.T
            # Que la costura no pegue a los bordes del solape: el fundido necesita sitio.
            coste[:, :margen] += 1e3
            coste[:, -margen:] += 1e3
            camino = camino_minimo(coste)
            idx = np.arange(coste.shape[1])[None, :]
            # Lado del trozo nuevo: hacia donde cae su centro respecto al solape.
            if vertical:
                nuevo_despues = r[0] + r[2] / 2 > (ox0 + ox1) / 2
            else:
                nuevo_despues = r[1] + r[3] / 2 > (oy0 + oy1) / 2
            parte = idx > camino[:, None] if nuevo_despues else idx <= camino[:, None]
            lado[caja] |= (parte if vertical else parte.T) & solape[caja]
            print(f"  costura {'vertical' if vertical else 'horizontal'} en el solape "
                  f"x {ox0}-{ox1}, y {oy0}-{oy1}; diferencia media en ella {coste[np.arange(len(camino)), camino].mean():.3f}")
        # Fundido corto a lo largo de la costura; donde solo pinta uno, manda ese.
        peso = gaussian_filter(lado.astype(np.float32), FUNDIDO)
        peso = np.where(suyo & ~cubierto, 1.0, np.where(cubierto & ~suyo, 0.0, peso))
        peso = np.where(suyo | cubierto, peso, 0.0)
        wn, wv = peso * capa[..., 3], (1 - peso) * alfa
        total = wn + wv
        nuevo = (capa[..., :3] * wn[..., None] + color * wv[..., None]) / np.maximum(total, 1e-6)[..., None]
        color = np.where((total > 1e-6)[..., None], nuevo, color)
        alfa = np.where(suyo, np.maximum(alfa, capa[..., 3]), alfa)
        cubierto |= suyo
    return color, alfa


def ajustar_a_la_noche(color, alfa, render):
    """Lleva el brillo de la pintura al de la noche de la escena: una curva de potencia
    (Y' = A·Y^g) que pone sus percentiles 5 a 95 de luminancia en los del render por
    NOCHE. Multiplica los tres canales por igual, así que el color de la pintura no
    cambia, solo su luz. Sin esto, un suelo pintado de día o con niebla queda mucho
    más claro que las casas."""
    sel = alfa > 0.5
    pesos = np.array([0.2126, 0.7152, 0.0722], np.float32)
    y = np.maximum((color * pesos).sum(-1), 1e-4)
    yr = np.maximum((render * pesos).sum(-1), 1e-4)
    p = np.arange(5, 96, 5)
    origen = np.percentile(y[sel], p)
    destino = np.percentile(yr[sel], p) * NOCHE
    g, _ = np.polyfit(np.log(origen), np.log(destino), 1)
    # El contraste del render es el de su empedrado; a una pintura suave no se le
    # sube más de CONTRASTE_MAX, que la textura se vuelve áspera. La mediana sí se iguala.
    g = float(np.clip(g, 1.0, CONTRASTE_MAX))
    log_a = np.log(np.median(destino)) - g * np.log(np.median(origen))
    factor = np.where(sel, np.exp(log_a) * y ** g / y, 1.0)[..., None]
    print(f"Noche: luminancia mediana {np.median(y[sel]) * 255:.0f} → {np.median(destino) * 255:.0f} "
          f"(curva Y' = {np.exp(log_a):.2f}·Y^{g:.2f})")
    return np.clip(color * factor, 0, 1)


def main():
    ficha = json.loads((DATOS / "suelo.json").read_text(encoding="utf-8"))
    lienzo = tuple(ficha["lienzo"])
    escala = ficha["escala"]
    teselas = ficha["teselas"]
    ENTRADA.mkdir(parents=True, exist_ok=True)

    # Pinturas nuevas pasadas como suelo_N=ruta: se guardan en arte/entrada/suelo.
    # Con --tal-cual no se ajusta el brillo a la noche de la escena.
    tal_cual = "--tal-cual" in sys.argv
    for arg in (a for a in sys.argv[1:] if not a.startswith("--")):
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
    for i, capa in enumerate(capas):
        if capa is not None:
            capa[..., :3] = np.clip(capa[..., :3] * g[i], 0, 1)
    color, alfa = coser(capas, rects, lienzo)
    if not tal_cual:
        color = ajustar_a_la_noche(color, alfa, render)
    # Donde no hay pintura (bajo las casas o en un trozo sin pintar) queda el render.
    final = color * alfa[..., None] + render * (1 - alfa[..., None])
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
