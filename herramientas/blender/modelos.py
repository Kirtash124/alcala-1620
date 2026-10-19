"""Modelos detallados de arquitectura y objetos de Alcalá hacia 1620.

Cada función añade geometría a una Malla (base.py) en nuestras coordenadas (metros,
x a lo largo de la calle, y hacia la calle, z arriba). Los nombres de material son
los de materiales.FABRICAS.

Referencias de época que fijan las decisiones (ver docs/arte/piezas/README.md):
columna de piedra con zapata de madera en los soportales de la calle Mayor;
puertas de tablas claveteadas con pernios y aldaba de hierro; ventanas sin vidriera,
con hojas y postigos de madera; rejas de cuadradillo con pletinas; balcones de
hierro con balaustres y macollas; teja árabe; aleros de canecillos de madera;
medianeras de aparejo toledano (tapial entre verdugadas de ladrillo).
"""
import math

from mathutils import Matrix, Vector

from base import B, giro_x, giro_y, giro_z


def _suma(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _por(a, k):
    return tuple(x * k for x in a)


def _intervalos_libres(a, b, ocupados):
    libres, actual = [], a
    for o0, o1 in sorted(ocupados):
        if o1 <= actual or o0 >= b:
            continue
        if o0 > actual:
            libres.append((actual, o0))
        actual = max(actual, o1)
    if actual < b:
        libres.append((actual, b))
    return libres


# ------------------------------------------------------------------ muros

def placa(m, origen, u, v, ancho, alto, grosor, normal, mat, huecos=()):
    """Paño de muro plano con huecos rectangulares. `origen` es la esquina inferior
    de la cara vista; u y v, vectores unitarios a lo ancho y a lo alto; el grosor
    crece hacia -normal. huecos: (s0, s1, t0, t1) en metros sobre el paño."""
    ss = sorted({0.0, ancho, *[max(0.0, min(ancho, h[i])) for h in huecos for i in (0, 1)]})
    ts = sorted({0.0, alto, *[max(0.0, min(alto, h[i])) for h in huecos for i in (2, 3)]})

    def P(s, t, d=0.0):
        return _suma(_suma(origen, _por(u, s)), _suma(_por(v, t), _por(normal, -d)))

    def en_hueco(s, t):
        return any(h[0] < s < h[1] and h[2] < t < h[3] for h in huecos)

    frente = {(i, j): m._v(P(s, t)) for i, s in enumerate(ss) for j, t in enumerate(ts)}
    caras = []
    for i in range(len(ss) - 1):
        for j in range(len(ts) - 1):
            if en_hueco((ss[i] + ss[i + 1]) / 2, (ts[j] + ts[j + 1]) / 2):
                continue
            caras.append(m.bm.faces.new([frente[i, j], frente[i + 1, j], frente[i + 1, j + 1], frente[i, j + 1]]))
    usados = {v for f in caras for v in f.verts}
    for clave in [k for k, vt in frente.items() if vt not in usados]:
        m.bm.verts.remove(frente.pop(clave))
    bordes = [e for f in caras for e in f.edges if len(e.link_faces) == 1]
    bordes = list(dict.fromkeys(bordes))
    detras = {}
    for (i, j), vt in frente.items():
        detras[vt] = m._v(P(ss[i], ts[j], grosor))
    nuevas = [m.bm.faces.new([detras[vt] for vt in reversed(f.verts)]) for f in caras]
    for e in bordes:
        a, b = e.verts
        nuevas.append(m.bm.faces.new([a, b, detras[b], detras[a]]))
    todas = caras + nuevas
    import bmesh
    bmesh.ops.recalc_face_normals(m.bm, faces=todas)
    m._asignar(todas, mat)


def muro_x(m, x0, x1, y_cara, grosor, z0, z1, mat, huecos=()):
    """Muro a lo largo de x con la cara vista hacia +y. huecos: (xa, xb, za, zb)."""
    placa(m, (x0, y_cara, z0), (1, 0, 0), (0, 0, 1), x1 - x0, z1 - z0, grosor, (0, 1, 0), mat,
          [(h[0] - x0, h[1] - x0, h[2] - z0, h[3] - z0) for h in huecos])


def muro_y(m, y0, y1, x_cara, grosor, z0, z1, mat, huecos=()):
    """Muro a lo largo de y con la cara vista hacia +x. huecos: (ya, yb, za, zb)."""
    placa(m, (x_cara, y0, z0), (0, 1, 0), (0, 0, 1), y1 - y0, z1 - z0, grosor, (1, 0, 0), mat,
          [(h[0] - y0, h[1] - y0, h[2] - z0, h[3] - z0) for h in huecos])


def muro_perfil_y(m, perfil_yz, x0, x1, mat):
    """Muro lateral (cara hacia ±x) con un contorno cualquiera en el plano y-z."""
    m.prisma(perfil_yz, "yz", x0, x1, mat)


def recercado(m, x0, x1, z0, z1, y_cara, ancho=0.12, saliente=0.012, mat="cal_blanco", alfeizar=True):
    """Recercado de cal alrededor de un hueco: banda algo más clara y en resalte."""
    a, s = ancho, saliente
    m.caja(x0 - a, y_cara - 0.01, z1, x1 + a, y_cara + s, z1 + a, mat, 0.004)
    m.caja(x0 - a, y_cara - 0.01, z0 - (a if alfeizar else 0), x0, y_cara + s, z1, mat, 0.004)
    m.caja(x1, y_cara - 0.01, z0 - (a if alfeizar else 0), x1 + a, y_cara + s, z1, mat, 0.004)
    if alfeizar:
        m.caja(x0, y_cara - 0.01, z0 - a, x1, y_cara + s, z0, mat, 0.004)


def zocalo(m, s0, s1, cara, z1, mat, saltar=(), eje="x", alturas=(0.22, 0.2, 0.18)):
    """Zócalo de mampostería concertada: hiladas de sillarejo en resalte.
    eje 'x': muro a lo largo de x con la cara en y=cara; 'y': a lo largo de y, cara en x=cara."""
    def caja(sa, sb, d0, d1, za, zb, **kw):
        if eje == "x":
            m.caja(sa, cara + d0, za, sb, cara + d1, zb, mat, **kw)
        else:
            m.caja(cara + d0, sa, za, cara + d1, sb, zb, mat, **kw)
    z = 0.0
    hiladas = [h * z1 / sum(alturas) for h in alturas]
    for k, h in enumerate(hiladas):
        h = h + m.azar(-0.015, 0.015) if k < len(hiladas) - 1 else z1 - z
        for a, b in _intervalos_libres(s0, s1, saltar):
            s = a + (m.azar(0.0, 0.25) if k % 2 else 0.0)
            if s > a:
                caja(a + 0.006, s - 0.006, -0.03, m.azar(0.015, 0.04), z + 0.006, z + h - 0.006,
                     bisel=0.018, segmentos=2, desorden=0.006)
            while s < b - 0.05:
                largo = m.azar(0.28, 0.62)
                e = min(b, s + largo)
                if b - e < 0.15:
                    e = b
                caja(s + 0.007, e - 0.007, -0.03, m.azar(0.018, 0.05), z + 0.007, z + h - 0.007,
                     bisel=0.02, segmentos=2, desorden=0.008)
                s = e
        z += h


def losas(m, x0, x1, y0, y1, mat="losa", fila=(0.42, 0.68), largo=(0.45, 0.9)):
    """Enlosado de piedra en hileras paralelas a la calle, con juntas y cejas."""
    y = y1
    while y > y0 + 0.05:
        alto_fila = m.azar(*fila)
        ya = max(y0, y - alto_fila)
        if ya - y0 < 0.2:
            ya = y0
        x = x0 - m.azar(0.0, 0.4)
        while x < x1:
            xb = x + m.azar(*largo)
            a, b = max(x, x0), min(xb, x1)
            if b - a > 0.06:
                cima = m.azar(-0.008, 0.004)
                m.caja(a + 0.007, ya + 0.007, -0.12, b - 0.007, y - 0.007, cima, mat, bisel=0.012,
                       segmentos=2, desorden=0.004)
            x = xb
        y = ya


def estancia(m, x0, x1, y_frente, y_fondo, z0, z1, mat):
    """Interior de una habitación vista por un hueco: suelo, techo y tres paredes."""
    g = 0.03
    m.caja(x0, y_fondo - g, z0, x1, y_fondo, z1, mat)
    m.caja(x0 - g, y_fondo, z0, x0, y_frente, z1, mat)
    m.caja(x1, y_fondo, z0, x1 + g, y_frente, z1, mat)
    m.caja(x0, y_fondo, z0 - g, x1, y_frente, z0, "madera_x")
    m.caja(x0, y_fondo, z1, x1, y_frente, z1 + g, mat)


# ------------------------------------------------------------------ soportal

def columna_toscana(m, cx, cy, mat="piedra", etiqueta=None, argolla=False):
    """Columna de piedra: plinto, basa de toro, fuste con éntasis, collarino,
    equino y ábaco. Altura total 3,35 m; encima va la zapata."""
    m.caja(cx - 0.28, cy - 0.28, 0.0, cx + 0.28, cy + 0.28, 0.13, mat, bisel=0.014, segmentos=2,
           desorden=0.005, etiqueta=etiqueta)
    perfil = [(0.245, 0.13), (0.252, 0.145), (0.258, 0.17), (0.255, 0.195), (0.245, 0.215),
              (0.228, 0.232), (0.21, 0.24), (0.2, 0.255), (0.192, 0.27)]
    for h in (0.45, 0.8, 1.2, 1.6, 2.0, 2.4, 2.75, 2.98):
        t = max(0.0, (h - 1.2) / 1.8)
        perfil.append((0.192 - 0.026 * t ** 1.4, h))
    perfil += [(0.168, 3.0), (0.18, 3.008), (0.186, 3.025), (0.18, 3.042), (0.166, 3.05), (0.162, 3.06),
               (0.162, 3.12), (0.172, 3.13), (0.192, 3.15), (0.214, 3.185), (0.232, 3.215), (0.24, 3.24)]
    m.torno(perfil, (cx, cy, 0.0), mat, lados=36, etiqueta=etiqueta, ruido=0.012)
    m.caja(cx - 0.255, cy - 0.255, 3.24, cx + 0.255, cy + 0.255, 3.35, mat, bisel=0.012, segmentos=2,
           desorden=0.004, etiqueta=etiqueta)
    if argolla:
        # Argolla de hierro para atar caballerías, mirando a la calle.
        yy = cy + 0.19
        m.caja(cx - 0.012, yy - 0.01, 1.18, cx + 0.012, yy + 0.03, 1.22, "hierro", 0.004)
        pts = [(cx + 0.045 * math.sin(a), yy + 0.035, 1.135 + 0.045 * math.cos(a))
               for a in [i * 2 * math.pi / 20 for i in range(20)]]
        m.tubo(pts, 0.007, "hierro", lados=6, cerrado=True)


def zapata(m, cx, cy, z0, mat="madera_x", largo=1.3, alto=0.25, fondo=0.32, eje="x"):
    """Zapata de madera de perfil lobulado sobre la columna."""
    mitad = largo / 2
    lado = []
    n = 26
    for i in range(n + 1):
        t = i / n                                       # 0 en el extremo, 1 junto al apoyo
        u = mitad - t * (mitad - 0.27)
        base = alto * 0.6 * (1 - (3 * t * t - 2 * t * t * t))
        lobulo = 0.024 * abs(math.sin(3 * math.pi * t)) * (1 - t * 0.4)
        lado.append((u, max(0.0, base - lobulo)))
    perfil = [(-mitad, alto), (mitad, alto)] + lado + [(-u, z) for u, z in reversed(lado)]
    # Se eliminan puntos repetidos (el lóbulo toca cero en el apoyo).
    limpio = []
    for p in perfil:
        if not limpio or abs(p[0] - limpio[-1][0]) > 1e-4 or abs(p[1] - limpio[-1][1]) > 1e-4:
            limpio.append(p)
    if eje == "x":
        m.prisma([(cx + u, z0 + z) for u, z in limpio], "xz", cy - fondo / 2, cy + fondo / 2, mat, bisel=0.006)
    else:
        m.prisma([(cy + u, z0 + z) for u, z in limpio], "yz", cx - fondo / 2, cx + fondo / 2, mat, bisel=0.006)


def viga(m, x0, x1, y0, y1, z0, z1, mat="madera_x", juntas=()):
    """Viga corrida en tramos que empalman sobre las zapatas."""
    cortes = [x0] + [j for j in sorted(juntas) if x0 + 0.05 < j < x1 - 0.05] + [x1]
    for a, b in zip(cortes, cortes[1:]):
        ga = 0.004 if a in juntas else 0.0
        gb = 0.004 if b in juntas else 0.0
        dz = m.azar(-0.006, 0.006)
        dy = m.azar(-0.008, 0.008)
        m.caja(a + ga, y0 + dy, z0 + dz, b - gb, y1 + dy, z1 + dz, mat, bisel=0.014, segmentos=2, desorden=0.003)


# ------------------------------------------------------------------ carpintería y herrajes

def clavo(m, x, y, z, radio=0.011, eje="y", mat="hierro"):
    """Clavo de forja de cabeza redondeada, saliendo hacia +eje."""
    m.torno([(radio, 0.0), (radio, 0.003), (radio * 0.75, 0.007), (radio * 0.35, 0.0095), (0.0, 0.0105)],
            (x, y, z), mat, lados=8, eje=eje, tapas=True)


def hoja_tablas(m, x0, x1, z0, z1, y, mat, grosor=0.04, tabla=0.15, filas_clavos=(), clavos=True,
                junta=0.005):
    """Hoja de puerta o postigo: tablas verticales en el plano y (cara hacia +y)."""
    ancho = x1 - x0
    n = max(1, round(ancho / tabla))
    xs = [x0 + ancho * i / n for i in range(n + 1)]
    for i in range(n):
        a = xs[i] + (junta / 2 if i else 0.0)
        b = xs[i + 1] - (junta / 2 if i < n - 1 else 0.0)
        sale = m.azar(-0.003, 0.003)
        m.caja(a, y - grosor, z0, b, y + sale, z1, mat, bisel=0.004, desorden=0.0015,
               giro=Matrix.Rotation(math.radians(m.azar(-0.25, 0.25)), 4, "Y"))
        if clavos:
            for zc in filas_clavos:
                clavo(m, (a + b) / 2 + m.azar(-0.01, 0.01), y + sale, zc + m.azar(-0.008, 0.008))


def pernio(m, x_bisagra, z, y, largo, hacia=1, mat="hierro"):
    """Pernio de pala: pletina de forja clavada, con el extremo en punta."""
    x_fin = x_bisagra + hacia * largo
    a, b = sorted((x_bisagra, x_fin))
    m.caja(a, y, z - 0.022, b, y + 0.006, z + 0.022, mat, 0.002, desorden=0.001)
    punta = [(x_fin, y, z - 0.035), (x_fin + hacia * 0.05, y, z), (x_fin, y, z + 0.035)]
    m.prisma([(p[0], p[2]) for p in (punta if hacia > 0 else list(reversed(punta)))], "xz", y, y + 0.006, mat)
    for k in range(3):
        clavo(m, x_bisagra + hacia * (0.06 + k * largo / 3), y + 0.006, z, 0.008)
    m.torno([(0.016, -0.06), (0.016, 0.06)], (x_bisagra, y + 0.004, z), mat, lados=8, eje="z")


def aldaba(m, x, y, z, mat="hierro"):
    """Aldaba de anilla sobre un escudo de chapa."""
    m.caja(x - 0.045, y, z - 0.055, x + 0.045, y + 0.005, z + 0.055, mat, 0.003)
    clavo(m, x, y + 0.005, z + 0.03, 0.012)
    pts = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        pts.append((x + 0.055 * math.sin(a), y + 0.02 + 0.012 * (1 - math.cos(a)) * 0.5,
                    z + 0.03 - 0.055 * (1 - math.cos(a))))
    m.tubo(pts, 0.008, mat, lados=6, cerrado=True)


def cerradura(m, x, y, z, mat="hierro"):
    m.caja(x - 0.04, y, z - 0.07, x + 0.04, y + 0.004, z + 0.07, mat, 0.003)
    m.caja(x - 0.006, y + 0.003, z - 0.02, x + 0.006, y + 0.006, z + 0.012, "oscuro")
    for dz in (-0.055, 0.055):
        clavo(m, x, y + 0.004, z + dz, 0.007)


def puerta(m, sx, y_cara, ancho=1.2, alto=2.4, mat="madera_z", grosor_muro=0.3, abierta=0.0):
    """Puerta de dos hojas de tablas claveteadas, entre jambas de sillar, con umbral
    de piedra, pernios, aldaba y cerradura. El hueco del muro debe ser sx±(ancho/2+0.2),
    de 0 a alto+0.22."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    # Jambas de sillares alternados (a soga y a tizón).
    for lado, borde in ((-1, x0), (1, x1)):
        z = 0.0
        k = 0
        while z < alto - 0.05:
            h = min(alto - z, m.azar(0.34, 0.5))
            w = 0.2 if k % 2 == 0 else 0.3
            a, b = (borde - w, borde) if lado < 0 else (borde, borde + w)
            m.caja(a + 0.004 * lado, y_cara - grosor_muro, z + 0.005, b, y_cara + m.azar(0.015, 0.03), z + h - 0.005,
                   "piedra", bisel=0.015, segmentos=2, desorden=0.006)
            z += h
            k += 1
    # Dintel de madera y umbral.
    m.caja(x0 - 0.22, y_cara - grosor_muro, alto, x1 + 0.22, y_cara + 0.02, alto + 0.22, "madera_x", bisel=0.012,
           desorden=0.004)
    m.caja(x0 - 0.05, y_cara - grosor_muro, -0.05, x1 + 0.05, y_cara + 0.08, 0.035, "piedra", bisel=0.015,
           segmentos=2, desorden=0.005)
    # Hojas, retranqueadas en el grueso del muro.
    yh = y_cara - 0.15
    filas = (0.25, 0.9, 1.55, 2.15)
    with m.transformada(giro_z(-abierta, (x0, yh, 0))):
        hoja_tablas(m, x0 + 0.005, sx - 0.004, 0.04, alto - 0.01, yh, mat, filas_clavos=filas)
        pernio(m, x0 + 0.01, 0.42, yh, 0.42, 1)
        pernio(m, x0 + 0.01, 2.02, yh, 0.42, 1)
        cerradura(m, sx - 0.12, yh, 1.05)
    hoja_tablas(m, sx + 0.004, x1 - 0.005, 0.04, alto - 0.01, yh, mat, filas_clavos=filas)
    pernio(m, x1 - 0.01, 0.42, yh, 0.42, -1)
    pernio(m, x1 - 0.01, 2.02, yh, 0.42, -1)
    aldaba(m, sx + 0.2, yh, 1.25)
    if abierta:
        m.caja(x0, yh - 1.2, 0, x1, yh - 1.17, alto, "oscuro")


def tienda_cerrada(m, sx, y_cara, ancho=1.7, alto=2.2, mat="madera_z", grosor_muro=0.3):
    """Tienda cerrada de noche: tableros de tablas y barra de hierro con candado.
    Hueco del muro: sx±(ancho/2+0.1), de 0 a alto+0.12."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    for a, b in ((x0 - 0.1, x0), (x1, x1 + 0.1)):
        m.caja(a, y_cara - grosor_muro, 0, b, y_cara + 0.02, alto, "madera_media_z", bisel=0.01, desorden=0.003)
    m.caja(x0 - 0.18, y_cara - grosor_muro, alto, x1 + 0.18, y_cara + 0.03, alto + 0.14, "madera_x", bisel=0.012,
           desorden=0.004)
    m.caja(x0 - 0.04, y_cara - grosor_muro, -0.04, x1 + 0.04, y_cara + 0.06, 0.03, "piedra", bisel=0.012, desorden=0.004)
    yh = y_cara - 0.06
    hoja_tablas(m, x0, x1, 0.03, 0.92, yh, mat, tabla=0.17, filas_clavos=(0.2, 0.72))
    hoja_tablas(m, x0, x1, 0.94, alto - 0.01, yh, mat, tabla=0.21, filas_clavos=(1.15, 1.95))
    m.caja(x0 - 0.06, yh, 0.9, x1 + 0.06, yh + 0.045, 0.96, "madera_x", bisel=0.008)     # peinazo
    # Barra de hierro cruzada y candado.
    m.caja(x0 - 0.12, yh + 0.045, 1.28, x1 + 0.12, yh + 0.07, 1.33, "hierro", 0.003)
    for xa in (x0 - 0.08, x1 + 0.08):
        m.caja(xa - 0.015, yh, 1.25, xa + 0.015, yh + 0.08, 1.36, "hierro", 0.003)
    m.caja(sx - 0.035, yh + 0.07, 1.16, sx + 0.035, yh + 0.095, 1.24, "hierro", 0.004)
    m.tubo([(sx - 0.022, yh + 0.083, 1.24), (sx - 0.022, yh + 0.083, 1.27), (sx, yh + 0.083, 1.295),
            (sx + 0.022, yh + 0.083, 1.27), (sx + 0.022, yh + 0.083, 1.24)], 0.005, "hierro", lados=6)


def vela(m, x, y, z, alto=0.22, radio=0.02, mat="cera_blanca", encendida=False, gastada=0.0):
    perfil = [(radio, 0.0), (radio * 1.05, alto * 0.3), (radio, alto - gastada - 0.01),
              (radio * 0.8, alto - gastada), (0.0, alto - gastada - 0.004)]
    m.torno(perfil, (x, y, z), mat, lados=14, ruido=0.05)
    m.barra((x, y, z + alto - gastada - 0.005), (x + 0.002, y, z + alto - gastada + 0.012), 0.0025, mat="oscuro")
    if encendida:
        m.esfera((x, y, z + alto - gastada + 0.03), (0.009, 0.009, 0.026), "llama", segmentos=10, anillos=8)


def manojo_velas(m, x, y, z_cuelgue, n=6, largo=0.38):
    """Manojo de velas colgadas por el pabilo, como se ponían a secar y a la venta."""
    m.tubo([(x, y, z_cuelgue + 0.04), (x, y, z_cuelgue - 0.03)], 0.004, "tela", lados=5)
    for i in range(n):
        a = 2 * math.pi * i / n + m.azar(-0.3, 0.3)
        dx, dy = 0.022 * math.cos(a), 0.022 * math.sin(a)
        top = (x + dx * 0.4, y + dy * 0.4, z_cuelgue - 0.03)
        bot = (x + dx * 1.8, y + dy * 1.8, z_cuelgue - 0.03 - largo * m.azar(0.9, 1.05))
        m.tubo([top, bot], 0.0105, "cera_blanca", lados=8, radios=[0.007, 0.012])


def tienda_velas(m, sx, y_cara, ancho=1.7, alto=2.2, grosor_muro=0.3):
    """Cerería abierta: tablero bajado como mostrador, hojas abiertas contra el muro,
    velas colgadas en manojos de un varal y una vela encendida en el mostrador."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    for a, b in ((x0 - 0.1, x0), (x1, x1 + 0.1)):
        m.caja(a, y_cara - grosor_muro, 0, b, y_cara + 0.02, alto, "madera_media_z", bisel=0.01, desorden=0.003)
    m.caja(x0 - 0.18, y_cara - grosor_muro, alto, x1 + 0.18, y_cara + 0.03, alto + 0.14, "madera_x", bisel=0.012,
           desorden=0.004)
    m.caja(x0 - 0.04, y_cara - grosor_muro, -0.04, x1 + 0.04, y_cara + 0.06, 0.03, "piedra", bisel=0.012, desorden=0.004)
    # Frente bajo del mostrador y tablero.
    hoja_tablas(m, x0, x1, 0.03, 0.86, y_cara - 0.02, "madera_media_z", tabla=0.17, filas_clavos=(0.2, 0.7))
    m.caja(x0 - 0.02, y_cara - 0.32, 0.86, x1 + 0.02, y_cara + 0.34, 0.91, "madera_media_x", bisel=0.008,
           desorden=0.003)
    for xa in (x0 + 0.2, x1 - 0.2):
        m.barra((xa, y_cara + 0.02, 0.45), (xa, y_cara + 0.3, 0.86), 0.05, mat="madera_media_x")
    # Hojas abiertas contra el muro.
    for a, b, hacia in ((x0 - 0.72, x0 - 0.1, -1), (x1 + 0.1, x1 + 0.72, 1)):
        hoja_tablas(m, a, b, 0.05, alto - 0.02, y_cara + 0.07, "postigo_verde", tabla=0.155,
                    filas_clavos=(0.3, 1.1, 1.9))
        borde = b if hacia < 0 else a
        for zz in (0.35, 1.85):
            pernio(m, borde, zz, y_cara + 0.07, 0.36, hacia * -1)
    # Interior: estancia con anaqueles.
    estancia(m, x0 - 0.1, x1 + 0.1, y_cara - grosor_muro, y_cara - 2.0, 0.0, alto + 0.6, "cal_interior")
    for zz in (0.55, 0.95, 1.35):
        m.caja(x0, y_cara - 2.0, zz, x1, y_cara - 1.7, zz + 0.03, "madera_media_x", 0.005)
        xx = x0 + 0.08
        while xx < x1 - 0.12:
            if m.azar(0, 1) < 0.7:
                for k in range(int(m.azar(2, 5))):
                    vela(m, xx + k * 0.035, y_cara - 1.82 + m.azar(-0.03, 0.03), zz + 0.03, m.azar(0.2, 0.3), 0.012)
            xx += m.azar(0.18, 0.3)
    # Varal con manojos de velas, justo detrás del dintel (la viga tapa lo de más arriba).
    yv = y_cara - 0.1
    m.barra((x0 - 0.05, yv, 1.63), (x1 + 0.05, yv, 1.63), 0.035, mat="madera_media_x")
    xx = x0 + 0.12
    while xx < x1 - 0.08:
        manojo_velas(m, xx, yv, 1.61, n=int(m.azar(5, 8)), largo=m.azar(0.32, 0.4))
        xx += m.azar(0.2, 0.27)
    # Sobre el mostrador: caja de velas, un cabo encendido en su palmatoria y un velón tumbado.
    m.caja(x0 + 0.15, y_cara + 0.05, 0.91, x0 + 0.55, y_cara + 0.25, 1.0, "madera_media_x", 0.006)
    for k in range(7):
        m.barra((x0 + 0.18 + k * 0.05, y_cara + 0.08, 0.99), (x0 + 0.18 + k * 0.05 + 0.01, y_cara + 0.22, 0.995),
                0.022, mat="cera_blanca", bisel=0.008)
    m.torno([(0.0, 0.0), (0.05, 0.0), (0.055, 0.008), (0.012, 0.012), (0.012, 0.04), (0.02, 0.045)],
            (sx + 0.35, y_cara + 0.12, 0.91), "hierro", lados=16)
    vela(m, sx + 0.35, y_cara + 0.12, 0.955, 0.12, 0.016, encendida=True, gastada=0.02)
    return (sx + 0.35, y_cara + 0.12, 0.955 + 0.12)          # posición de la llama


def reja(m, x0, x1, z0, z1, y, barra=0.02, paso=0.115, pletinas=None):
    """Reja de cuadradillo con pletinas horizontales atravesadas."""
    n = max(2, round((x1 - x0) / paso))
    for i in range(1, n):
        x = x0 + (x1 - x0) * i / n
        m.caja(x - barra / 2, y - barra / 2, z0 - 0.04, x + barra / 2, y + barra / 2, z1 + 0.04, "hierro", 0.003)
    for z in pletinas or (z0 + (z1 - z0) * 0.3, z0 + (z1 - z0) * 0.72):
        m.caja(x0 - 0.03, y - 0.006, z - 0.02, x1 + 0.03, y + 0.006, z + 0.02, "hierro", 0.002)
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            m.caja(x - barra * 0.8, y - barra * 0.8, z - 0.026, x + barra * 0.8, y + barra * 0.8, z + 0.026,
                   "hierro", 0.004)


def ventana_baja(m, sx, y_cara, ancho=0.9, z0=0.9, z1=2.0, grosor_muro=0.3):
    """Ventana de planta baja: recerco de piedra, alféizar, reja y postigos cerrados.
    Hueco del muro: sx±(ancho/2+0.1), de z0-0.08 a z1+0.1."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    m.caja(x0 - 0.12, y_cara - grosor_muro, z0 - 0.09, x1 + 0.12, y_cara + 0.07, z0, "piedra", bisel=0.012,
           segmentos=2, desorden=0.004)
    for a, b in ((x0 - 0.1, x0), (x1, x1 + 0.1)):
        m.caja(a, y_cara - grosor_muro, z0, b, y_cara + 0.025, z1, "piedra_b", bisel=0.01, desorden=0.004)
    m.caja(x0 - 0.1, y_cara - grosor_muro, z1, x1 + 0.1, y_cara + 0.025, z1 + 0.11, "piedra_b", bisel=0.01,
           desorden=0.004)
    yh = y_cara - 0.2
    hoja_tablas(m, x0, sx - 0.003, z0, z1, yh, "postigo_verde", tabla=0.15, filas_clavos=(z0 + 0.15, z1 - 0.15))
    hoja_tablas(m, sx + 0.003, x1, z0, z1, yh, "postigo_verde", tabla=0.15, filas_clavos=(z0 + 0.15, z1 - 0.15))
    reja(m, x0, x1, z0, z1, y_cara + 0.04)


