#!/usr/bin/env python3
"""Kit de piezas de la calle Mayor, modelado y renderizado en Blender por código.

El escenario se compone de piezas sueltas (casas, carro, barriles). Cada pieza se
modela con geometría de verdad (cada teja, cada tabla, cada clavo, cada balaustre)
y se renderiza con la cámara exacta del juego. Para cada pieza salen:

  arte/piezas/<id>.png                   pieza para el juego, con la luz de noche ya hecha
  arte/piezas/<id>_sombra.png            sombra que echa en el suelo (el juego la pone encima)
  docs/arte/piezas/<id>_luz.png          estudio de luz a tamaño de ChatGPT, sobre magenta
  docs/arte/piezas/<id>_maqueta.png      maqueta de forma (arcilla), sobre magenta
  herramientas/datos/piezas/<id>.json    ficha: ancla, huella, recortes, escala de la maqueta
  herramientas/datos/piezas/<id>_mascara.png   silueta de la maqueta (para comprobar la pintada)
Y además:
  arte/fondos/calle_mayor_suelo.png      suelo de la calle
  herramientas/datos/calle_mayor.json    composición de la escena (la usa generar_calle_mayor.py)

Toda la calle se construye a la vez: al renderizar una pieza, las demás no salen en
la imagen pero siguen haciendo sombra y reflejando luz, así que las sombras entre
vecinas son las de verdad.

Requisitos: pip install bpy (Python 3.13), scikit-image.
Uso:  python3 herramientas/kit_calle_mayor.py [--solo casa_3 ...] [--sin-suelo] [--rapido] [--sombras]

Coordenadas del mundo en metros: x a lo largo de la calle (hacia abajo a la derecha en
pantalla), y hacia la calle (abajo a la izquierda), z arriba. Ver isometria.py.
"""
import argparse
import json
import math
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent / "blender"))
import base as BL           # noqa: E402
import materiales as MAT    # noqa: E402
import modelos as MD        # noqa: E402
from isometria import AX, AY, ZH   # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DIR_MAQUETAS = RAIZ / "docs/arte/piezas"
DIR_PIEZAS = RAIZ / "arte/piezas"
DIR_FICHAS = RAIZ / "herramientas/datos/piezas"
DIR_TEXTURAS = RAIZ / "herramientas/datos/texturas"

# ------------------------------------------------------------- medidas comunes

ANCHO_CASA = 6.0       # fachada de cada casa (m)
FONDO = -2.0           # cara del muro interior del soportal (y)
GROSOR_FONDO = 0.3
FRENTE = 0.25          # cara de la fachada alta, sobre las columnas (y)
GROSOR_FACHADA = 0.4
ALTO_SOPORTAL = 3.6    # altura libre hasta la viga (m)
ALTO_VIGA = 3.86       # cara superior de la viga
SUELO_ALTO = 4.0       # suelo de la planta principal
FONDO_TEJADO = -4.5    # cumbrera del tejado (y)
SUBIDA_TEJADO = 2.1    # de alero a cumbrera (m)
VUELO_ALERO = 0.55
COLUMNAS = (1.5, 4.5)  # columnas de cada casa (x local)
HUECOS = (1.0, 4.0)    # centros de lo que se ve del muro interior entre columnas (x local)
Z_HORNACINA = 1.0      # repisa de la hornacina (más arriba la tapa la viga desde esta cámara)
LIMITE_VISIBLE = 1.76  # altura del muro interior que deja ver la viga del soportal
VENTANA = (4.95, 6.15) # alféizar y dintel de las ventanas altas
PUERTA_BALCON = (4.05, 6.05)

# Suelo de la escena (lienzo del fondo, a escala del juego).
SUELO_ANCHO, SUELO_ALTO_PX = 3200, 1800
SUELO_OX, SUELO_OY = 710.0, 450.0

# Luz de la escena. La luna entra de arriba a la izquierda de la pantalla y rasante
# a las fachadas, para que el relieve se lea y los soportales queden en penumbra.
LUNA = (-0.5, 0.33, 0.8)
LUNA_FUERZA = 0.8
LUNA_COLOR = (0.66, 0.76, 1.0)
CIELO_COLOR = (0.010, 0.013, 0.024)
CIELO_FUERZA = 2.5
CALIDA = (1.0, 0.56, 0.24)       # vela, candil
TONO_PERSONAJES = (0.6, 0.62, 0.76)   # los personajes son dibujos neutros: se apagan y enfrían de noche
EXPOSICION = 3.5


def pantalla(x, y, z=0.0, ox=0.0, oy=0.0):
    return (ox + (x - y) * AX, oy + (x + y) * AY - z * ZH)


# ------------------------------------------------------------- piezas

@dataclass
class Casa:
    id: str
    nombre: str
    x0: float                    # posición en la calle (m)
    tono: str                    # color del enlucido: ocre, blanco o almagra
    alero: float                 # altura del alero (m)
    bajos: dict                  # hueco (1.0 o 4.0) -> puerta, tienda, tienda_velas, ventana_baja, hornacina
    altos: dict                  # hueco -> balcon, ventana, balcon_luz, ventana_luz
    esquina: bool = False
    fondo: bool = True           # se dibuja detrás de los personajes; las columnas los tapan
    desvan: float = None         # x local de un ventanuco de desván, si cabe
    argolla: int = None          # índice de la columna con argolla de atar

    @property
    def cumbrera(self):
        return self.alero + SUBIDA_TEJADO

    def columnas(self):
        cols = list(COLUMNAS)
        if self.esquina:
            cols.append(ANCHO_CASA - 0.18)
        return cols

    def huella(self):
        """Obstáculos de la casa dentro de la zona transitable: solo las columnas."""
        return [[(c - 0.3, -0.3), (c + 0.3, -0.3), (c + 0.3, 0.3), (c - 0.3, 0.3)] for c in self.columnas()]

    def origen(self):
        return (self.x0, 0.0, 0.0)


@dataclass
class Objeto:
    id: str
    nombre: str
    origen_xy: tuple             # posición del origen local en la calle (m)
    fondo: bool = False
    huella_local: list = field(default_factory=list)

    def huella(self):
        return [self.huella_local] if self.huella_local else []

    def origen(self):
        return (self.origen_xy[0], self.origen_xy[1], 0.0)


CASAS = [
    Casa("casa_1", "Casa del zapatero", 0.0, "ocre", 6.6,
         {1.0: "puerta", 4.0: "tienda"}, {1.0: "balcon", 4.0: "ventana"}),
    Casa("casa_2", "Casa de la ventana encendida", 6.0, "blanco", 7.0,
         {1.0: "puerta", 4.0: "ventana_baja"}, {1.0: "balcon", 4.0: "balcon_luz"}),
    Casa("casa_3", "Casa de la hornacina", 12.0, "almagra", 7.6,
         {1.0: "hornacina", 4.0: "puerta"}, {1.0: "ventana", 4.0: "balcon"}, desvan=4.0, argolla=0),
    Casa("casa_4", "Cerería de la esquina", 18.0, "blanco", 7.0,
         {1.0: "puerta", 4.0: "tienda_velas"}, {1.0: "balcon_luz", 4.0: "ventana"}, esquina=True),
]

