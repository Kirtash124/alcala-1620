#!/usr/bin/env python3
"""Fondo de la calle Mayor construido como maqueta: geometría por código y
texturas pintadas con ChatGPT (método de prueba frente al fondo pintado entero).

La geometría es la misma de arte_provisional.py, así que la zona transitable,
los oclusores y los puntos de interés de la escena siguen valiendo.

Texturas que usa (arte/entrada/texturas/):
  tex_cal.png              muros enfoscados (ocre; blanco y almagra se derivan)
  tex_empedrado.png, _b    calzada (se mezclan para que no se note la repetición)
  tex_empedrado_c.png      zócalo de cantos (provisional, hasta tener T05)
  tex_losas.png            suelo del soportal y canalillo
  tex_piedra.png, _b       columnas, basas, capiteles y balcones
Provisionales hechas por código, hasta tener las de ChatGPT: madera (T08) y teja (T09).

Uso:   python3 herramientas/maqueta_calle_mayor.py
Salida: arte/fondos/calle_mayor_texturas.png (2560 × 1440)
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

import arte_provisional as ap
from isometria import AX, AY, ZH, ANCHO_FONDO, ALTO_FONDO

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "arte/entrada/texturas"
ESC = 2                 # se pinta al doble de tamaño y se reduce: bordes limpios
DENS = 200              # píxeles de textura por metro, al doble de tamaño
LARGO, FONDO, FRENTE, ALTO = ap.LARGO, ap.FONDO_GALERIA, ap.FRENTE, ap.ALTO_SOPORTAL
RNG = np.random.default_rng(1620)

# Luz principal desde arriba a la izquierda (ver isometria.py). Con estos valores
# el suelo queda a 1, una cara que mira a +y a 0,89 y una que mira a +x a 0,64.
LUZ = np.array([-0.162, 0.566, 0.808])
AMBIENTE, DIFUSA = 0.643, 0.442


def sombreado(normal) -> float:
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    return AMBIENTE + DIFUSA * max(0.0, float(n @ LUZ))


# --------------------------------------------------------------- materiales

def periodico_suave(n: int, celdas: int, sigma: float) -> np.ndarray:
    """Ruido suave en [0, 1] que se repite sin costuras."""
    base = RNG.random((celdas, celdas)).astype(np.float32)
    grande = ndimage.zoom(np.tile(base, (3, 3)), n / celdas, order=3, mode="grid-wrap")[n:2 * n, n:2 * n]
    grande = ndimage.gaussian_filter(grande, sigma, mode="wrap")
    grande -= grande.min()
    return grande / (grande.max() + 1e-6)


def aplanar_tono(arr: np.ndarray, fuerza: float) -> np.ndarray:
    """Reduce las manchas grandes de luz y color de una textura (la suciedad la pongo yo)."""
    n = arr.shape[0]
    lum = arr @ np.array([0.299, 0.587, 0.114], np.float32)
    suave = ndimage.gaussian_filter(lum, n / 10, mode="wrap")
    factor = (lum.mean() / np.maximum(suave, 1.0)) ** fuerza
    return np.clip(arr * factor[..., None], 0, 255)


class Textura:
    """Textura repetible; se muestrea en metros sobre el plano de cada cara."""

    def __init__(self, fuente, metros: float, aplanar: float = 0.6, tinte=(1, 1, 1)):
        n = round(metros * DENS)
        img = fuente if isinstance(fuente, Image.Image) else Image.open(ENTRADA / fuente).convert("RGB")
        arr = np.asarray(img.resize((n, n), Image.LANCZOS)).astype(np.float32)
        if aplanar:
            arr = aplanar_tono(arr, aplanar)
        self.t = np.clip(arr * np.array(tinte, np.float32), 0, 255)
        self.n = n

    def muestrear(self, u, v):
        x = (u * DENS) % self.n
        y = (v * DENS) % self.n
        return np.stack([ndimage.map_coordinates(self.t[..., c], [y, x], order=1, mode="grid-wrap")
                         for c in range(3)], axis=-1)


class Mezcla:
    """Dos texturas que se alternan con manchas suaves de unos metros: rompe la repetición."""

    def __init__(self, a: Textura, b: Textura, metros_mancha: float = 3.0):
        self.a, self.b = a, b
        self.ruido = periodico_suave(512, 8, 18)
        self.periodo = metros_mancha * 4

    def muestrear(self, u, v):
        x = (u / self.periodo * 512) % 512
        y = (v / self.periodo * 512) % 512
        m = ndimage.map_coordinates(self.ruido, [y, x], order=1, mode="grid-wrap")
        m = np.clip((m - 0.5) * 5 + 0.5, 0, 1)[..., None]
        return self.a.muestrear(u, v) * (1 - m) + self.b.muestrear(u, v) * m


class Suciedad:
    """Variación de tono a gran escala (barro, humedad, desgaste), en metros del mundo."""

    def __init__(self, metros: float, fuerza: float, celdas: int = 10):
        self.ruido = periodico_suave(512, celdas, 10)
        self.metros, self.fuerza = metros, fuerza

    def factor(self, u, v):
        x = (u / self.metros * 512) % 512
        y = (v / self.metros * 512) % 512
        r = ndimage.map_coordinates(self.ruido, [y, x], order=1, mode="grid-wrap")
        return (1 - self.fuerza / 2 + self.fuerza * r)[..., None]


def madera(metros: float, tablas: float | None = None, tono=(96, 74, 56), vertical=False) -> Textura:
    """Madera vieja provisional (hasta tener T08): veta con ruido estirado y tablas opcionales."""
    n = round(metros * DENS)
    veta = periodico_suave(n, 6, 3)
    fino = ndimage.zoom(RNG.random((n, 6)).astype(np.float32), (1, n / 6), order=1, mode="grid-wrap")
    fino = ndimage.gaussian_filter(fino, (0.6, 12), mode="wrap")
    lum = 0.78 + 0.22 * veta + 0.28 * (fino - fino.mean())
    if tablas:
        paso = max(1, round(tablas * DENS))
        filas = np.arange(n)[:, None] % paso
        lum = lum * np.where(filas < 3, 0.45, 1.0)
        por_tabla = RNG.uniform(0.85, 1.12, n // paso + 1)
        lum = lum * por_tabla[np.arange(n) // paso][:, None]
    arr = np.clip(lum[..., None] * np.array(tono, np.float32), 0, 255)
    if vertical:
        arr = np.transpose(arr, (1, 0, 2))
    return Textura(Image.fromarray(arr.astype(np.uint8)), metros, aplanar=0)


def teja(metros: float = 2.0) -> Textura:
    """Teja árabe provisional (hasta tener T09): canal y cobija alternas, 11 hileras."""
    n = round(metros * DENS)
    arr = np.zeros((n, n, 3), np.float32)
    columnas, filas = 11, 4
    cw, fh = n / columnas, n / filas
    xx = np.arange(n)
    for c in range(columnas):
        x0, x1 = int(round(c * cw)), int(round((c + 1) * cw))
        t = (xx[x0:x1] - x0) / max(1, x1 - x0 - 1)
        convexa = c % 2 == 0
        perfil = np.sin(t * math.pi) if convexa else 1 - 0.55 * np.sin(t * math.pi)
        for f in range(filas):
            y0, y1 = int(round(f * fh)), int(round((f + 1) * fh))
            tono = np.array([158, 82, 52], np.float32) * RNG.uniform(0.78, 1.12)
            if RNG.random() < 0.2:
                tono = tono * np.array([1.05, 1.1, 0.8])       # liquen amarillento
            ty = (np.arange(y0, y1) - y0) / max(1, y1 - y0 - 1)
            solape = np.clip(1.0 - 0.45 * np.exp(-((1 - ty) * 9)), 0, 1)  # sombra de la teja de arriba
            bloque = (0.62 + 0.45 * perfil)[None, :] * solape[:, None]
            arr[y0:y1, x0:x1] = bloque[..., None] * tono
    ruido = periodico_suave(n, 40, 1.0)[..., None]
    arr = np.clip(arr * (0.88 + 0.24 * ruido), 0, 255)
    return Textura(Image.fromarray(arr.astype(np.uint8)), metros, aplanar=0)


def cal_variante(tono: str) -> Image.Image:
    """Deriva variantes de la cal de ChatGPT sin tocar los desconchones de ladrillo."""
    img = Image.open(ENTRADA / "tex_cal.png").convert("RGB")
    if tono == "ocre":
        return img
    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1], hsv[..., 2]
    peso = np.clip((h - 22) / 10, 0, 1) * np.clip((70 - h) / 10, 0, 1)
    blanco = Image.fromarray(np.dstack([hsv[..., 0], s * (1 - 0.72 * peso), np.clip(v * (1 + 0.10 * peso), 0, 255)])
                             .astype(np.uint8), "HSV").convert("RGB")
    if tono == "blanco":
        return blanco
    almagra = np.asarray(blanco).astype(np.float32) * np.array([0.86, 0.60, 0.50])
    return Image.fromarray(np.clip(almagra, 0, 255).astype(np.uint8))


# --------------------------------------------------------------- lienzo

class Lienzo:
    def __init__(self):
        self.W, self.H = ANCHO_FONDO * ESC, ALTO_FONDO * ESC
        self.ox, self.oy = ap.PR.ox * ESC, ap.PR.oy * ESC
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.grano = periodico_suave(512, 200, 0.7)

    def p(self, x, y, z=0.0):
        return (self.ox + (x - y) * AX * ESC, self.oy + (x + y) * AY * ESC - z * ZH * ESC)

    def lin(self, d):
        x, y, z = d
        return np.array([(x - y) * AX * ESC, (x + y) * AY * ESC - z * ZH * ESC])

    def _caja(self, pantalla, margen=0):
        xs = [q[0] for q in pantalla]
        ys = [q[1] for q in pantalla]
        x0 = max(0, int(math.floor(min(xs))) - margen)
        y0 = max(0, int(math.floor(min(ys))) - margen)
        x1 = min(self.W, int(math.ceil(max(xs))) + 1 + margen)
        y1 = min(self.H, int(math.ceil(max(ys))) + 1 + margen)
        return x0, y0, x1, y1

    def _mascara(self, pantalla, caja):
        x0, y0, x1, y1 = caja
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(a - x0, b - y0) for a, b in pantalla], fill=255)
        return np.asarray(m).astype(np.float32) / 255.0

    def cara(self, puntos, origen, eje_u, eje_v, material, luz=1.0, suciedad=None, desplaz=(0.0, 0.0)):
        """Rellena el polígono `puntos` (mundo) con `material` proyectado sobre su plano."""
        pantalla = [self.p(*q) for q in puntos]
        caja = self._caja(pantalla)
        x0, y0, x1, y1 = caja
        if x1 <= x0 or y1 <= y0:
            return
        M = np.column_stack([self.lin(eje_u), self.lin(eje_v)])
        if abs(np.linalg.det(M)) < 1e-6:
            return
        Minv = np.linalg.inv(M)
        O = np.array(self.p(*origen))
        mascara = self._mascara(pantalla, caja)
        for f0 in range(y0, y1, 384):           # por franjas, para no agotar la memoria
            f1 = min(y1, f0 + 384)
            m = mascara[f0 - y0:f1 - y0]
            if m.max() == 0:
                continue
            sy, sx = np.mgrid[f0:f1, x0:x1].astype(np.float32)
            d = np.stack([sx - O[0], sy - O[1]])
            u = Minv[0, 0] * d[0] + Minv[0, 1] * d[1] + desplaz[0]
            v = Minv[1, 0] * d[0] + Minv[1, 1] * d[1] + desplaz[1]
            col = material.muestrear(u, v) * luz
            if suciedad is not None:
                col = col * suciedad.factor(u, v)
            zona = self.rgb[f0:f1, x0:x1]
            zona[:] = zona * (1 - m[..., None]) + col * m[..., None]

    def plano(self, puntos, rgb, grano=0.06):
        """Polígono de color liso con un poco de grano."""
        pantalla = [self.p(*q) for q in puntos]
        self.plano_pantalla(pantalla, rgb, grano)

    def plano_pantalla(self, pantalla, rgb, grano=0.06):
        caja = self._caja(pantalla)
        x0, y0, x1, y1 = caja
        if x1 <= x0 or y1 <= y0:
            return
        m = self._mascara(pantalla, caja)[..., None]
        yy, xx = np.mgrid[y0:y1, x0:x1]
        g = self.grano[yy % 512, xx % 512][..., None]
        col = np.array(rgb, np.float32) * (1 - grano + 2 * grano * g)
        zona = self.rgb[y0:y1, x0:x1]
        zona[:] = zona * (1 - m) + col * m

    def sombra(self, puntos, intensidad, desenfoque_m=0.15, mundo=True):
        """Oscurece una zona con bordes suaves (oclusión ambiental, sombras de contacto)."""
        pantalla = [self.p(*q) for q in puntos] if mundo else puntos
        r = int(desenfoque_m * ZH * ESC)
        caja = self._caja(pantalla, margen=3 * r + 2)
        x0, y0, x1, y1 = caja
        if x1 <= x0 or y1 <= y0:
            return
        m = Image.fromarray((self._mascara(pantalla, caja) * 255).astype(np.uint8))
        if r:
            m = m.filter(ImageFilter.GaussianBlur(r))
        m = np.asarray(m).astype(np.float32)[..., None] / 255.0
        self.rgb[y0:y1, x0:x1] *= 1 - intensidad * m

    def linea(self, puntos, rgb, ancho_px):
        pantalla = [self.p(*q) for q in puntos]
        caja = self._caja(pantalla, margen=ancho_px + 2)
        x0, y0, x1, y1 = caja
        if x1 <= x0 or y1 <= y0:
            return  # fuera del encuadre
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).line([(a - x0, b - y0) for a, b in pantalla], fill=255, width=ancho_px, joint="curve")
        m = np.asarray(m.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)[..., None] / 255.0
        zona = self.rgb[y0:y1, x0:x1]
        zona[:] = zona * (1 - m) + np.array(rgb, np.float32) * m

    def punto(self, centro, radio_px, rgb):
        cx, cy = self.p(*centro)
        self.plano_pantalla([(cx + radio_px * math.cos(a), cy + radio_px * 0.75 * math.sin(a))
                             for a in np.linspace(0, 2 * math.pi, 10)], rgb, 0)

    # -------------------------------------------------- formas compuestas

    def caja3d(self, x0, y0, x1, y1, z0, z1, material, desplaz=(0.0, 0.0), suciedad=None):
        """Prisma: tapa, cara que mira a +y y cara que mira a +x, cada una con su luz."""
        self.cara([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (x0, y0, z1),
                  (1, 0, 0), (0, 1, 0), material, sombreado((0, 0, 1)), suciedad, desplaz)
        self.cara([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (x0, y1, z1),
                  (1, 0, 0), (0, 0, -1), material, sombreado((0, 1, 0)), suciedad, desplaz)
        self.cara([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (x1, y1, z1),
                  (0, -1, 0), (0, 0, -1), material, sombreado((1, 0, 0)), suciedad, desplaz)

    def cilindro(self, cx, cy, r, z0, z1, material, facetas=20, desplaz=(0.0, 0.0), tapa=None):
        """Cilindro vertical: solo la mitad que ve la cámara, en facetas con su luz."""
        angulos = np.linspace(-math.pi / 4, 3 * math.pi / 4, facetas + 1)
        for a, b in zip(angulos[:-1], angulos[1:]):
            m = (a + b) / 2
            pa = (cx + r * math.cos(a), cy + r * math.sin(a))
            pb = (cx + r * math.cos(b), cy + r * math.sin(b))
            eje = (pb[0] - pa[0], pb[1] - pa[1], 0)
            largo = math.hypot(eje[0], eje[1])
            self.cara([(*pa, z0), (*pb, z0), (*pb, z1), (*pa, z1)], (*pa, z1),
                      (eje[0] / largo, eje[1] / largo, 0), (0, 0, -1), material,
                      sombreado((math.cos(m), math.sin(m), 0)), None, (desplaz[0] + r * a, desplaz[1]))
        if tapa is not None:
            borde = [(cx + r * math.cos(a), cy + r * math.sin(a), z1) for a in np.linspace(0, 2 * math.pi, 32)]
            self.cara(borde, (cx, cy, z1), (1, 0, 0), (0, 1, 0), tapa, sombreado((0, 0, 1)))

    def resultado(self) -> Image.Image:
        img = Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))
        return img.resize((ANCHO_FONDO, ALTO_FONDO), Image.LANCZOS)


# --------------------------------------------------------------- escena

def construir() -> Image.Image:
    L = Lienzo()
    empedrado = Mezcla(Textura("tex_empedrado.png", 1.8, 0.7), Textura("tex_empedrado_b.png", 1.8, 0.7))
    losas = Textura("tex_losas.png", 1.7, 0.7)
    cantos_muro = Textura("tex_empedrado_c.png", 1.2, 0.6, tinte=(0.78, 0.76, 0.74))
    piedra = Textura("tex_piedra.png", 1.0, 0.5, tinte=(0.93, 0.92, 0.9))
    piedra_b = Textura("tex_piedra_b.png", 1.0, 0.5, tinte=(0.93, 0.92, 0.9))
    cales = {t: Textura(cal_variante(t), 2.0, 0.5) for t in ("ocre", "blanco", "almagra")}
    viga = madera(1.0, tono=(78, 60, 46))
    tablas_puerta = madera(1.0, tablas=0.2, tono=(88, 64, 46), vertical=True)
    tablas_carro = madera(1.0, tablas=0.22, tono=(104, 78, 54))
    duelas = madera(1.0, tablas=0.12, tono=(110, 80, 52), vertical=True)
    postigo = madera(1.0, tablas=0.16, tono=(74, 84, 66), vertical=True)
    tejado = teja(2.0)
    barro = Suciedad(7.0, 0.22, celdas=12)
    humedad = Suciedad(5.0, 0.22, celdas=14)
    p = L.p

    # Cielo de anochecer.
    for yy in range(0, 700 * ESC):
        t = yy / (700 * ESC)
        L.rgb[yy] = (28 + 30 * t, 32 + 30 * t, 48 + 30 * t)

    # Calle: dos empedrados mezclados y barro a gran escala.
    L.cara([(-20, -12, 0), (50, -12, 0), (50, 32, 0), (-20, 32, 0)], (0, 0, 0), (1, 0, 0), (0, 1, 0),
           empedrado, 1.0, barro)
    # Canalillo central: losas estrechas, más oscuras por la humedad.
    L.cara([(-10, 3.65, 0), (38, 3.65, 0), (38, 3.95, 0), (-10, 3.95, 0)], (0, 3.65, 0), (1, 0, 0), (0, 1, 0),
           Textura("tex_losas.png", 0.8, 0.7), 0.62, humedad)
    L.sombra([(-10, 3.6, 0), (38, 3.6, 0), (38, 4.0, 0), (-10, 4.0, 0)], 0.18, 0.05)

    # Suelo del soportal.
    L.cara([(0, FONDO, 0), (LARGO, FONDO, 0), (LARGO, 0.3, 0), (0, 0.3, 0)], (0, FONDO, 0), (1, 0, 0), (0, 1, 0),
           losas, 1.0, humedad)

    # Muro interior del soportal, por casas, con su zócalo de cantos.
    tramos = [(0, 5.5, "ocre"), (5.5, 11, "blanco"), (11, 16.5, "almagra"), (16.5, LARGO, "blanco")]
    for i, (x0, x1, tono) in enumerate(tramos):
        L.cara([(x0, FONDO, 0), (x1, FONDO, 0), (x1, FONDO, ALTO), (x0, FONDO, ALTO)], (x0, FONDO, ALTO),
               (1, 0, 0), (0, 0, -1), cales[tono], sombreado((0, 1, 0)), humedad, (i * 0.7, i * 0.37))
        L.cara([(x0, FONDO, 0), (x1, FONDO, 0), (x1, FONDO, 0.6), (x0, FONDO, 0.6)], (x0, FONDO, 0.6),
               (1, 0, 0), (0, 0, -1), cantos_muro, sombreado((0, 1, 0)) * 0.9, None, (i * 0.5, 0))
        L.sombra([(x1 - 0.04, FONDO, 0), (x1 + 0.04, FONDO, 0), (x1 + 0.04, FONDO, ALTO), (x1 - 0.04, FONDO, ALTO)], 0.35, 0.03)

    # Puertas de tablas claveteadas con su dintel.
    for px_ in [2.4, 8.2, 13.6, 19.6]:
        L.sombra([(px_ - 0.12, FONDO, 0), (px_ + 1.42, FONDO, 0), (px_ + 1.42, FONDO, 2.62), (px_ - 0.12, FONDO, 2.62)], 0.4, 0.04)
        L.cara([(px_, FONDO, 0), (px_ + 1.3, FONDO, 0), (px_ + 1.3, FONDO, 2.4), (px_, FONDO, 2.4)], (px_, FONDO, 2.4),
               (1, 0, 0), (0, 0, -1), tablas_puerta, sombreado((0, 1, 0)))
        L.cara([(px_ - 0.1, FONDO, 2.4), (px_ + 1.4, FONDO, 2.4), (px_ + 1.4, FONDO, 2.6), (px_ - 0.1, FONDO, 2.6)],
               (px_ - 0.1, FONDO, 2.6), (1, 0, 0), (0, 0, -1), viga, sombreado((0, 1, 0)))
        L.linea([(px_ + 0.65, FONDO, 0.03), (px_ + 0.65, FONDO, 2.38)], (30, 22, 16), 4)
        for zc in (0.5, 1.2, 1.9):
            for xc in np.arange(px_ + 0.12, px_ + 1.25, 0.2):
                L.punto((xc, FONDO, zc), 2.2, (34, 30, 28))
        L.punto((px_ + 0.9, FONDO, 1.15), 5, (40, 36, 34))           # aldaba

    # Hornacina con estampa, vela blanca y cera negra en la repisa. Va baja (repisa a 1 m)
    # y entre dos columnas en pantalla: si no, la taparían la viga o una columna.
    hx, z0 = ap.X_HORNACINA, ap.Z_HORNACINA
    nicho = [(hx, FONDO, z0), (hx + 0.55, FONDO, z0)]
    nicho += [(hx + 0.275 + 0.275 * math.cos(a), FONDO, z0 + 0.4 + 0.275 * math.sin(a)) for a in np.linspace(0, math.pi, 16)]
    L.cara(nicho, (hx, FONDO, z0 + 0.7), (1, 0, 0), (0, 0, -1), cales["blanco"], 0.5)
    L.sombra(nicho, 0.35, 0.05)
    L.plano([(hx + 0.15, FONDO, z0 + 0.22), (hx + 0.4, FONDO, z0 + 0.22), (hx + 0.4, FONDO, z0 + 0.58), (hx + 0.15, FONDO, z0 + 0.58)], (110, 82, 48), 0.1)
    L.plano([(hx + 0.21, FONDO, z0 + 0.27), (hx + 0.34, FONDO, z0 + 0.27), (hx + 0.34, FONDO, z0 + 0.52), (hx + 0.21, FONDO, z0 + 0.52)], (64, 52, 46), 0.1)
    L.caja3d(hx - 0.05, FONDO, hx + 0.6, FONDO + 0.12, z0 - 0.06, z0, piedra)
    L.plano([(hx + 0.23, FONDO + 0.06, z0), (hx + 0.32, FONDO + 0.06, z0), (hx + 0.32, FONDO + 0.06, z0 + 0.23), (hx + 0.23, FONDO + 0.06, z0 + 0.23)], (232, 223, 200), 0.02)
    for gx, gz in [(0.2, 0.0), (0.36, 0.0), (0.29, -0.02), (0.12, -0.04)]:
        L.punto((hx + gx, FONDO + 0.1, z0 + gz), 3, (14, 12, 14))
    llama = p(hx + 0.275, FONDO + 0.06, z0 + 0.29)
    L.plano_pantalla([(llama[0] + 5 * math.cos(a), llama[1] + 11 * math.sin(a) - 3) for a in np.linspace(0, 2 * math.pi, 14)], (255, 214, 130), 0)

    # Penumbra bajo el soportal: más oscuro arriba del muro y junto a él en el suelo.
    L.sombra([(0, FONDO, 0), (LARGO, FONDO, 0), (LARGO, FONDO, ALTO), (0, FONDO, ALTO)], 0.40, 0.3)
    L.sombra([(0, FONDO, ALTO - 0.9), (LARGO, FONDO, ALTO - 0.9), (LARGO, FONDO, ALTO), (0, FONDO, ALTO)], 0.35, 0.3)
    L.sombra([(0, FONDO, 0), (LARGO, FONDO, 0), (LARGO, 0.3, 0), (0, 0.3, 0)], 0.30, 0.4)
    L.sombra([(0, FONDO, 0), (LARGO, FONDO, 0), (LARGO, FONDO + 0.7, 0), (0, FONDO + 0.7, 0)], 0.30, 0.25)

    # Columnas de piedra, redondas, con basa, capitel y zapata de madera.
    for i, cx in enumerate(ap.COLUMNAS_X):
        mat = piedra if i % 2 == 0 else piedra_b
        L.sombra([(cx - 0.45, -0.1, 0), (cx + 0.5, -0.1, 0), (cx + 0.5, 0.6, 0), (cx - 0.45, 0.6, 0)], 0.40, 0.12)
        L.caja3d(cx - 0.26, -0.26, cx + 0.26, 0.26, 0, 0.32, mat, (i * 0.31, 0))
        L.cilindro(cx, 0, 0.17, 0.32, 3.12, mat, desplaz=(i * 0.43, i * 0.2))
        L.sombra([(cx - 0.18, 0.18, 0.32), (cx + 0.18, 0.18, 0.32), (cx + 0.18, 0.18, 0.5), (cx - 0.18, 0.18, 0.5)], 0.25, 0.05)
        L.caja3d(cx - 0.25, -0.25, cx + 0.25, 0.25, 3.12, 3.35, mat, (i * 0.17, 0))
        L.caja3d(cx - 0.65, -0.18, cx + 0.65, 0.18, 3.35, 3.6, viga, (i * 0.29, 0))

    # Viga corrida, fachada alta por casas, ventanas y balcones.
    L.cara([(0, FRENTE, 3.6), (LARGO + 0.3, FRENTE, 3.6), (LARGO + 0.3, FRENTE, 3.85), (0, FRENTE, 3.85)],
           (0, FRENTE, 3.85), (1, 0, 0), (0, 0, -1), viga, sombreado((0, 1, 0)))
    fachada = [(0, 5.5, "ocre"), (5.5, 11, "blanco"), (11, 16.5, "almagra"), (16.5, LARGO + 0.3, "ocre")]
    encendidas = {(5.5, 1), (16.5, 0)}
    for i, (x0, x1, tono) in enumerate(fachada):
        L.cara([(x0, FRENTE, 3.85), (x1, FRENTE, 3.85), (x1, FRENTE, 7.0), (x0, FRENTE, 7.0)], (x0, FRENTE, 7.0),
               (1, 0, 0), (0, 0, -1), cales[tono], sombreado((0, 1, 0)), humedad, (i * 0.9 + 0.3, i * 0.55))
        L.sombra([(x0, FRENTE, 6.5), (x1, FRENTE, 6.5), (x1, FRENTE, 7.0), (x0, FRENTE, 7.0)], 0.40, 0.25)
        L.sombra([(x0, FRENTE, 3.85), (x1, FRENTE, 3.85), (x1, FRENTE, 4.1), (x0, FRENTE, 4.1)], 0.25, 0.08)
        L.sombra([(x1 - 0.04, FRENTE, 3.85), (x1 + 0.04, FRENTE, 3.85), (x1 + 0.04, FRENTE, 7.0), (x1 - 0.04, FRENTE, 7.0)], 0.4, 0.03)
        for k, vx in enumerate((x0 + 1.4, x0 + 3.8)):
            if vx + 1.0 > x1:
                continue
            hueco = [(vx, FRENTE, 4.6), (vx + 1.0, FRENTE, 4.6), (vx + 1.0, FRENTE, 6.1), (vx, FRENTE, 6.1)]
            if (x0, k) in encendidas:
                L.plano(hueco, (226, 168, 88), 0.05)
                L.sombra([(vx, FRENTE, 5.6), (vx + 1.0, FRENTE, 5.6), (vx + 1.0, FRENTE, 6.1), (vx, FRENTE, 6.1)], 0.35, 0.15)
            else:
                L.plano(hueco, (30, 26, 24), 0.05)
            L.sombra([(vx - 0.06, FRENTE, 4.54), (vx + 1.06, FRENTE, 4.54), (vx + 1.06, FRENTE, 6.16), (vx - 0.06, FRENTE, 6.16)], 0.3, 0.04)
            L.cara([(vx - 0.42, FRENTE, 4.6), (vx - 0.02, FRENTE, 4.6), (vx - 0.02, FRENTE, 6.1), (vx - 0.42, FRENTE, 6.1)],
                   (vx - 0.42, FRENTE, 6.1), (1, 0, 0), (0, 0, -1), postigo, sombreado((0, 1, 0)))
            # Balcón: losa de piedra, su sombra en la fachada y barandilla de forja.
            L.sombra([(vx - 0.15, FRENTE, 4.05), (vx + 1.15, FRENTE, 4.05), (vx + 1.15, FRENTE, 4.35), (vx - 0.15, FRENTE, 4.35)], 0.35, 0.06)
            L.caja3d(vx - 0.15, FRENTE, vx + 1.15, FRENTE + 0.4, 4.27, 4.35, piedra_b)
            for bx in np.arange(vx - 0.1, vx + 1.12, 0.12):
                L.linea([(bx, FRENTE + 0.36, 4.35), (bx, FRENTE + 0.36, 5.05)], (24, 22, 22), 3)
            L.linea([(vx - 0.13, FRENTE + 0.36, 5.05), (vx + 1.13, FRENTE + 0.36, 5.05)], (24, 22, 22), 5)
            L.linea([(vx - 0.13, FRENTE + 0.36, 4.42), (vx + 1.13, FRENTE + 0.36, 4.42)], (24, 22, 22), 4)

    # Alero de madera y tejado.
    L.cara([(0, FRENTE, 7.0), (LARGO + 0.3, FRENTE, 7.0), (LARGO + 0.3, FRENTE + 0.5, 6.92), (0, FRENTE + 0.5, 6.92)],
           (0, FRENTE, 7.0), (1, 0, 0), (0, 1, 0), viga, 0.7)
    pendiente = np.array([0, -4.5 - (FRENTE + 0.5), 9.1 - 6.92])
    pendiente = tuple(pendiente / np.linalg.norm(pendiente))
    normal_tejado = np.cross(pendiente, (1, 0, 0))
    L.cara([(0, FRENTE + 0.5, 6.92), (LARGO + 0.3, FRENTE + 0.5, 6.92), (LARGO + 0.3, -4.5, 9.1), (0, -4.5, 9.1)],
           (0, -4.5, 9.1), (1, 0, 0), tuple(-np.array(pendiente)), tejado, sombreado(normal_tejado), barro)

    # Fachada lateral del último edificio.
    L.cara([(LARGO + 0.3, FONDO, 3.6), (LARGO + 0.3, FRENTE + 0.5, 3.6), (LARGO + 0.3, FRENTE + 0.5, 6.92),
            (LARGO + 0.3, -2.0, 8.1), (LARGO + 0.3, -4.5, 9.1), (LARGO + 0.3, -4.5, 3.6)],
           (LARGO + 0.3, FRENTE + 0.5, 9.1), (0, -1, 0), (0, 0, -1), cales["blanco"], sombreado((1, 0, 0)), humedad)

    # Carro de tablas.
    cx0, cx1, cy0, cy1 = 6.2, 9.1, 6.1, 7.0
    L.sombra([(cx0 - 0.3, cy0 - 0.1, 0), (cx1 + 0.5, cy0 - 0.1, 0), (cx1 + 0.5, cy1 + 0.7, 0), (cx0 - 0.3, cy1 + 0.7, 0)], 0.45, 0.2)
    L.linea([(cx0, cy0 + 0.2, 0.9), (cx0 - 2.0, cy0 + 0.2, 0.25)], (70, 52, 36), 10)
    L.caja3d(cx0, cy0, cx1, cy1, 0.65, 1.1, tablas_carro)
    L.sombra([(cx0, cy1, 0.65), (cx1, cy1, 0.65), (cx1, cy1, 0.8), (cx0, cy1, 0.8)], 0.3, 0.04)
    for vx in (6.75, 8.45):
        rueda = [(vx + 0.55 * math.cos(a), cy1 + 0.06, 0.58 + 0.55 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)]
        L.linea(rueda, (52, 38, 26), 12)
        for a in np.linspace(0, math.pi, 5, endpoint=False):
            L.linea([(vx + 0.52 * math.cos(a), cy1 + 0.06, 0.58 + 0.52 * math.sin(a)),
                     (vx - 0.52 * math.cos(a), cy1 + 0.06, 0.58 - 0.52 * math.sin(a))], (60, 44, 30), 6)
        L.punto((vx, cy1 + 0.06, 0.58), 7, (40, 30, 22))
    L.linea([(cx0, cy1 - 0.2, 0.9), (cx0 - 2.0, cy1 - 0.2, 0.25)], (80, 60, 40), 10)

    # Barriles de duelas con aros de hierro.
    for bx, by in [(19.0, 6.55), (19.75, 6.85)]:
        L.sombra([(bx - 0.45, by - 0.3, 0), (bx + 0.6, by - 0.3, 0), (bx + 0.6, by + 0.6, 0), (bx - 0.45, by + 0.6, 0)], 0.45, 0.1)
        L.cilindro(bx, by, 0.33, 0, 0.95, duelas, facetas=16, tapa=madera(0.66, tono=(118, 90, 60)))
        for zz in (0.12, 0.42, 0.83):
            L.linea([(bx + 0.335 * math.cos(a), by + 0.335 * math.sin(a), zz)
                     for a in np.linspace(-math.pi / 4, 3 * math.pi / 4, 16)], (36, 34, 34), 5)

    # Viñeteado suave para centrar la mirada.
    yy, xx = np.mgrid[0:L.H, 0:L.W].astype(np.float32)
    dist = np.sqrt(((xx - L.W / 2) / (L.W / 2)) ** 2 + ((yy - L.H / 2) / (L.H / 2)) ** 2)
    L.rgb *= np.clip(1.08 - 0.28 * dist ** 2, 0.6, 1.0)[..., None]
    return L.resultado()


if __name__ == "__main__":
    destino = RAIZ / "arte/fondos/calle_mayor_texturas.png"
    construir().save(destino, optimize=True)
    print(f"Fondo con texturas guardado en {destino.relative_to(RAIZ)}")