def ventana_alta(m, sx, y_cara, z0, z1, ancho=1.0, grosor_muro=0.4, estado="cerrada", mat_hoja="postigo_verde",
                 alfeizar=True):
    """Hueco de la fachada alta con marco y dos hojas de tablas (sin vidriera, como
    en la mayoría de casas de la época). estado: 'cerrada', 'entornada' o 'abierta'."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    ym = y_cara - 0.14
    # Marco.
    m.caja(x0, ym - 0.06, z1 - 0.06, x1, ym + 0.02, z1, "madera_media_x", 0.006)
    m.caja(x0, ym - 0.06, z0, x0 + 0.06, ym + 0.02, z1, "madera_media_z", 0.006)
    m.caja(x1 - 0.06, ym - 0.06, z0, x1, ym + 0.02, z1, "madera_media_z", 0.006)
    if alfeizar:
        m.caja(x0 - 0.1, y_cara - 0.2, z0 - 0.07, x1 + 0.1, y_cara + 0.07, z0, "piedra_b", bisel=0.01, desorden=0.004)
    else:
        m.caja(x0, ym - 0.06, z0, x1, ym + 0.02, z0 + 0.04, "madera_media_x", 0.006)
    giros = {"cerrada": (0, 0), "entornada": (0, 28), "abierta": (95, 100)}[estado]
    yh = ym - 0.04
    ancho_hoja = (x1 - x0 - 0.12) / 2
    with m.transformada(giro_z(-giros[0], (x0 + 0.06, yh - 0.04, 0))):
        hoja_tablas(m, x0 + 0.06, x0 + 0.06 + ancho_hoja - 0.003, z0 + 0.04, z1 - 0.06, yh, mat_hoja, 0.035, 0.13,
                    filas_clavos=(z0 + 0.2, z1 - 0.25))
    with m.transformada(giro_z(giros[1], (x1 - 0.06, yh - 0.04, 0))):
        hoja_tablas(m, x1 - 0.06 - ancho_hoja + 0.003, x1 - 0.06, z0 + 0.04, z1 - 0.06, yh, mat_hoja, 0.035, 0.13,
                    filas_clavos=(z0 + 0.2, z1 - 0.25))


def balcon_forja(m, sx, y_cara, z_suelo, ancho=1.5, vuelo=0.45, alto=0.95):
    """Balcón de losa moldurada sobre canes de hierro, con antepecho de hierro de
    balaustres con macollas y pasamanos de pletina."""
    x0, x1 = sx - ancho / 2, sx + ancho / 2
    yf = y_cara + vuelo
    zl = z_suelo
    perfil = [(y_cara - 0.1, zl), (yf, zl), (yf, zl - 0.035), (yf - 0.015, zl - 0.05), (yf - 0.03, zl - 0.07),
              (yf - 0.06, zl - 0.085), (yf - 0.09, zl - 0.12), (y_cara - 0.1, zl - 0.12)]
    m.prisma(perfil, "yz", x0, x1, "piedra_b", bisel=0.006)
    # Canes de hierro en voluta.
    for xc in (x0 + 0.22, x1 - 0.22):
        pts = []
        for i in range(14):
            t = i / 13
            pts.append((xc, y_cara + 0.01 + t * (vuelo - 0.1), zl - 0.12 - 0.32 * (1 - t) ** 1.6))
        m.tubo(pts, 0.014, "hierro", lados=6)
        ang = [i * 0.35 for i in range(16)]
        espiral = [(xc, y_cara + 0.07 + 0.05 * (1 - a / 6) * math.cos(a), zl - 0.38 + 0.05 * (1 - a / 6) * math.sin(a))
                   for a in ang]
        m.tubo(espiral, 0.009, "hierro", lados=6)
    # Antepecho.
    yb = yf - 0.04
    z0, z1 = zl + 0.03, zl + alto
    esquinas = [(x0 + 0.04, y_cara + 0.01), (x0 + 0.04, yb), (x1 - 0.04, yb), (x1 - 0.04, y_cara + 0.01)]
    for (ax, ay), (bx, by) in zip(esquinas, esquinas[1:]):
        m.barra((ax, ay, z0), (bx, by, z0), 0.03, 0.03, "hierro", bisel=0.004)
        m.barra((ax, ay, z1), (bx, by, z1), 0.05, 0.018, "hierro", bisel=0.004)
        m.barra((ax, ay, z1 - 0.12), (bx, by, z1 - 0.12), 0.022, 0.022, "hierro", bisel=0.003)
        largo = math.hypot(bx - ax, by - ay)
        n = max(2, round(largo / 0.11))
        for i in range(n + 1):
            if (ax, ay) != esquinas[0] and i == 0:
                continue
            t = i / n
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            m.caja(px - 0.009, py - 0.009, z0, px + 0.009, py + 0.009, z1, "hierro", 0.002,
                   giro=Matrix.Rotation(math.radians(45), 4, "Z"))
            for zm in (z0 + 0.3, z0 + 0.55):
                m.torno([(0.009, -0.03), (0.02, -0.018), (0.024, 0.0), (0.02, 0.018), (0.009, 0.03)],
                        (px, py, zm), "hierro", lados=10)
    # Volutas (ces) en el friso alto del antepecho.
    for (ax, ay), (bx, by) in zip(esquinas[1:2], esquinas[2:3]):
        n = round((bx - ax) / 0.11)
        for i in range(n):
            px = ax + (bx - ax) * (i + 0.5) / n
            pts = [(px + 0.035 * math.cos(a), ay, z1 - 0.06 + 0.04 * math.sin(a)) for a in
                   [math.pi * k / 10 for k in range(11)]]
            m.tubo(pts, 0.005, "hierro", lados=5)


def alero_canecillos(m, x0, x1, y_fachada, z_alero, vuelo=0.55, paso=0.38, mat="madera_y"):
    """Alero de canecillos de madera con tablazón encima y cornisa de madera debajo."""
    n = max(1, round((x1 - x0) / paso))
    for i in range(n):
        xc = x0 + (x1 - x0) * (i + 0.5) / n + m.azar(-0.01, 0.01)
        punta = y_fachada + vuelo + m.azar(-0.015, 0.015)
        perfil = [(y_fachada - 0.05, z_alero), (punta, z_alero), (punta, z_alero - 0.055)]
        for k in range(1, 9):
            f = math.pi / 2 * k / 8
            perfil.append((punta - 0.16 * math.sin(f), z_alero - 0.15 + 0.095 * math.cos(f)))
        perfil.append((y_fachada - 0.05, z_alero - 0.15))
        m.prisma(perfil, "yz", xc - 0.043, xc + 0.043, mat, bisel=0.005)
    # Tablazón en tablas a lo largo de x.
    y = y_fachada - 0.05
    while y < y_fachada + vuelo + 0.04:
        yb = min(y_fachada + vuelo + 0.05, y + m.azar(0.14, 0.2))
        m.caja(x0, y + 0.003, z_alero, x1, yb - 0.003, z_alero + 0.028, "madera_x", 0.004, desorden=0.002)
        y = yb
    m.caja(x0, y_fachada - 0.02, z_alero - 0.22, x1, y_fachada + 0.05, z_alero - 0.15, "madera_x", 0.008,
           desorden=0.002)


# ------------------------------------------------------------------ tejado

def _teja(m, centro, a, b, n, largo, r_ancho, r_estrecho, canal, grosor=0.016, segs=6):
    """Una teja árabe (tronco de cono partido). a: eje cuesta arriba; b: lateral; n:
    normal del faldón. canal=True: cóncava hacia arriba, boca ancha arriba;
    canal=False (cobija): convexa, boca ancha abajo."""
    abertura = math.radians(78)
    pts = []
    secciones = 3
    for capa in (0, 1):
        for j in range(secciones):
            t = j / (secciones - 1) - 0.5                        # -0.5 abajo, 0.5 arriba
            r = (r_estrecho + (r_ancho - r_estrecho) * (t + 0.5)) if canal else \
                (r_ancho + (r_estrecho - r_ancho) * (t + 0.5))
            r -= grosor * capa
            for k in range(segs + 1):
                th = -abertura + 2 * abertura * k / segs
                lat = r * math.sin(th)
                alt = -r * math.cos(th) if canal else r * math.cos(th)
                p = centro + a * (t * largo) + b * lat + n * alt
                pts.append(p)
    fila = segs + 1
    capa_n = secciones * fila

    def idx(capa, j, k):
        return capa * capa_n + j * fila + k
    caras = []
    for j in range(secciones - 1):
        for k in range(segs):
            caras.append([idx(0, j, k), idx(0, j, k + 1), idx(0, j + 1, k + 1), idx(0, j + 1, k)])
            caras.append([idx(1, j, k), idx(1, j + 1, k), idx(1, j + 1, k + 1), idx(1, j, k + 1)])
        caras.append([idx(0, j, 0), idx(0, j + 1, 0), idx(1, j + 1, 0), idx(1, j, 0)])
        caras.append([idx(0, j, segs), idx(1, j, segs), idx(1, j + 1, segs), idx(0, j + 1, segs)])
    for j in (0, secciones - 1):
        for k in range(segs):
            caras.append([idx(0, j, k), idx(1, j, k), idx(1, j, k + 1), idx(0, j, k + 1)])
    vs = [m.bm.verts.new(m.M @ p) for p in pts]
    nuevas = []
    for c in caras:
        try:
            nuevas.append(m.bm.faces.new([vs[i] for i in c]))
        except ValueError:
            pass
    import bmesh
    bmesh.ops.recalc_face_normals(m.bm, faces=nuevas)
    m._asignar(nuevas, "teja", liso=True)


def tejado_arabe(m, x0, x1, y_alero, z_alero, y_cumbrera, z_cumbrera, remate_derecho=False, boca_mortero=True):
    """Faldón de teja árabe pieza a pieza: canales y cobijas solapadas, caballete con
    mortero y, si el vecino es más bajo, remate de tejas sobre la medianera."""
    E = B(x0, y_alero, z_alero)
    R = B(x0, y_cumbrera, z_cumbrera)
    abajo = (E - R)
    L = abajo.length
    d = abajo.normalized()                    # cuesta abajo
    a = -d                                    # cuesta arriba
    b = Vector((1, 0, 0))
    n = a.cross(b) if a.cross(b).z > 0 else b.cross(a)
    n.normalize()
    # Tablero bajo las tejas (cierra la luz y se ve en el borde del alero).
    W = x1 - x0
    tablero = [E - n * 0.005, E + b * W - n * 0.005, R + b * W - n * 0.005, R - n * 0.005]
    tablero += [p - n * 0.1 for p in tablero]
    m.solido([_nuestro(p) for p in tablero], _CARAS_CAJA, "madera_x")
    paso_fila = 0.25
    largo = 0.46
    paso = 0.31
    filas = int((x1 - x0) / paso_fila)
    margen = ((x1 - x0) - filas * paso_fila) / 2
    cursos = int(L / paso) + 1
    r_canal = (0.115, 0.088)
    r_cobija = (0.108, 0.082)
    alto_borde_canal = 0.012 + r_canal[0] * (1 - math.cos(math.radians(78)))
    for i in range(filas):
        xc = x0 + margen + paso_fila * (i + 0.5)
        for k in range(cursos):
            s = k * paso + largo / 2 - 0.08                 # distancia desde el alero, cuesta arriba
            if s - largo / 2 > L - 0.05:
                continue
            jit = Vector((m.azar(-0.006, 0.006), 0, 0))
            caida = 0.05 if m.azar(0, 1) < 0.03 else 0.0
            # Canal.
            c = E + b * (xc - x0) + a * (s - caida) + n * (0.012 + r_canal[0]) + jit
            G = Matrix.Rotation(math.radians(m.azar(-1.5, 1.5)), 3, n) @ Matrix.Rotation(math.radians(m.azar(-1.0, 1.0)), 3, b)
            _teja(m, c, G @ a, G @ b, G @ n, largo * m.azar(0.97, 1.0), r_canal[0], r_canal[1], True)
            # Cobija, montada sobre los bordes de dos canales.
            xb = xc + paso_fila / 2
            if xb < x1 - 0.05:
                c2 = E + b * (xb - x0) + a * (s + 0.02 - caida * 0.5) + n * (alto_borde_canal - r_cobija[0] * math.cos(math.radians(78)) + 0.01) + jit
                G2 = Matrix.Rotation(math.radians(m.azar(-2.0, 2.0)), 3, n) @ Matrix.Rotation(math.radians(m.azar(-1.5, 1.5)), 3, b)
                _teja(m, c2, G2 @ a, G2 @ b, G2 @ n, largo * m.azar(0.96, 1.0), r_cobija[0], r_cobija[1], False)
        if boca_mortero:
            xb = xc + paso_fila / 2
            if xb < x1 - 0.05:
                c3 = E + b * (xb - x0) + a * 0.0 + n * (alto_borde_canal + 0.03)
                m.esfera(tuple(Vector((c3.x, -c3.y, c3.z))), (0.06, 0.02, 0.045), "mortero", 8, 5, desorden=0.006)
    # Caballete.
    zc = R + n * 0.02
    m.caja(x0, -(zc.y) - 0.12, zc.z - 0.04, x1, -(zc.y) + 0.12, zc.z + 0.06, "mortero", 0.03, desorden=0.01)
    x = x0 - 0.1
    while x < x1:
        c = Vector((x + 0.22, zc.y, zc.z + 0.07))
        _teja(m, c, Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.46, 0.13, 0.1, False)
        x += 0.36
    if remate_derecho:
        xr = x1 - 0.12
        s = 0.0
        while s < L:
            c = E + b * (xr - x0) + a * (s + 0.2) + n * 0.17
            _teja(m, c, a, b, n, 0.46, 0.12, 0.09, False)
            s += 0.34
        lomo = [E + a * 0.05 + b * (xr - x0 - 0.14), E + a * 0.05 + b * (xr - x0 + 0.14),
                R + b * (xr - x0 + 0.14), R + b * (xr - x0 - 0.14)]
        lomo += [p + n * 0.12 for p in lomo]
        m.solido([_nuestro(p) for p in lomo], _CARAS_CAJA, "mortero")


_CARAS_CAJA = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]


def _nuestro(p):
    """Vector de Blender → tupla en nuestras coordenadas."""
    return (p.x, -p.y, p.z)


# ------------------------------------------------------------------ hornacina

def hornacina(m, hx, y_cara, z0, ancho=0.55, alto=0.675, fondo=0.22, imagen=None):
    """Hornacina de medio punto con repisa moldurada, lienzo devoto, vela encendida y
    goterones de cera negra. Hueco del muro: hx..hx+ancho, z0..z0+alto."""
    r = ancho / 2
    zr = z0 + alto - r                      # arranque del arco
    # Enjutas: rellenan el hueco rectangular por encima del arco.
    for lado in (-1, 1):
        cx = hx + r
        borde = hx if lado < 0 else hx + ancho
        arco = [(cx + lado * r * math.cos(math.pi / 2 * k / 10), zr + r * math.sin(math.pi / 2 * k / 10))
                for k in range(11)]
        perfil = [(borde, zr), (borde, z0 + alto)] + list(reversed(arco[1:]))
        if lado > 0:
            perfil = list(reversed(perfil))
        m.prisma(perfil, "xz", y_cara - fondo, y_cara, "cal_hornacina")
    m.caja(hx, y_cara - 0.32, z0, hx + ancho, y_cara - fondo, z0 + alto, "cal_hornacina")
    # Hollín sobre la llama.
    pts = [(hx + r + 0.12 * math.cos(t) * (1 + 0.15 * math.sin(3 * t)), y_cara - fondo + 0.002,
            zr + 0.05 + 0.16 * math.sin(t) * (0.8 + 0.2 * math.cos(2 * t))) for t in
           [math.pi * k / 14 for k in range(15)]]
    m.poligono([(hx + r + 0.12, y_cara - fondo + 0.002, zr - 0.05)] + pts + [(hx + r - 0.12, y_cara - fondo + 0.002, zr - 0.05)],
               "hollin")
    # Moldura de ladrillo agramilado alrededor del arco.
    yb = y_cara + 0.012
    contorno = [(hx - 0.035, yb, z0)] + [(hx + r - (r + 0.035) * math.cos(math.pi * k / 16), yb,
                                          zr + (r + 0.035) * math.sin(math.pi * k / 16)) for k in range(17)]
    contorno += [(hx + ancho + 0.035, yb, z0)]
    m.tubo(contorno, 0.024, "piedra_b", lados=6, liso=False)
    # Repisa moldurada.
    perfil = [(y_cara - fondo, z0), (y_cara + 0.11, z0), (y_cara + 0.11, z0 - 0.03), (y_cara + 0.095, z0 - 0.045),
              (y_cara + 0.07, z0 - 0.06), (y_cara + 0.045, z0 - 0.08), (y_cara + 0.02, z0 - 0.105),
              (y_cara - fondo, z0 - 0.105)]
    m.prisma(perfil, "yz", hx - 0.08, hx + ancho + 0.08, "piedra", bisel=0.005)
    # Lienzo con marco dorado, apoyado en el fondo.
    lx0, lx1 = hx + r - 0.13, hx + r + 0.13
    lz0, lz1 = z0 + 0.12, z0 + 0.5
    yl = y_cara - fondo + 0.03
    m.caja(lx0 - 0.03, yl - 0.02, lz0 - 0.03, lx1 + 0.03, yl, lz1 + 0.03, "oro_viejo", 0.006)
    m.poligono([(lx0, yl + 0.001, lz0), (lx1, yl + 0.001, lz0), (lx1, yl + 0.001, lz1), (lx0, yl + 0.001, lz1)],
               f"imagen:{imagen}" if imagen else "oscuro", uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # Vela blanca encendida, en su charco de cera.
    xv, yv = hx + r, y_cara - 0.05
    m.esfera((xv, yv, z0 + 0.004), (0.045, 0.04, 0.008), "cera_blanca", 12, 5, desorden=0.003)
    vela(m, xv, yv, z0, 0.27, 0.021, encendida=True, gastada=0.02)
    # Cera negra: cabos derretidos y goterones que caen por la repisa y el muro.
    for gx, gy, h in ((hx + 0.1, y_cara - 0.12, 0.05), (hx + ancho - 0.12, y_cara - 0.02, 0.035)):
        m.torno([(0.02, 0.0), (0.019, h * 0.6), (0.014, h), (0.0, h + 0.004)], (gx, gy, z0), "cera_negra",
                lados=10, ruido=0.25)
        m.esfera((gx, gy, z0 + 0.003), (0.04, 0.035, 0.007), "cera_negra", 10, 5, desorden=0.004)
    def y_moldura(z):
        """Cara de la repisa a la altura z (sigue la moldura)."""
        for (ya, za), (yb, zb) in zip(perfil[1:], perfil[2:]):
            if zb <= z <= za:
                return ya + (yb - ya) * (za - z) / max(1e-6, za - zb)
        return y_cara + 0.005
    for gx, largo, sigue in ((hx + 0.08, 0.16, True), (hx + 0.19, 0.07, False), (hx + ancho - 0.1, 0.25, True),
                             (hx + ancho - 0.02, 0.09, False), (hx + 0.33, 0.05, False)):
        pts, radios = [], []
        for k in range(8):
            z = z0 + 0.002 - min(largo, 0.105) * k / 7
            pts.append((gx + 0.003 * math.sin(k * 1.7), y_moldura(z) + 0.004, z))
            radios.append(0.008 * (1 - 0.35 * k / 7))
        radios[-1] = 0.011
        m.tubo(pts, 0.008, "cera_negra", lados=6, radios=radios)
        if sigue and largo > 0.11:
            # El goterón sigue cayendo por el muro, bajo la repisa.
            zt = z0 - 0.105
            pts = [(gx + 0.002, y_cara + 0.006, zt - (largo - 0.105) * k / 6) for k in range(7)]
            radios = [0.006 * (1 - 0.3 * k / 6) for k in range(7)]
            radios[-1] = 0.009
            m.tubo(pts, 0.006, "cera_negra", lados=6, radios=radios)


# ------------------------------------------------------------------ objetos

def rueda_radios(m, centro, radio, ancho, eje_lateral="y", radios=12, mat="madera_media_z"):
    """Rueda de carro: pinas, radios, cubo y llanta de hierro claveteada."""
    cx, cy, cz = centro
    lado = 1
    def P(r, a, dy=0.0):
        return (cx + r * math.cos(a), cy + dy, cz + r * math.sin(a))
    # Llanta de hierro y pinas de madera (anillo segmentado).
    m.torno([(radio, -ancho / 2), (radio + 0.012, -ancho / 2 + 0.005), (radio + 0.012, ancho / 2 - 0.005),
             (radio, ancho / 2), (radio - 0.004, ancho / 2), (radio - 0.004, -ancho / 2)], (cx, cy, cz),
            "hierro", lados=48, eje="y", liso=False)
    for k in range(6):
        a0 = 2 * math.pi * k / 6 + 0.01
        a1 = 2 * math.pi * (k + 1) / 6 - 0.01
        m.torno([(radio - 0.004, -ancho / 2 + 0.005), (radio - 0.004, ancho / 2 - 0.005),
                 (radio - 0.075, ancho / 2 - 0.01), (radio - 0.075, -ancho / 2 + 0.01)], (cx, cy, cz), mat,
                lados=8, eje="y", liso=False, tapas=False, angulo=(a0, a1))
    for k in range(radios):
        a = 2 * math.pi * k / radios
        m.barra(P(0.08, a), P(radio - 0.07, a), 0.038, 0.03, mat, bisel=0.006, arriba=(0, 1, 0))
    m.torno([(0.06, -0.12), (0.085, -0.09), (0.095, -0.03), (0.095, 0.03), (0.085, 0.09), (0.06, 0.12)],
            (cx, cy, cz), "madera_media_y", lados=16, eje="y")
    m.torno([(0.064, -0.13), (0.064, -0.1)], (cx, cy, cz), "hierro", lados=16, eje="y")
    m.torno([(0.064, 0.1), (0.064, 0.13)], (cx, cy, cz), "hierro", lados=16, eje="y")
    m.torno([(0.035, 0.12), (0.035, 0.16), (0.0, 0.17)], (cx, cy, cz), "hierro", lados=10, eje="y")
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        x, _, z = P(radio + 0.012, a)
        m.esfera((x, cy, z), (0.009, 0.009, 0.009), "hierro", 6, 4)


def carro(m, x0, x1, y0, y1, z_caja=0.68, mat="madera_media_x"):
    """Carro de dos ruedas y varas, desenganchado y con las varas en el suelo.
    La caja va de x0 a x1 (varas hacia -x) y de y0 a y1."""
    largo = x1 - x0
    xr = x0 + largo * 0.55                            # eje bajo el centro de la caja
    rr = 0.58
    # Varas: suben desde el suelo por delante hasta pasar bajo la caja.
    for yv in (y0 + 0.1, y1 - 0.1):
        m.barra((x0 - 1.9, yv, 0.06), (x1 + 0.05, yv, z_caja - 0.06), 0.075, 0.09, "madera_media_x", bisel=0.012)
        m.barra((x0 - 1.95, yv, 0.03), (x0 - 1.88, yv, 0.12), 0.06, 0.05, "hierro", bisel=0.008)
    # Lecho de tablas y travesaños.
    m.caja(x0, y0, z_caja - 0.05, x1, y1, z_caja, mat, 0.006)
    yy = y0
    while yy < y1 - 0.02:
        yb = min(y1, yy + m.azar(0.16, 0.22))
        m.caja(x0 - 0.02, yy + 0.003, z_caja, x1 + 0.02, yb - 0.003, z_caja + 0.035, mat, 0.006, desorden=0.003)
        yy = yb
    # Adrales de estacas y largueros.
    for ya in (y0 + 0.02, y1 - 0.02):
        n = 7
        for i in range(n):
            xa = x0 + 0.06 + (largo - 0.12) * i / (n - 1)
            m.barra((xa, ya, z_caja - 0.02), (xa + m.azar(-0.01, 0.01), ya + m.azar(-0.01, 0.01), z_caja + 0.5), 0.04,
                    0.04, "madera_media_z", bisel=0.008)
        for zz in (z_caja + 0.2, z_caja + 0.47):
            m.barra((x0 - 0.03, ya, zz), (x1 + 0.03, ya, zz + m.azar(-0.01, 0.01)), 0.05, 0.035, mat, bisel=0.008)
    for xa in (x0 + 0.02, x1 - 0.02):
        m.barra((xa, y0, z_caja + 0.3), (xa, y1, z_caja + 0.3), 0.04, 0.035, "madera_media_y", bisel=0.008)
    # Eje y ruedas.
    m.barra((xr, y0 - 0.25, rr), (xr, y1 + 0.25, rr), 0.08, 0.08, "madera_media_y", bisel=0.01)
    rueda_radios(m, (xr, y1 + 0.17, rr), rr, 0.08)
    rueda_radios(m, (xr, y0 - 0.17, rr), rr, 0.08)
    # Carga: dos sacos atados por la boca y una gavilla de paja atada por el medio.
    for sx, sy, giro in ((x0 + 0.62, (y0 + y1) / 2 - 0.12, 8), (x0 + 1.28, (y0 + y1) / 2 + 0.14, -14)):
        with m.transformada(giro_z(giro, (sx, sy, 0))):
            m.esfera((sx, sy, z_caja + 0.15), (0.3, 0.21, 0.15), "tela", 14, 9, desorden=0.025)
            m.torno([(0.06, 0.0), (0.035, 0.05), (0.045, 0.1), (0.07, 0.14), (0.0, 0.15)], (sx + 0.3, sy, z_caja + 0.17),
                    "tela", lados=10, eje="x", ruido=0.2)
    gx, gy = x1 - 0.62, (y0 + y1) / 2 + 0.05
    perfil = [(0.0, -0.45), (0.13, -0.44), (0.12, -0.3), (0.095, -0.12), (0.08, 0.0), (0.095, 0.12),
              (0.12, 0.3), (0.13, 0.44), (0.0, 0.45)]
    m.torno(perfil, (gx, gy, z_caja + 0.13), "paja", lados=16, eje="x", ruido=0.12)
    m.torno([(0.085, -0.02), (0.085, 0.02)], (gx, gy, z_caja + 0.13), "tela", lados=16, eje="x", tapas=False)


def barril(m, cx, cy, alto=0.95, radio=0.33, duelas=18, mat="madera_media_z", aros_hierro=True):
    """Barril de duelas con barriga, tapa con su chimenea y aros."""
    panza = 0.06
    for k in range(duelas):
        a0 = 2 * math.pi * k / duelas + 0.004
        a1 = 2 * math.pi * (k + 1) / duelas - 0.004
        perfil = []
        for j in range(9):
            t = j / 8
            r = radio - panza + panza * math.sin(math.pi * t) + 0.0
            perfil.append((r + m.azar(-0.002, 0.002), alto * t))
        m.torno(perfil, (cx, cy, 0.0), mat, lados=3, angulo=(a0, a1), tapas=False, liso=True)
        m.torno([(p[0] - 0.022, p[1]) for p in reversed(perfil)], (cx, cy, 0.0), mat, lados=3, angulo=(a0, a1),
                tapas=False, liso=True)
    # Fondos de tablas, metidos en el jable de las duelas.
    rt = radio - panza - 0.012
    for zt in (alto - 0.045, 0.03):
        xs = [-rt + 2 * rt * i / 5 for i in range(6)]
        for xa, xb in zip(xs, xs[1:]):
            cuerda = math.sqrt(max(0.0, rt * rt - max(abs(xa), abs(xb)) ** 2)) if xa * xb > 0 else rt
            m.caja(cx + xa + 0.002, cy - cuerda, zt - 0.02, cx + xb - 0.002, cy + cuerda, zt, "madera_media_y", 0.004)
    for t in (0.06, 0.2, 0.8, 0.94):
        r = radio - panza + panza * math.sin(math.pi * t)
        mat_aro = "hierro" if aros_hierro else "madera_media_y"
        m.torno([(r + 0.002, alto * t - 0.022), (r + 0.006, alto * t - 0.018), (r + 0.006, alto * t + 0.018),
                 (r + 0.002, alto * t + 0.022)], (cx, cy, 0.0), mat_aro, lados=36, tapas=False)


def empedrado(rng, x0, x1, y0, y1, dentro, paso=0.105, saltar_y=(), maestras=()):
    """Empedrado de canto rodado asentado en tierra, con maestras (hileras de piedras
    mayores, de través) en las x indicadas. `dentro(x, y)` dice qué celdas poblar,
    para no modelar lo que no sale en la imagen. Devuelve centros, radios y giros para
    base.nube()."""
    centros, radios, giros = [], [], []
    y, fila = y0, 0
    while y < y1:
        x = x0 + (fila % 2) * paso / 2
        while x < x1:
            px, py = x + rng.uniform(-0.025, 0.025), y + rng.uniform(-0.025, 0.025)
            if dentro(px, py) and not any(a <= py <= b for a, b in saltar_y) and \
                    not any(abs(px - mx) < 0.13 for mx in maestras):
                centros.append((px, py, rng.uniform(-0.008, 0.002)))
                radios.append((rng.uniform(0.04, 0.06), rng.uniform(0.03, 0.048), rng.uniform(0.022, 0.036)))
                giros.append(rng.uniform(0, 180))
            x += paso
        y += paso * 0.87
        fila += 1
    for mx in maestras:
        y = y0
        while y < y1:
            largo = rng.uniform(0.16, 0.24)
            if dentro(mx, y) and not any(a <= y + largo / 2 <= b for a, b in saltar_y):
                centros.append((mx, y + largo / 2, 0.004))
                radios.append((largo / 2, rng.uniform(0.06, 0.075), 0.034))
                giros.append(90 + rng.uniform(-6, 6))
            y += largo + 0.02
    return centros, radios, giros