CARRO = Objeto("carro", "Carro de varas", (9.1, 7.0), huella_local=[(-4.9, -1.0), (0.1, -1.0), (0.1, 0.15), (-4.9, 0.15)])
BARRILES = Objeto("barriles", "Dos barriles", (19.983, 7.083),
                  huella_local=[(-1.35, -0.9), (0.1, -0.9), (0.1, 0.1), (-1.35, 0.1)])
OBJETOS = [CARRO, BARRILES]


# ------------------------------------------------------------- construcción

def hueco_bajo(tipo, sx):
    """Rectángulo (x0, x1, z0, z1) que se abre en el muro del soportal para cada cosa."""
    if tipo == "puerta":
        return (sx - 0.8, sx + 0.8, 0.0, 2.62)
    if tipo in ("tienda", "tienda_velas"):
        return (sx - 0.95, sx + 0.95, 0.0, 2.34)
    if tipo == "ventana_baja":
        return (sx - 0.55, sx + 0.55, 0.81, 2.11)
    if tipo == "hornacina":
        return (sx - 0.275, sx + 0.275, Z_HORNACINA, Z_HORNACINA + 0.675)
    raise ValueError(tipo)


def hueco_alto(tipo, sx):
    if tipo.startswith("balcon"):
        return (sx - 0.5, sx + 0.5, PUERTA_BALCON[0], PUERTA_BALCON[1])
    return (sx - 0.5, sx + 0.5, VENTANA[0], VENTANA[1])


def techo_en(casa, y):
    """Altura del faldón del tejado sobre la vertical y."""
    y_alero = FRENTE + VUELO_ALERO + 0.1
    z_alero = casa.alero + 0.035
    t = (y_alero - y) / (y_alero - FONDO_TEJADO)
    return z_alero + t * (casa.cumbrera - z_alero)


def construir_casa(casa: Casa, vecina_derecha):
    """Modela la casa entera. Devuelve el objeto, las siluetas de sus columnas y sus luces."""
    m = BL.Malla(casa.id, semilla=int(casa.x0 * 7) + 3)
    X, W = casa.x0, ANCHO_CASA
    cal = f"cal_{casa.tono}"
    luces = []

    # Suelo del soportal: losas sobre un lecho de mortero (por las juntas se ve el
    # mortero, no la tierra de la calle) y bordillo hacia la calle.
    m.caja(X, FONDO - 0.02, -0.08, X + W, 0.44, -0.012, "mortero")
    MD.losas(m, X, X + W, FONDO - 0.02, 0.2)
    x = X - m.azar(0, 0.6)
    while x < X + W:
        xb = x + m.azar(0.8, 1.3)
        a, b = max(x, X), min(xb, X + W)
        if b - a > 0.1:
            m.caja(a + 0.006, 0.2, -0.15, b - 0.006, 0.44, m.azar(0.015, 0.03), "piedra_b", bisel=0.02, segmentos=2,
                   desorden=0.006)
        x = xb

    # Muro del fondo del soportal, con su zócalo y lo que hay en él.
    huecos = [hueco_bajo(t, X + sx) for sx, t in casa.bajos.items()]
    MD.muro_x(m, X, X + W, FONDO, GROSOR_FONDO, 0.0, ALTO_SOPORTAL, cal, huecos)
    saltar = [(h[0] - 0.02, h[1] + 0.02) for h, t in zip(huecos, casa.bajos.values()) if h[2] < 0.6]
    MD.zocalo(m, X, X + W, FONDO, 0.62, "piedra_b", saltar=saltar)
    for sx, tipo in casa.bajos.items():
        cx = X + sx
        if tipo == "puerta":
            MD.puerta(m, cx, FONDO, mat="madera_z" if casa.tono != "blanco" else "postigo_almagra")
        elif tipo == "tienda":
            MD.tienda_cerrada(m, cx, FONDO)
        elif tipo == "tienda_velas":
            llama = MD.tienda_velas(m, cx, FONDO)
            luces.append(("punto", "VelaCereria", (llama[0], llama[1], llama[2] + 0.03), 2.2, CALIDA, 0.015))
            luces.append(("punto", "CandilCereria", (cx - 0.3, FONDO - 1.1, 1.45), 9.0, CALIDA, 0.06))
        elif tipo == "ventana_baja":
            MD.ventana_baja(m, cx, FONDO)
        elif tipo == "hornacina":
            MD.hornacina(m, cx - 0.275, FONDO, Z_HORNACINA, imagen=DIR_TEXTURAS / "pintura_hornacina.png")
            luces.append(("punto", "VelaHornacina", (cx, FONDO - 0.05, Z_HORNACINA + 0.27 + 0.035), 2.6, CALIDA, 0.012))

    # Interior de la casa tras el muro (para que los huecos no den al vacío).
    MD.estancia(m, X + 0.2, X + W - 0.2, FONDO - GROSOR_FONDO, FONDO - 3.0, 0.0, ALTO_SOPORTAL, "cal_interior")

    # Columnas, zapatas, viga y techo del soportal.
    siluetas = {}
    for i, c in enumerate(casa.columnas()):
        etiqueta = f"columna_{i}"
        MD.columna_toscana(m, X + c, 0.0, "piedra" if i % 2 == 0 else "piedra_b", etiqueta=etiqueta,
                           argolla=(casa.argolla == i))
        MD.zapata(m, X + c, 0.08, 3.35, largo=1.5, fondo=0.34)
        siluetas[etiqueta] = m.siluetas.pop(etiqueta)
    if casa.esquina:
        c = casa.columnas()[-1]
        MD.zapata(m, X + c, -0.45, 3.35, mat="madera_y", largo=1.0, eje="y")
        MD.viga(m, X + c - 0.14, X + c + 0.15, FONDO - GROSOR_FONDO, -0.14, 3.6, 3.86, "madera_y")
    juntas = [X + c for c in COLUMNAS] + ([X + casa.columnas()[-1]] if casa.esquina else [])
    MD.viga(m, X, X + W, -0.14, 0.27, ALTO_SOPORTAL, ALTO_VIGA, juntas=juntas)
    m.caja(X, FONDO - GROSOR_FONDO, ALTO_SOPORTAL + 0.02, X + W, -0.14, ALTO_VIGA, "madera_x")

    # Fachada alta, con recercados de cal, huecos, balcones y el interior de cada hueco.
    huecos_alt = [hueco_alto(t, X + sx) for sx, t in casa.altos.items()]
    if casa.desvan is not None:
        huecos_alt.append((X + casa.desvan - 0.24, X + casa.desvan + 0.24, casa.alero - 0.78, casa.alero - 0.38))
    MD.muro_x(m, X, X + W, FRENTE, GROSOR_FACHADA, ALTO_VIGA, casa.alero, cal, huecos_alt)
    for sx, tipo in casa.altos.items():
        cx = X + sx
        x0, x1, z0, z1 = hueco_alto(tipo, cx)
        luz = tipo.endswith("_luz")
        MD.recercado(m, x0, x1, z0, z1, FRENTE, 0.13, 0.012, "cal_blanco" if casa.tono != "blanco" else "cal_ocre",
                     alfeizar=not tipo.startswith("balcon"))
        if tipo.startswith("balcon"):
            MD.balcon_forja(m, cx, FRENTE, PUERTA_BALCON[0])
            MD.ventana_alta(m, cx, FRENTE, z0, z1, estado="abierta" if luz else "cerrada", alfeizar=False,
                            mat_hoja="postigo_verde" if casa.tono != "almagra" else "madera_z")
        else:
            MD.ventana_alta(m, cx, FRENTE, z0, z1, estado="abierta" if luz else "entornada",
                            mat_hoja="postigo_verde" if casa.tono != "almagra" else "madera_z")
        MD.estancia(m, max(X + 0.3, cx - 1.3), min(X + W - 0.3, cx + 1.3), FRENTE - GROSOR_FACHADA, -2.6,
                    SUELO_ALTO, casa.alero - 0.1, "cal_interior")
        if luz:
            luces.append(("area", f"Luz_{casa.id}_{sx}", (cx + 0.5, -1.6, z1 - 0.2), 26.0, CALIDA, (0.6, 0.6)))
            luces.append(("punto", f"Candil_{casa.id}_{sx}", (cx - 0.4, -1.2, z0 + 0.7), 6.0, CALIDA, 0.05))
    if casa.desvan is not None:
        cx = X + casa.desvan
        z0, z1 = casa.alero - 0.78, casa.alero - 0.38
        MD.recercado(m, cx - 0.24, cx + 0.24, z0, z1, FRENTE, 0.09, 0.01, "cal_blanco")
        m.caja(cx - 0.3, FRENTE - 0.15, z0 - 0.05, cx + 0.3, FRENTE + 0.05, z0, "piedra_b", 0.008, desorden=0.003)
        MD.hoja_tablas(m, cx - 0.24, cx + 0.24, z0, z1, FRENTE - 0.16, "madera_z", 0.03, 0.12, filas_clavos=(z0 + 0.1,))

    # Costados: medianera de aparejo toledano o, en la esquina, fachada lateral.
    # Los costados quedan un poco por detrás de la cara de la fachada: dos caras
    # coplanarias se harían sombra la una a la otra (franja negra en el render).
    yc = FRENTE - 0.05
    perfil_costado = [(FONDO_TEJADO, 0.0), (FONDO - GROSOR_FONDO - 0.02, 0.0),
                      (FONDO - GROSOR_FONDO - 0.02, ALTO_SOPORTAL), (yc, ALTO_SOPORTAL),
                      (yc, techo_en(casa, yc) - 0.04), (FONDO_TEJADO, casa.cumbrera - 0.04)]
    m.prisma(perfil_costado, "yz", X, X + 0.25, "tapial")
    if casa.esquina:
        construir_costado_esquina(m, casa)
    else:
        m.prisma(perfil_costado, "yz", X + W - 0.25, X + W, "tapial")

    # Alero y tejado.
    MD.alero_canecillos(m, X, X + W, FRENTE, casa.alero, VUELO_ALERO)
    remate = casa.esquina or (vecina_derecha is not None and vecina_derecha.alero < casa.alero)
    MD.tejado_arabe(m, X, X + W, FRENTE + VUELO_ALERO + 0.1, casa.alero + 0.035, FONDO_TEJADO, casa.cumbrera,
                    remate_derecho=remate)
    return m, siluetas, luces


def construir_costado_esquina(m, casa):
    """Fachada lateral de la casa de esquina: planta baja tras el soportal con ventana
    enrejada, planta alta con ventana, piñón hasta el tejado."""
    X, W = casa.x0, ANCHO_CASA
    xc = X + W
    cal = f"cal_{casa.tono}"
    yv = -3.3                                     # ventana baja del costado
    MD.muro_y(m, FONDO_TEJADO, FONDO - GROSOR_FONDO, xc, 0.3, 0.0, ALTO_VIGA, cal,
              [(yv - 0.55, yv + 0.55, 0.81, 2.11)])
    MD.zocalo(m, FONDO_TEJADO, FONDO - GROSOR_FONDO, xc, 0.62, "piedra_b", saltar=(), eje="y")
    with m.transformada(BL.giro_z(-90, (xc, yv, 0))):
        MD.ventana_baja(m, xc, yv)
    ya = -1.45
    MD.muro_y(m, FONDO_TEJADO, FRENTE - GROSOR_FACHADA, xc, 0.3, ALTO_VIGA, casa.alero, cal,
              [(ya - 0.5, ya + 0.5, VENTANA[0], VENTANA[1])])
    with m.transformada(BL.giro_z(-90, (xc, ya, 0))):
        MD.recercado(m, xc - 0.5, xc + 0.5, VENTANA[0], VENTANA[1], ya, 0.13, 0.012, "cal_ocre")
        MD.ventana_alta(m, xc, ya, VENTANA[0], VENTANA[1], estado="cerrada")
    pinon = [(FRENTE - 0.05, casa.alero), (FONDO_TEJADO, casa.alero), (FONDO_TEJADO, casa.cumbrera - 0.04),
             (FRENTE - 0.05, techo_en(casa, FRENTE - 0.05) - 0.04)]
    m.prisma(pinon, "yz", xc - 0.3, xc, cal)


def construir_carro():
    m = BL.Malla("carro", semilla=11)
    ox, oy = CARRO.origen_xy
    MD.carro(m, ox - 2.9, ox, oy - 0.9, oy)
    return m


def construir_barriles():
    m = BL.Malla("barriles", semilla=5)
    ox, oy = BARRILES.origen_xy
    for bx, by in [(-0.983, -0.533), (-0.233, -0.233)]:
        MD.barril(m, ox + bx, oy + by)
    return m


CANAL = (3.6, 4.0)       # canalillo central de la calle (y)


def construir_suelo(detalle=True):
    """Calle de canto rodado asentado en tierra, con maestras frente a las columnas y
    un canalillo de losas con charcos. Solo se modela lo que cae dentro del lienzo."""
    m = BL.Malla("suelo", semilla=2)
    # La tierra queda algo por debajo de las losas del soportal: el suelo recorta a las
    # casas (holdout) y, a la misma altura, se comería las losas.
    m.caja(-14, FONDO - 4, -0.3, 40, 26, -0.015, "tierra")

    def dentro(x, y, margen=60):
        sx, sy = pantalla(x, y, 0.0, SUELO_OX, SUELO_OY)
        return -margen < sx < SUELO_ANCHO + margen and -margen < sy < SUELO_ALTO_PX + margen
    cantos = None
    if detalle:
        maestras = [1.5 + 3 * k for k in range(-5, 13)]
        c, r, g = MD.empedrado(m.rng, -12, 36, 0.43, 23, dentro, saltar_y=[(CANAL[0] - 0.04, CANAL[1] + 0.04)],
                               maestras=maestras)
        # Bocacalle tras la casa de la esquina y calle que sigue antes de la primera casa.
        c2, r2, g2 = MD.empedrado(m.rng, 24.35, 36, -9, 0.43, dentro)
        c3, r3, g3 = MD.empedrado(m.rng, -14, -0.02, -9, 0.43, dentro)
        c, r, g = c + c2 + c3, r + r2 + r3, g + g2 + g3
        cantos = BL.nube("suelo_cantos", c, r, g, MAT.obtener("canto"), desorden=0.005)
        print(f"  {len(c)} cantos", flush=True)
    # Canalillo: dos hileras de losas que vierten al centro.
    for lado, (ya, yb) in ((1, (CANAL[0], (CANAL[0] + CANAL[1]) / 2 - 0.02)),
                           (-1, ((CANAL[0] + CANAL[1]) / 2 + 0.02, CANAL[1]))):
        x = -12 - m.azar(0, 0.5)
        while x < 36:
            xb = x + m.azar(0.35, 0.6)
            if dentro((x + xb) / 2, ya):
                m.caja(x + 0.008, ya, -0.1, xb - 0.008, yb, -0.012, "losa", bisel=0.01, desorden=0.004,
                       giro=BL.Matrix.Rotation(BL.math.radians(4 * lado), 4, "X"))
            x = xb
    extras = []
    if detalle:
        extras = barro_y_charcos(m)
    return [m.objeto(MAT.obtener, "suelo")] + ([cantos] if cantos else []) + extras


RODERAS = (5.93, 7.17)    # y de las rodadas de los carros (el del carro aparcado)


def barro_y_charcos(m, paso=0.07, semilla=7):
    """Barro que entierra las piedras a manchas (más junto al canalillo y en las
    roderas), charcos donde queda hondo, estiércol y paja. Devuelve los objetos."""
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(semilla)
    x0, x1, y0, y1 = -14.0, 36.0, -9.0, 23.0
    nx, ny = int((x1 - x0) / paso) + 1, int((y1 - y0) / paso) + 1
    X, Y = np.meshgrid(x0 + paso * np.arange(nx), y0 + paso * np.arange(ny))

    def ruido(sigma_m):
        r = gaussian_filter(rng.standard_normal((ny, nx)), sigma_m / paso)
        return (r - r.mean()) / r.std()
    grande, medio, fino = ruido(1.3), ruido(0.35), ruido(0.07)
    canal = np.exp(-((Y - (CANAL[0] + CANAL[1]) / 2) / 0.7) ** 2)
    roderas = sum(np.exp(-((Y - yr) / 0.24) ** 2) for yr in RODERAS)
    surco = sum(np.exp(-((Y - yr) / 0.07) ** 2) for yr in RODERAS)
    cantidad = 0.55 * grande + 0.35 * medio + 0.1 * fino + 0.9 * canal + 0.8 * roderas * (0.6 + 0.4 * (medio > -0.3))
    barro = np.clip((cantidad - 0.35) / 0.6, 0, 1)
    # Nada de barro bajo las casas ni pegado al bordillo (lo recortaría).
    casas = ((X > -0.4) & (X < 24.4) & (Y < 0.8)).astype(float)
    barro *= 1 - np.clip(gaussian_filter(casas, 0.15 / paso) * 2, 0, 1)
    z = -0.022 + 0.072 * barro ** 1.3 + 0.004 * fino - 0.02 * surco * barro
    # Charcos: donde el terreno queda hondo o el agua corre (canalillo, roderas).
    charco = 0.6 * ruido(0.5) + 0.4 * medio + 0.9 * canal + 0.7 * surco - 1.6 * gaussian_filter(casas, 0.3 / paso)
    agua = charco > 1.2
    nivel = 0.011
    hondo = gaussian_filter(agua.astype(float), 0.06 / paso) > 0.2
    z = np.where(hondo, np.minimum(z, nivel - 0.008), z)
    sx = (X - Y) * AX + SUELO_OX
    sy = (X + Y) * AY + SUELO_OY
    dentro = (sx > -60) & (sx < SUELO_ANCHO + 60) & (sy > -60) & (sy < SUELO_ALTO_PX + 60)
    con_barro = gaussian_filter((barro > 0.02).astype(float), 1.0) > 0.01
    objetos = [BL.campo_alturas("suelo_barro", x0, y0, paso, z, MAT.obtener("barro"), con_barro & dentro)]
    olas = nivel + 0.0015 * fino
    objetos.append(BL.campo_alturas("suelo_agua", x0, y0, paso, olas, MAT.obtener("agua"), agua & dentro))
    print(f"  barro en el {con_barro[dentro].mean():.0%} de la calle, charcos en el {agua[dentro].mean():.1%}",
          flush=True)
    # Boñigas y paja suelta por la calle (hacia 1620 las calles eran de caballerías).
    r = m.rng
    for _ in range(16):
        bx, by = r.uniform(-8, 30), r.uniform(1.4, 12)
        for _k in range(r.randint(3, 6)):
            m.esfera((bx + r.uniform(-0.12, 0.12), by + r.uniform(-0.1, 0.1), 0.02),
                     (r.uniform(0.035, 0.06), r.uniform(0.03, 0.05), r.uniform(0.018, 0.03)), "bonigas", 8, 5,
                     desorden=0.008)
    for _ in range(26):
        px, py = r.uniform(-8, 30), r.uniform(0.9, 14)
        for _k in range(r.randint(8, 18)):
            a = r.uniform(0, math.pi)
            l = r.uniform(0.08, 0.26)
            cx, cy = px + r.uniform(-0.3, 0.3), py + r.uniform(-0.25, 0.25)
            m.barra((cx - l / 2 * math.cos(a), cy - l / 2 * math.sin(a), 0.03),
                    (cx + l / 2 * math.cos(a), cy + l / 2 * math.sin(a), 0.03 + r.uniform(-0.01, 0.01)),
                    0.006, 0.004, "paja")
    return objetos


def pintura_hornacina():
    """Lienzo devoto de la hornacina, hecho con PIL. Solo tiene que leerse como mancha
    (un manto oscuro, la cara pálida y el resplandor); ChatGPT lo pintará de verdad."""
    DIR_TEXTURAS.mkdir(parents=True, exist_ok=True)
    w, h = 180, 260
    img = Image.new("RGB", (w, h), (24, 18, 15))
    d = ImageDraw.Draw(img)
    for r in range(70, 0, -2):                                    # resplandor
        c = int(40 + (70 - r) * 1.6)
        d.ellipse((w / 2 - r, 78 - r, w / 2 + r, 78 + r), fill=(c, int(c * 0.75), int(c * 0.35)))
    d.polygon([(w / 2, 70), (w * 0.12, h * 0.97), (w * 0.88, h * 0.97)], fill=(22, 26, 46))      # manto
    d.polygon([(w / 2, 92), (w * 0.3, h * 0.9), (w * 0.7, h * 0.9)], fill=(70, 22, 20))          # túnica
    d.ellipse((w / 2 - 15, 64, w / 2 + 15, 100), fill=(196, 160, 128))                          # rostro
    d.polygon([(w / 2 - 20, 70), (w / 2, 52), (w / 2 + 20, 70), (w / 2 + 24, 110), (w / 2 - 24, 110)],
              outline=(16, 18, 30), fill=None)
    d.ellipse((w / 2 - 9, 150, w / 2 + 9, 162), fill=(190, 150, 118))                           # manos
    ruido = np.random.default_rng(3).normal(0, 6, (h, w, 3))
    arr = np.clip(np.asarray(img, dtype=float) + ruido, 0, 255).astype(np.uint8)
    ruta = DIR_TEXTURAS / "pintura_hornacina.png"
    Image.fromarray(arr).save(ruta)
    return ruta


# ------------------------------------------------------------- luz

class Iluminacion:
    def __init__(self, luces):
        self.luna = BL.luna(LUNA, LUNA_FUERZA, LUNA_COLOR)
        self.mundo = BL.cielo(CIELO_COLOR, CIELO_FUERZA)
        self.calidas = []
        for spec in luces:
            if spec[0] == "punto":
                _, nombre, pos, pot, col, radio = spec
                self.calidas.append(BL.punto_luz(nombre, pos, pot, col, radio))
            else:
                _, nombre, pos, pot, col, tam = spec
                self.calidas.append(BL.area_luz(nombre, pos, pot, col, tam, mirando=(0, 1, -0.4)))
        BL.bpy.context.scene.view_settings.exposure = EXPOSICION

    def modo(self, cual):
        """'noche': la del juego. 'forma': luz de estudio para la maqueta de arcilla."""
        s = BL.bpy.context.scene
        fondo = self.mundo.node_tree.nodes["Background"]
        if cual == "forma":
            self.luna.data.energy = 2.2
            self.luna.data.color = (1, 1, 1)
            fondo.inputs["Color"].default_value = (0.5, 0.5, 0.52, 1)
            fondo.inputs["Strength"].default_value = 0.35
            BL.bpy.context.view_layer.material_override = MAT.obtener("arcilla")
            s.view_settings.exposure = 0.0
            for luz in self.calidas:
                luz.hide_render = True
        else:
            self.luna.data.energy = LUNA_FUERZA
            self.luna.data.color = LUNA_COLOR
            fondo.inputs["Color"].default_value = (*CIELO_COLOR, 1)
            fondo.inputs["Strength"].default_value = CIELO_FUERZA
            BL.bpy.context.view_layer.material_override = None
            s.view_settings.exposure = EXPOSICION
            for luz in self.calidas:
                luz.hide_render = False


# ------------------------------------------------------------- render de piezas

def caja_pantalla(objetos, origen, margen=6):
    pts = np.concatenate([BL.vertices(o) for o in objetos]) - np.array(origen)
    sx = (pts[:, 0] - pts[:, 1]) * AX
    sy = (pts[:, 0] + pts[:, 1]) * AY - pts[:, 2] * ZH
    x0, x1, y0, y1 = sx.min(), sx.max(), sy.min(), sy.max()
    ancho = int(math.ceil(x1 - x0)) + 2 * margen
    alto = int(math.ceil(y1 - y0)) + 2 * margen
    return ancho, alto, (-x0 + margen, -y0 + margen)


def lienzo_maqueta(ancho, alto):
    aspecto = ancho / alto
    if aspecto < 0.8:
        return 1024, 1536
    if aspecto > 1.25:
        return 1536, 1024
    return 1024, 1024


def recortes_columnas(siluetas, origen, ancla, tamano):
    """Polígono exacto de cada columna en la imagen de la pieza: unión de las
    envolventes de sus partes (plinto, cada tramo del torno, ábaco) y su contorno."""
    from scipy.spatial import ConvexHull
    from skimage import measure
    sobre = 4
    salida = []
    for etiqueta, partes in sorted(siluetas.items()):
        lienzo = Image.new("L", (tamano[0] * sobre, tamano[1] * sobre), 0)
        d = ImageDraw.Draw(lienzo)
        base_pt = None
        for p in partes:
            q = p - np.array(origen)
            sx = ((q[:, 0] - q[:, 1]) * AX + ancla[0]) * sobre
            sy = ((q[:, 0] + q[:, 1]) * AY - q[:, 2] * ZH + ancla[1]) * sobre
            xy = np.stack([sx, sy], 1)
            if len(xy) >= 3:
                h = ConvexHull(xy)
                d.polygon([tuple(xy[i]) for i in h.vertices], fill=255)
        mascara = np.asarray(lienzo) > 127
        contornos = measure.find_contours(mascara.astype(float), 0.5)
        contorno = max(contornos, key=len)
        poli = measure.approximate_polygon(contorno, tolerance=0.6 * sobre)
        poligono = [[round(c / sobre, 1), round(f / sobre, 1)] for f, c in poli[:-1]]
        cx = np.mean([p[:, 0].mean() for p in partes]) - origen[0]
        base_pt = pantalla(cx + 0.26, 0.26, 0.0)
        salida.append({"poligono": poligono, "base": round(base_pt[1] + ancla[1], 1)})
    return salida


def tiras(pieza, ancho, alto, ancla, ruta_imagen, paso=80):
    """Recortes de un objeto suelto: tiras verticales de la imagen, cada una con la
    línea base del punto más cercano a la cámara de la huella en esa franja."""
    huella = [(pantalla(x, y)[0] + ancla[0], pantalla(x, y)[1] + ancla[1]) for x, y in pieza.huella_local]
    alfa = np.asarray(Image.open(ruta_imagen).split()[3]) > 8
    n = max(1, round(ancho / paso))
    salida = []
    for i in range(n):
        u0, u1 = ancho * i / n, ancho * (i + 1) / n
        filas = np.where(alfa[:, int(u0):int(math.ceil(u1))].any(axis=1))[0]
        if len(filas) == 0:
            continue
        base = None
        for u in np.linspace(u0, u1, 24):
            for (ax, ay), (bx, by) in zip(huella, huella[1:] + huella[:1]):
                if min(ax, bx) <= u <= max(ax, bx) and ax != bx:
                    y = ay + (by - ay) * (u - ax) / (bx - ax)
                    base = y if base is None else max(base, y)
        if base is None:
            base = max(p[1] for p in huella)
        y0, y1 = max(0, filas[0] - 1), min(alto, filas[-1] + 2)
        salida.append({"poligono": [[round(u0, 1), float(y0)], [round(u1, 1), float(y0)], [round(u1, 1), float(y1)],
                                    [round(u0, 1), float(y1)]], "base": round(float(base), 1)})
    return salida


def sobre_magenta(ruta_rgba, destino):
    img = Image.open(ruta_rgba).convert("RGBA")
    lienzo = Image.new("RGBA", img.size, (255, 0, 255, 255))
    lienzo.alpha_composite(img)
    lienzo.convert("RGB").save(destino, optimize=True)
    return img


def renderizar_pieza(pieza, objetos, siluetas, ilum, muestras, temporal, recortan=(), renderizar=True):
    """Renderiza la pieza (juego, estudio de luz y maqueta de forma) y escribe su
    ficha. Con renderizar=False solo rehace la ficha a partir de las imágenes que ya hay."""
    t0 = time.time()
    origen = pieza.origen()
    BL.solo_visibles(objetos, recortan)
    ancho, alto, ancla = caja_pantalla(objetos, origen)
    cw, ch = lienzo_maqueta(ancho, alto)
    s = min(0.88 * cw / ancho, 0.88 * ch / alto)
    ancla_m = ((cw - ancho * s) / 2 + ancla[0] * s, (ch - alto * s) / 2 + ancla[1] * s)

    if renderizar:
        # Pieza para el juego. El render queda siempre en la carpeta de fichas; al juego
        # solo pasa si la pieza no está ya repintada (si lo está, hay que volver a
        # pasar procesar_pieza.py con la pintura guardada en arte/entrada/piezas/).
        ilum.modo("noche")
        BL.encuadrar(ancho, alto, ancla, 1.0, origen)
        render = DIR_FICHAS / f"{pieza.id}_render.png"
        BL.renderizar(render, muestras)
        pintada = RAIZ / "arte/entrada/piezas" / f"{pieza.id}_pintada.png"
        if pintada.exists():
            print(f"  {pieza.id} está repintada: python3 herramientas/procesar_pieza.py {pieza.id} "
                  f"{pintada.relative_to(RAIZ)}", flush=True)
        else:
            shutil.copy(render, DIR_PIEZAS / f"{pieza.id}.png")
        # Estudio de luz y maqueta de forma a tamaño de ChatGPT.
        BL.encuadrar(cw, ch, ancla_m, s, origen)
        BL.renderizar(temporal / f"{pieza.id}_luz.png", max(32, int(muestras * 0.75)))
        sobre_magenta(temporal / f"{pieza.id}_luz.png", DIR_MAQUETAS / f"{pieza.id}_luz.png")
        ilum.modo("forma")
        BL.renderizar(temporal / f"{pieza.id}_forma.png", max(24, muestras // 3))
        forma = sobre_magenta(temporal / f"{pieza.id}_forma.png", DIR_MAQUETAS / f"{pieza.id}_maqueta.png")
        forma.split()[3].save(DIR_FICHAS / f"{pieza.id}_mascara.png", optimize=True)
        ilum.modo("noche")

    ficha = {
        "id": pieza.id,
        "nombre": pieza.nombre,
        "imagen": f"res://arte/piezas/{pieza.id}.png",
        "tamano": [ancho, alto],
        "ancla": [round(ancla[0], 1), round(ancla[1], 1)],
        "fondo": pieza.fondo,
        "huella": [[list(q) for q in h] for h in pieza.huella()],
        "recortes": (recortes_columnas(siluetas, origen, ancla, (ancho, alto)) if pieza.fondo
                     else tiras(pieza, ancho, alto, ancla, DIR_PIEZAS / f"{pieza.id}.png")),
        "maqueta": {"archivo": f"docs/arte/piezas/{pieza.id}_maqueta.png",
                    "luz": f"docs/arte/piezas/{pieza.id}_luz.png", "tamano": [cw, ch],
                    "escala": round(s, 5), "ancla": [round(ancla_m[0], 2), round(ancla_m[1], 2)]},
    }
    sombra = ficha_sombra(pieza, objetos)
    if sombra:
        ficha["sombra"] = sombra
    (DIR_FICHAS / f"{pieza.id}.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {pieza.id}: {ancho}×{alto} px en el juego; maqueta {cw}×{ch} a ×{s:.2f}; {time.time() - t0:.0f} s",
          flush=True)
    return ficha


SOMBRA_MARGEN = 24         # px alrededor de la sombra (penumbra y lo que tapa del cielo)
SOMBRA_CURVA = 0.6         # de oscurecimiento lineal a oscurecimiento en pantalla


def caja_sombra(objetos, origen):
    """Caja en pantalla (ancho, alto, ancla) de la sombra que la pieza echa en el suelo:
    la de sus vértices llevados a z = 0 en la dirección de la luna, más su base."""
    pts = np.concatenate([BL.vertices(o) for o in objetos])
    luz = np.array(LUNA) / np.linalg.norm(LUNA)
    z = np.clip(pts[:, 2], 0, None)
    proyectados = pts - (z / luz[2])[:, None] * luz
    q = np.concatenate([proyectados, pts]) * np.array([1, 1, 0]) - np.array(origen) * np.array([1, 1, 0])
    sx = (q[:, 0] - q[:, 1]) * AX
    sy = (q[:, 0] + q[:, 1]) * AY
    m = SOMBRA_MARGEN
    ancho = int(math.ceil(sx.max() - sx.min())) + 2 * m
    alto = int(math.ceil(sy.max() - sy.min())) + 2 * m
    return ancho, alto, (-sx.min() + m, -sy.min() + m)


class AtrapaSombras:
    """Plano en z = 0 que solo recoge sombras (shadow catcher de Cycles). Con él, cada
    pieza deja su sombra en una imagen aparte y el juego la pone sobre el suelo, sea
    cual sea su pintura: así el suelo no tiene que traer pintadas las sombras."""

    def __init__(self):
        m = BL.Malla("atrapa_sombras", semilla=1)
        m.caja(-30, -30, -0.02, 60, 40, 0.0, "tierra")
        self.plano = m.objeto(MAT.obtener, "atrapa_sombras")
        self.plano.is_shadow_catcher = True
        self.plano.hide_render = True

    def renderizar(self, pieza, objetos, ilum, muestras, temporal):
        """Sombra de la pieza en arte/piezas/<id>_sombra.png: negro con la opacidad que
        oscurece el suelo. Solo cuentan la luna y el cielo (las velas no)."""
        escena = BL.bpy.context.scene
        propios = {o.name for o in objetos}
        antes = {o.name: o.hide_render for o in escena.objects}
        for o in escena.objects:
            if o.type == "MESH":
                o.hide_render = not (o.name in propios or o == self.plano)
                o.visible_camera = o == self.plano
                o.is_holdout = False
        for luz in ilum.calidas:
            luz.hide_render = True
        ancho, alto, ancla = caja_sombra(objetos, pieza.origen())
        BL.encuadrar(ancho, alto, ancla, 1.0, pieza.origen())
        tmp = temporal / f"{pieza.id}_sombra.png"
        BL.renderizar(tmp, muestras)
        for o in escena.objects:
            o.hide_render = antes.get(o.name, o.hide_render)
        for luz in ilum.calidas:
            luz.hide_render = False
        # El atrapasombras da cuánto baja la luz (lineal). La pintura del suelo está en
        # valores de pantalla, donde la misma sombra oscurece menos. El exponente sale
        # de medir el render del suelo con sus sombras: con AgX y esta exposición, la
        # razón en pantalla es la lineal elevada a 0,6 (bajo el carro, 0,13 → 0,28).
        a = np.asarray(Image.open(tmp).convert("RGBA")).astype(np.float32)[..., 3] / 255.0
        a = 1 - (1 - a) ** SOMBRA_CURVA
        salida = np.zeros(a.shape + (4,), np.uint8)
        salida[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
        Image.fromarray(salida, "RGBA").save(DIR_PIEZAS / f"{pieza.id}_sombra.png", optimize=True)
        print(f"  sombra de {pieza.id}: {ancho}×{alto} px, opacidad máxima {a.max():.2f}", flush=True)


def sombra_sin_lo_tapado(ident):
    """Las casas tapan su propia sombra (la de bajo el soportal, casi negra), pero su
    pie sale dentado en el render y por las muescas asomaba ese negro. Se borra la
    sombra donde está la casa (su silueta cerrada y ensanchada unos px). Solo para las
    casas: en los objetos sueltos, entre los radios de una rueda o bajo un barril, la
    sombra sí se ve. Usa la ficha (anclas de la pieza y de la sombra) y el render."""
    from scipy.ndimage import binary_closing, binary_dilation
    ficha = json.loads((DIR_FICHAS / f"{ident}.json").read_text(encoding="utf-8"))
    ruta_sombra = DIR_PIEZAS / f"{ident}_sombra.png"
    ruta_render = DIR_FICHAS / f"{ident}_render.png"
    if not (ficha["fondo"] and ficha.get("sombra") and ruta_sombra.exists() and ruta_render.exists()):
        return
    sombra = np.asarray(Image.open(ruta_sombra).convert("RGBA")).copy()
    silueta = np.asarray(Image.open(ruta_render).convert("RGBA"))[..., 3] > 8
    silueta = binary_dilation(binary_closing(silueta, np.ones((9, 9), bool)), iterations=2)
    # Un mismo punto del suelo está en (u, v) en la pieza y en (u, v) + (dx, dy) en la sombra.
    dx = round(ficha["sombra"]["ancla"][0] - ficha["ancla"][0])
    dy = round(ficha["sombra"]["ancla"][1] - ficha["ancla"][1])
    h, w = silueta.shape
    hs, ws = sombra.shape[:2]
    tapa = np.zeros((hs, ws), bool)
    x0, y0 = max(0, dx), max(0, dy)
    x1, y1 = min(ws, dx + w), min(hs, dy + h)
    tapa[y0:y1, x0:x1] = silueta[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    sombra[..., 3] = np.where(tapa, 0, sombra[..., 3])
    Image.fromarray(sombra, "RGBA").save(ruta_sombra, optimize=True)
    print(f"  sombra de {ident}: quitada bajo la casa", flush=True)


def ficha_sombra(pieza, objetos):
    """Datos de la sombra para la ficha, si está renderizada."""
    if not (DIR_PIEZAS / f"{pieza.id}_sombra.png").exists():
        return None
    _, _, ancla = caja_sombra(objetos, pieza.origen())
    return {"imagen": f"res://arte/piezas/{pieza.id}_sombra.png", "ancla": [round(ancla[0], 1), round(ancla[1], 1)]}


TESELA = (1536, 1024)      # tamaño de cada trozo del suelo para ChatGPT
TESELA_ESCALA = 0.9        # cada trozo cubre 1707 × 1138 px del juego: 2 × 2 trozos con solape
DIR_SUELO = RAIZ / "docs/arte/suelo"


def teselas_suelo():
    """Trozos del suelo (id, x, y, ancho, alto) en píxeles del lienzo del juego."""
    w, h = TESELA[0] / TESELA_ESCALA, TESELA[1] / TESELA_ESCALA
    salida = []
    for j, y in enumerate((0.0, SUELO_ALTO_PX - h)):
        for i, x in enumerate((0.0, SUELO_ANCHO - w)):
            salida.append((f"suelo_{2 * j + i + 1}", round(x, 2), round(y, 2), round(w, 2), round(h, 2)))
    return salida


def renderizar_suelo(objetos, muestras, casas=(), temporal=None):
    """Suelo entero para el juego y, además, los cuatro trozos para ChatGPT (con las
    casas en magenta: lo que tapan no hace falta pintarlo). Si el suelo ya está
    repintado, el render solo se guarda aparte y no se toca el del juego."""
    DIR_SUELO.mkdir(parents=True, exist_ok=True)
    BL.solo_visibles(objetos)
    BL.encuadrar(SUELO_ANCHO, SUELO_ALTO_PX, (SUELO_OX, SUELO_OY), 1.0, (0.0, 0.0, 0.0))
    render = RAIZ / "herramientas/datos/suelo_render.png"
    BL.renderizar(render, muestras)
    Image.open(render).convert("RGB").save(render, optimize=True)
    pintado = sorted((RAIZ / "arte/entrada/suelo").glob("*_pintada.png"))
    if pintado:
        print("  el suelo está repintado: python3 herramientas/procesar_suelo.py", flush=True)
    else:
        shutil.copy(render, RAIZ / "arte/fondos/calle_mayor_suelo.png")

    BL.solo_visibles(objetos, casas)
    ficha = {"lienzo": [SUELO_ANCHO, SUELO_ALTO_PX], "escala": TESELA_ESCALA, "teselas": []}
    for ident, x, y, w, h in teselas_suelo():
        BL.encuadrar(TESELA[0], TESELA[1], ((SUELO_OX - x) * TESELA_ESCALA, (SUELO_OY - y) * TESELA_ESCALA),
                     TESELA_ESCALA, (0.0, 0.0, 0.0))
        tmp = (temporal or DIR_SUELO) / f"{ident}_tmp.png"
        BL.renderizar(tmp, max(32, int(muestras * 0.75)))
        img = sobre_magenta(tmp, DIR_SUELO / f"{ident}_luz.png")
        img.split()[3].save(DIR_FICHAS.parent / f"{ident}_mascara.png", optimize=True)
        tmp.unlink(missing_ok=True)
        ficha["teselas"].append({"id": ident, "rect": [x, y, w, h], "luz": f"docs/arte/suelo/{ident}_luz.png"})
        print(f"  {ident}: {w:.0f} × {h:.0f} px del suelo desde ({x:.0f}, {y:.0f})", flush=True)
    (RAIZ / "herramientas/datos/suelo.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")


# ------------------------------------------------------------- escena

def generar_escena(fichas: dict):
    def S(x, y, z=0.0):
        return [round(v, 1) for v in pantalla(x, y, z, SUELO_OX, SUELO_OY)]

    piezas = []
    for casa in CASAS:
        piezas.append({"id": casa.id, "nodo": casa.id.replace("_", " ").title().replace(" ", ""),
                       "posicion": S(casa.x0, 0)})
    piezas.append({"id": "carro", "nodo": "Carro", "posicion": S(*CARRO.origen_xy)})
    piezas.append({"id": "barriles", "nodo": "Barriles", "posicion": S(*BARRILES.origen_xy)})
    piezas.append({"id": "cadaver", "nodo": "Cadaver", "posicion": S(11.1, 1.25)})

    hx = 12.0 + HUECOS[0]       # hornacina, en la casa 3
    datos = {
        "suelo": "res://arte/fondos/calle_mayor_suelo.png",
        "piezas": piezas,
        "fichas": fichas,
        "transitable": [S(0.5, -1.65), S(23.5, -1.65), S(23.5, 0.55), S(26.4, 0.55), S(26.4, 7.5), S(0.5, 7.5)],
        "obstaculos": [[S(12.2, 2.15), S(12.85, 2.15), S(12.85, 2.85), S(12.2, 2.85)]],   # donde está el alguacil
        "inicio": S(3.5, 4.2),
        "alguacil": S(12.5, 2.5),
        "tono_personajes": TONO_PERSONAJES,
        # Puntos para la prueba de humo: detrás de una columna de la casa 3 y detrás del carro.
        "pruebas": {"TrasColumna": S(12.6, -0.9), "TrasCarro": S(7.5, 5.6)},
        "luces": [{"nombre": "VelaHornacina", "posicion": S(hx, FONDO - 0.05, Z_HORNACINA + 0.3)}],
        "puntos": {
            "alguacil": {"zona": [S(12.15, 2.15, 0), S(12.95, 2.15, 0), S(12.95, 2.95, 0), S(12.95, 2.95, 1.95),
                                  S(12.15, 2.15, 1.95)], "llegada": S(12.3, 3.9)},
            "cadaver": {"zona": [S(10.2, 0.7), S(12.05, 0.7), S(12.05, 1.8), S(10.2, 1.8)], "llegada": S(10.9, 2.55)},
            "hornacina": {"zona": [S(hx - 0.42, FONDO, Z_HORNACINA - 0.15), S(hx + 0.42, FONDO, Z_HORNACINA - 0.15),
                                   S(hx + 0.42, FONDO, Z_HORNACINA + 0.75), S(hx - 0.42, FONDO, Z_HORNACINA + 0.75)],
                          "llegada": S(hx, -1.3)},
            "salida": {"zona": [S(24.6, 1.0), S(26.6, 1.0), S(26.6, 6.5), S(24.6, 6.5)], "llegada": S(25.4, 3.6)},
        },
    }
    (RAIZ / "herramientas/datos/calle_mayor.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")


def ficha_cadaver() -> dict:
    """El cadáver es un dibujo provisional de arte_provisional.py; aquí se le hace su ficha y su maqueta."""
    img = Image.open(RAIZ / "arte/objetos/cadaver.png").convert("RGBA")
    ancla = (img.width / 2, img.height / 2 + 8)           # centro del cuerpo en el suelo
    cw, ch = 1536, 1024
    s = min(0.8 * cw / img.width, 0.8 * ch / img.height)
    grande = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    lienzo = Image.new("RGBA", (cw, ch), (255, 0, 255, 255))
    pos = ((cw - grande.width) // 2, (ch - grande.height) // 2)
    lienzo.alpha_composite(grande, pos)
    lienzo.convert("RGB").save(DIR_MAQUETAS / "cadaver_maqueta.png", optimize=True)
    mascara = Image.new("L", (cw, ch), 0)
    mascara.paste(grande.split()[3], pos)
    mascara.save(DIR_FICHAS / "cadaver_mascara.png", optimize=True)
    ficha = {
        "id": "cadaver", "nombre": "El muerto", "imagen": "res://arte/objetos/cadaver.png",
        "tamano": [img.width, img.height], "ancla": [ancla[0], ancla[1]], "fondo": True,
        "huella": [[[-0.85, -0.5], [0.9, -0.5], [0.9, 0.5], [-0.85, 0.5]]], "recortes": [],
        "maqueta": {"archivo": "docs/arte/piezas/cadaver_maqueta.png", "tamano": [cw, ch], "escala": round(s, 5),
                    "ancla": [round(pos[0] + ancla[0] * s, 2), round(pos[1] + ancla[1] * s, 2)]},
    }
    (DIR_FICHAS / "cadaver.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=1), encoding="utf-8")
    return ficha


# ------------------------------------------------------------- principal

def construir_calle(suelo_detallado=True):
    """Construye toda la calle. Devuelve {id: (pieza, objetos, siluetas)} y las luces."""
    pintura_hornacina()
    todo, luces = {}, []
    for i, casa in enumerate(CASAS):
        vecina = CASAS[i + 1] if i + 1 < len(CASAS) else None
        m, siluetas, l = construir_casa(casa, vecina)
        todo[casa.id] = (casa, [m.objeto(MAT.obtener, casa.id)], siluetas)
        luces += l
    todo["carro"] = (CARRO, [construir_carro().objeto(MAT.obtener, "carro")], {})
    todo["barriles"] = (BARRILES, [construir_barriles().objeto(MAT.obtener, "barriles")], {})
    t = time.time()
    todo["suelo"] = (None, construir_suelo(suelo_detallado), {})
    print(f"  suelo: {time.time() - t:.0f} s", flush=True)
    return todo, luces


def recortes_de(todo, clave):
    """Objetos que recortan a una pieza: las demás casas y el suelo (y, para los
    objetos sueltos, también los otros objetos). Las casas no se recortan con los
    objetos de la calle: estos se dibujan siempre encima, y por sus huecos (entre
    los radios de una rueda) tiene que verse la casa."""
    es_casa = clave.startswith("casa_")
    salida = []
    for otra, (pieza, objetos, _) in todo.items():
        if otra == clave:
            continue
        if otra == "suelo" or otra.startswith("casa_") or not es_casa:
            salida += objetos
    return salida


def main():
    args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args.add_argument("--solo", nargs="*", help="renderizar solo estas piezas («suelo» para el suelo)")
    args.add_argument("--sin-suelo", action="store_true", help="no rehacer el suelo")
    args.add_argument("--muestras", type=int, default=160, help="muestras por píxel de la pieza del juego")
    args.add_argument("--rapido", action="store_true", help="prueba rápida: pocas muestras")
    args.add_argument("--blend", help="guardar también la escena de Blender en este archivo")
    args.add_argument("--sin-render", action="store_true",
                      help="no renderizar: rehacer solo fichas y escena con las imágenes que ya hay")
    args.add_argument("--sombras", action="store_true",
                      help="renderizar solo las sombras de las piezas (y rehacer fichas y escena)")
    a = args.parse_args()
    for d in (DIR_MAQUETAS, DIR_PIEZAS, DIR_FICHAS):
        d.mkdir(parents=True, exist_ok=True)
    muestras = 24 if a.rapido else a.muestras
    temporal = RAIZ / "pruebas/salida/render"
    temporal.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    BL.reiniciar()
    MAT.vaciar()
    con_suelo = not (a.sin_suelo or a.sin_render or a.sombras) and (not a.solo or "suelo" in a.solo)
    todo, luces = construir_calle(suelo_detallado=con_suelo)
    ilum = Iluminacion(luces)
    atrapa = AtrapaSombras()
    print(f"Calle construida en {time.time() - t0:.0f} s", flush=True)
    if a.blend:
        BL.bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.blend).resolve()))

    print("Piezas:")
    for clave, (pieza, objetos, siluetas) in todo.items():
        if pieza is None or (a.solo and clave not in a.solo):
            continue
        if not a.sin_render:
            atrapa.renderizar(pieza, objetos, ilum, 64 if a.rapido else 192, temporal)
        renderizar_pieza(pieza, objetos, siluetas, ilum, muestras, temporal, recortes_de(todo, clave),
                         renderizar=not (a.sin_render or a.sombras))
        if not a.sin_render:
            sombra_sin_lo_tapado(pieza.id)
    if con_suelo:
        print("Suelo de la calle…", flush=True)
        casas = [o for clave, (_, objs, _) in todo.items() if clave.startswith("casa_") for o in objs]
        renderizar_suelo(todo["suelo"][1], muestras, casas, temporal)
    ficha_cadaver()
    fichas = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(DIR_FICHAS.glob("*.json"))}
    generar_escena(fichas)
    print(f"Hecho en {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
