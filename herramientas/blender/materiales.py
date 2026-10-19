"""Materiales procedurales para las piezas (Cycles).

Todos trabajan en coordenadas del objeto, en metros: las piezas se modelan en
coordenadas del mundo, así que la textura sigue de una casa a la vecina sin saltos.
Cada isla de la malla (una tabla, una teja, un sillar) varía su color con
«Random Per Island».

Los colores se escriben en sRGB y se pasan a lineal con srgb().
"""
import bpy

from base import srgb

_CACHE = {}
OCLUSION = False


class Arbol:
    """Pequeño ayudante para montar árboles de nodos sin ruido."""

    def __init__(self, nombre):
        self.mat = bpy.data.materials.new(nombre)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.salida = self.nt.nodes.new("ShaderNodeOutputMaterial")

    def poner(self, socket, valor):
        if isinstance(valor, bpy.types.NodeSocket):
            self.nt.links.new(valor, socket)
        elif isinstance(valor, bpy.types.Node):
            self.nt.links.new(valor.outputs[0], socket)
        elif isinstance(valor, (tuple, list)) and socket.type == "RGBA" and len(valor) == 3:
            socket.default_value = (*valor, 1.0)
        else:
            socket.default_value = valor

    def nodo(self, tipo, entradas=None, **props):
        n = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        for k, v in (entradas or {}).items():
            self.poner(n.inputs[k], v)
        return n

    # --- coordenadas
    def coord(self, escala=(1, 1, 1), desplaz=(0, 0, 0)):
        tc = self.nodo("ShaderNodeTexCoord")
        m = self.nodo("ShaderNodeMapping", {"Vector": tc.outputs["Object"], "Location": desplaz, "Scale": escala})
        return m.outputs[0]

    def isla(self):
        return self.nodo("ShaderNodeNewGeometry").outputs["Random Per Island"]

    def geometria(self, salida):
        return self.nodo("ShaderNodeNewGeometry").outputs[salida]

    def vsum(self, a, b):
        return self.nodo("ShaderNodeVectorMath", {0: a, 1: b}, operation="ADD").outputs[0]

    def vmul(self, a, b):
        return self.nodo("ShaderNodeVectorMath", {0: a, 1: b}, operation="MULTIPLY").outputs[0]

    def separar(self, v):
        return self.nodo("ShaderNodeSeparateXYZ", {"Vector": v}).outputs

    def combinar(self, x, y, z):
        return self.nodo("ShaderNodeCombineXYZ", {"X": x, "Y": y, "Z": z}).outputs[0]

    # --- texturas
    def ruido(self, v, escala, detalle=4.0, rugosidad=0.55, distorsion=0.0, salida="Fac"):
        n = self.nodo("ShaderNodeTexNoise", {"Vector": v, "Scale": escala, "Detail": detalle,
                                             "Roughness": rugosidad, "Distortion": distorsion})
        return n.outputs[salida]

    def voronoi(self, v, escala, salida="Distance", rasgo="F1", aleatorio=1.0):
        n = self.nodo("ShaderNodeTexVoronoi", {"Vector": v, "Scale": escala, "Randomness": aleatorio},
                      feature=rasgo)
        return n.outputs[salida]

    def ladrillo(self, v, color1, color2, mortero, escala=1.0, ancho=0.28, alto=0.07, junta=0.012):
        n = self.nodo("ShaderNodeTexBrick", {"Vector": v, "Color1": color1, "Color2": color2, "Mortar": mortero,
                                             "Scale": escala, "Mortar Size": junta, "Mortar Smooth": 0.3,
                                             "Brick Width": ancho, "Row Height": alto, "Bias": 0.0},
                      offset=0.5, squash=1.0)
        return n.outputs["Color"], n.outputs["Fac"]

    def onda(self, v, escala, tipo="RINGS", direccion="Z", distorsion=6.0, detalle=3.0, fase=0.0):
        n = self.nodo("ShaderNodeTexWave", {"Vector": v, "Scale": escala, "Distortion": distorsion,
                                            "Detail": detalle, "Detail Scale": 1.5, "Detail Roughness": 0.6,
                                            "Phase Offset": fase}, wave_type=tipo)
        if tipo == "RINGS":
            n.rings_direction = direccion
        else:
            n.bands_direction = direccion
        n.wave_profile = "SIN"
        return n.outputs["Fac"]

    # --- operaciones
    def rampa(self, fac, paradas, interpolacion="LINEAR"):
        n = self.nodo("ShaderNodeValToRGB", {"Fac": fac})
        cr = n.color_ramp
        cr.interpolation = interpolacion
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        for i, (pos, col) in enumerate(paradas):
            e = cr.elements[0] if i == 0 else cr.elements.new(pos)
            e.position = pos
            col = col if len(col) == 4 else (*col, 1.0)
            e.color = col
        return n.outputs["Color"]

    def gris(self, fac, a, b, interpolacion="LINEAR"):
        """Rampa en escala de grises de a (0) a b (1)."""
        return self.rampa(fac, [(a, (0, 0, 0)), (b, (1, 1, 1))], interpolacion)

    def mezcla(self, fac, a, b, modo="MIX"):
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = modo
        n.clamp_result = True
        self.poner(n.inputs[0], fac)
        self.poner(n.inputs[6], a)
        self.poner(n.inputs[7], b)
        return n.outputs[2]

    def mate(self, op, a, b=0.0, c=None, clamp=False):
        n = self.nodo("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.poner(n.inputs[0], a)
        self.poner(n.inputs[1], b)
        if c is not None:
            self.poner(n.inputs[2], c)
        return n.outputs[0]

    def rango(self, v, de0, de1, a0=0.0, a1=1.0, clamp=True):
        n = self.nodo("ShaderNodeMapRange", {"Value": v, "From Min": de0, "From Max": de1,
                                             "To Min": a0, "To Max": a1}, clamp=clamp)
        return n.outputs[0]

    def tono(self, color, h=0.5, s=1.0, v=1.0):
        return self.nodo("ShaderNodeHueSaturation", {"Color": color, "Hue": h, "Saturation": s, "Value": v}).outputs[0]

    def relieve(self, altura, fuerza, distancia=0.01, normal=None):
        n = self.nodo("ShaderNodeBump", {"Height": altura, "Strength": fuerza, "Distance": distancia})
        if normal is not None:
            self.poner(n.inputs["Normal"], normal)
        return n.outputs["Normal"]

    def oclusion(self, distancia=0.1):
        """Oclusión ambiental como máscara de suciedad. Es cara en Cycles (lanza rayos
        en cada evaluación), así que solo se usa si OCLUSION está activada; si no,
        devuelve 1 (sin suciedad de rincón: el trazado de rayos ya oscurece los rincones)."""
        if not OCLUSION:
            return 1.0
        n = self.nodo("ShaderNodeAmbientOcclusion", {"Distance": distancia}, samples=4)
        return n.outputs["AO"]

    # --- salida
    def superficie(self, color, rugosidad=0.85, normal=None, metal=0.0, especular=0.35, emision=None,
                   fuerza_emision=0.0, subsuperficie=0.0, brillo_capa=0.0):
        b = self.nodo("ShaderNodeBsdfPrincipled")
        self.poner(b.inputs["Base Color"], color)
        self.poner(b.inputs["Roughness"], rugosidad)
        self.poner(b.inputs["Metallic"], metal)
        self.poner(b.inputs["Specular IOR Level"], especular)
        if normal is not None:
            self.poner(b.inputs["Normal"], normal)
        if emision is not None:
            self.poner(b.inputs["Emission Color"], emision)
            self.poner(b.inputs["Emission Strength"], fuerza_emision)
        if subsuperficie:
            self.poner(b.inputs["Subsurface Weight"], subsuperficie)
            b.inputs["Subsurface Radius"].default_value = (0.02, 0.015, 0.01)
        if brillo_capa:
            self.poner(b.inputs["Coat Weight"], brillo_capa)
        self.nt.links.new(b.outputs[0], self.salida.inputs["Surface"])
        return self.mat


# ------------------------------------------------------------------ materiales

TONOS_CAL = {
    # (sombra de la mancha, tono medio, luz), en sRGB
    "blanco": ((0.62, 0.60, 0.55), (0.72, 0.70, 0.64), (0.79, 0.77, 0.71)),
    "ocre": ((0.52, 0.42, 0.29), (0.62, 0.51, 0.36), (0.69, 0.59, 0.44)),
    "almagra": ((0.36, 0.20, 0.15), (0.45, 0.26, 0.19), (0.52, 0.33, 0.25)),
    "hornacina": ((0.80, 0.78, 0.72), (0.88, 0.86, 0.80), (0.92, 0.91, 0.86)),
    "interior": ((0.36, 0.31, 0.25), (0.46, 0.40, 0.32), (0.52, 0.45, 0.36)),
}


def cal(tono):
    """Enlucido de cal: manchas, chorretones bajo los huecos, humedad que sube del
    suelo, desconchones que dejan ver el ladrillo."""
    A = Arbol(f"cal_{tono}")
    oscuro, medio, claro = (srgb(c) for c in TONOS_CAL[tono])
    v = A.coord()
    x, y, z = A.separar(v)
    plano = A.combinar(A.mate("ADD", x, y), z, 0.0)          # coordenada sobre el paramento
    manchas = A.ruido(v, 0.9, 8, 0.62)
    base = A.rampa(manchas, [(0.3, oscuro), (0.5, medio), (0.72, claro)])
    grano = A.ruido(v, 14.0, 6, 0.6)
    base = A.mezcla(A.rango(grano, 0.3, 0.7, 0.0, 0.18), base, srgb((0.45, 0.42, 0.38)), "MULTIPLY")
    # Chorretones verticales de lluvia y polvo.
    chorro = A.ruido(A.coord((7.0, 7.0, 0.45)), 1.0, 3, 0.5)
    chorro = A.rango(chorro, 0.52, 0.75, 0.0, 0.35)
    base = A.mezcla(chorro, base, srgb((0.38, 0.35, 0.31)), "MULTIPLY")
    # Humedad que sube del suelo (salitre y verdín).
    borde = A.mate("ADD", z, A.mate("MULTIPLY", A.ruido(v, 2.5, 4), 0.6))
    humedad = A.rango(borde, 1.25, 0.45, 0.0, 0.75)
    base = A.mezcla(humedad, base, srgb((0.36, 0.35, 0.30)), "MULTIPLY")
    # Desconchones: debajo asoma el ladrillo del aparejo.
    mascara_n = A.ruido(A.coord((1.0, 1.0, 1.6)), 0.55, 5, 0.6, distorsion=0.4)
    desconchon = A.rango(mascara_n, 0.668, 0.678)
    lad_col, lad_junta = A.ladrillo(plano, srgb((0.42, 0.23, 0.15)), srgb((0.33, 0.17, 0.11)),
                                    srgb((0.36, 0.33, 0.28)), 1.0, 0.28, 0.075, 0.013)
    # Capas de lechada: manchas de borde vivo, una mano de cal más clara encima de otra.
    capas = A.rango(A.ruido(A.coord((1.0, 1.0, 1.3)), 1.4, 6, 0.65, distorsion=0.6), 0.56, 0.575)
    base = A.mezcla(A.mate("MULTIPLY", capas, 0.55), base, srgb(claro))
    # Grietas finas del enlucido.
    borde = A.voronoi(A.coord((1.0, 1.0, 0.8)), 2.2, "Distance", "DISTANCE_TO_EDGE")
    grieta = A.mate("MULTIPLY", A.rango(borde, 0.004, 0.0), A.rango(A.ruido(v, 1.5, 3), 0.55, 0.65))
    base = A.mezcla(A.mate("MULTIPLY", grieta, 0.8), base, srgb((0.12, 0.1, 0.09)))
    # Hollín y polvo junto a la viga del soportal.
    hollin = A.mate("MULTIPLY", A.rango(z, 2.7, 3.6), A.rango(z, 4.6, 3.9))
    hollin = A.mate("MULTIPLY", hollin, A.rango(A.ruido(v, 3.0, 4), 0.3, 0.7, 0.35, 0.8))
    base = A.mezcla(hollin, base, srgb((0.22, 0.2, 0.18)), "MULTIPLY")
    color = A.mezcla(desconchon, base, lad_col)
    # Relieve: grano fino, ondulación de la llana, bordes de las capas y de los desconchones.
    n1 = A.relieve(A.ruido(v, 45.0, 6, 0.65), 0.22, 0.004)
    n2 = A.relieve(A.ruido(v, 4.0, 4, 0.55), 0.35, 0.012, n1)
    n3 = A.relieve(capas, 0.25, 0.003, n2)
    n4 = A.relieve(A.mate("MULTIPLY", grieta, -1.0), 0.6, 0.003, n3)
    n5 = A.relieve(A.mate("SUBTRACT", desconchon, A.mate("MULTIPLY", lad_junta, desconchon)), 0.7, 0.012, n4)
    return A.superficie(color, 0.92, n5, especular=0.22)


def tapial():
    """Aparejo toledano de medianera: cajones de tapial entre verdugadas y rafas de
    ladrillo, sin enlucir."""
    A = Arbol("tapial")
    v = A.coord()
    x, y, z = A.separar(v)
    plano = A.combinar(A.mate("ADD", x, y), z, 0.0)
    tierra = A.rampa(A.ruido(v, 1.6, 6, 0.6), [(0.35, srgb((0.42, 0.34, 0.25))), (0.65, srgb((0.56, 0.47, 0.35)))])
    tierra = A.mezcla(A.rango(A.ruido(v, 22, 4), 0.35, 0.7, 0, 0.3), tierra, srgb((0.3, 0.26, 0.2)), "MULTIPLY")
    # Cajones de 1,4 × 0,85 m separados por verdugadas de ladrillo de unos 0,16 m.
    caj_col, caj_fac = A.ladrillo(plano, (1, 1, 1), (1, 1, 1), (0, 0, 0), 1.0, 1.4, 0.85, 0.16)
    lad_col, lad_junta = A.ladrillo(plano, srgb((0.44, 0.23, 0.15)), srgb((0.36, 0.18, 0.11)),
                                    srgb((0.5, 0.45, 0.38)), 1.0, 0.28, 0.053, 0.012)
    es_ladrillo = A.mate("GREATER_THAN", caj_fac, 0.5)
    color = A.mezcla(es_ladrillo, tierra, lad_col)
    n1 = A.relieve(A.ruido(v, 18, 5, 0.65), 0.35, 0.008)
    n2 = A.relieve(A.mate("ADD", A.mate("MULTIPLY", es_ladrillo, 0.5), A.mate("MULTIPLY", lad_junta, -0.4)), 0.5,
                   0.01, n1)
    return A.superficie(color, 0.95, n2, especular=0.2)


def piedra(variante=0):
    """Caliza gastada de columnas, basas y repisas."""
    A = Arbol(f"piedra_{variante}")
    v = A.vsum(A.coord(), A.combinar(A.mate("MULTIPLY", A.isla(), 31.0), 0.0, 0.0))
    tonos = [((0.40, 0.38, 0.34), (0.50, 0.48, 0.43), (0.57, 0.55, 0.49)),
             ((0.42, 0.39, 0.33), (0.52, 0.48, 0.41), (0.58, 0.54, 0.46))][variante % 2]
    base = A.rampa(A.ruido(v, 2.2, 7, 0.6), [(0.3, srgb(tonos[0])), (0.55, srgb(tonos[1])), (0.75, srgb(tonos[2]))])
    vetas = A.rango(A.ruido(v, 2.5, 5, 0.55, 2.5), 0.58, 0.7, 0, 0.22)
    base = A.mezcla(vetas, base, srgb((0.4, 0.38, 0.34)), "MULTIPLY")
    poros = A.voronoi(v, 60.0)
    picado = A.rango(poros, 0.0, 0.12, 1.0, 0.0)
    # Suciedad en la parte baja y en los rincones.
    x, y, z = A.separar(A.coord())
    pie = A.rango(A.mate("ADD", z, A.mate("MULTIPLY", A.ruido(v, 4, 3), 0.25)), 0.55, 0.0, 0, 0.6)
    base = A.mezcla(pie, base, srgb((0.30, 0.28, 0.25)), "MULTIPLY")
    ao = A.oclusion(0.08)
    base = A.mezcla(A.rango(ao, 0.2, 1.0, 0.65, 0.0), base, srgb((0.25, 0.23, 0.21)), "MULTIPLY")
    n1 = A.relieve(A.ruido(v, 40, 6, 0.65), 0.25, 0.003)
    n2 = A.relieve(picado, 0.3, 0.004, n1)
    n3 = A.relieve(A.ruido(v, 5, 4, 0.55), 0.3, 0.012, n2)
    return A.superficie(base, 0.88, n3, especular=0.3)


def madera(eje="Z", tono="oscura"):
    """Madera vieja de pino o negrillo: fibra larga en la dirección de la pieza, veta
    de anillos, grietas finas a lo largo, nudos y el gris del sol y la lluvia."""
    A = Arbol(f"madera_{eje}_{tono}")
    isla = A.isla()
    v = A.vsum(A.coord(), A.combinar(A.mate("MULTIPLY", isla, 17.0), A.mate("MULTIPLY", isla, 7.0),
                                      A.mate("MULTIPLY", isla, 11.0)))
    colores = {
        "oscura": ((0.15, 0.10, 0.065), (0.24, 0.165, 0.105), (0.32, 0.23, 0.15)),
        "media": ((0.22, 0.155, 0.10), (0.33, 0.24, 0.16), (0.42, 0.31, 0.21)),
        "verde": ((0.14, 0.16, 0.13), (0.21, 0.24, 0.19), (0.28, 0.31, 0.25)),   # postigos pintados
        "almagra": ((0.22, 0.11, 0.08), (0.31, 0.16, 0.11), (0.39, 0.22, 0.15)),
    }[tono]
    estira = {"X": (0.5, 16.0, 16.0), "Y": (16.0, 0.5, 16.0), "Z": (16.0, 16.0, 0.5)}[eje]
    fibras = A.ruido(A.vmul(v, estira), 1.0, 10.0, 0.62, distorsion=0.4)
    anillos = A.onda(v, 2.4, "RINGS", eje, distorsion=2.2, detalle=2.0)
    base = A.rampa(fibras, [(0.3, srgb(colores[0])), (0.5, srgb(colores[1])), (0.72, srgb(colores[2]))])
    base = A.mezcla(A.rango(anillos, 0.7, 1.0, 0.0, 0.55), base, srgb(colores[0]))
    # Cada pieza un poco distinta.
    base = A.tono(base, 0.5, A.rango(isla, 0, 1, 0.8, 1.15), A.rango(isla, 0, 1, 0.82, 1.18))
    # Nudos.
    nudo = A.rango(A.voronoi(A.vmul(v, tuple(e / 8 for e in estira)), 1.6), 0.0, 0.06, 1.0, 0.0)
    base = A.mezcla(A.mate("MULTIPLY", nudo, 0.85), base, srgb((0.08, 0.05, 0.03)))
    # Gris de intemperie, a manchas.
    gris = A.rango(A.ruido(v, 1.3, 4, 0.6), 0.45, 0.72, 0.0, 0.5)
    base = A.mezcla(gris, base, srgb((0.34, 0.32, 0.29)))
    # Grietas finas a lo largo de la fibra.
    grieta = A.rango(A.ruido(A.vmul(v, tuple(e * 0.35 for e in estira)), 1.0, 3.0, 0.5), 0.6, 0.625)
    grieta = A.mate("MULTIPLY", grieta, A.rango(A.ruido(v, 2.0, 2), 0.5, 0.6))
    base = A.mezcla(A.mate("MULTIPLY", grieta, 0.9), base, srgb((0.03, 0.02, 0.015)))
    n1 = A.relieve(fibras, 0.35, 0.003)
    n2 = A.relieve(anillos, 0.12, 0.002, n1)
    n3 = A.relieve(A.mate("MULTIPLY", grieta, -1.0), 0.8, 0.004, n2)
    return A.superficie(base, A.rango(gris, 0, 0.5, 0.7, 0.9), n3, especular=0.3)


def teja():
    """Teja árabe cocida: cada pieza con su color, líquenes y suciedad en los canales."""
    A = Arbol("teja")
    isla = A.isla()
    v = A.coord()
    color = A.rampa(isla, [(0.0, srgb((0.32, 0.19, 0.13))), (0.3, srgb((0.40, 0.24, 0.16))),
                           (0.55, srgb((0.45, 0.30, 0.20))), (0.8, srgb((0.37, 0.25, 0.18))),
                           (1.0, srgb((0.50, 0.38, 0.27)))])
    color = A.mezcla(A.rango(A.ruido(v, 9, 5, 0.6), 0.35, 0.7, 0, 0.3), color, srgb((0.3, 0.2, 0.14)), "MULTIPLY")
    liquen = A.rango(A.ruido(A.vsum(v, A.combinar(isla, isla, 0)), 6.0, 6, 0.7), 0.6, 0.66)
    color = A.mezcla(A.mate("MULTIPLY", liquen, 0.85), color, srgb((0.55, 0.53, 0.40)))
    musgo = A.rango(A.ruido(v, 3.0, 5, 0.6), 0.62, 0.7)
    color = A.mezcla(A.mate("MULTIPLY", musgo, 0.6), color, srgb((0.22, 0.24, 0.13)))
    ao = A.oclusion(0.06)
    color = A.mezcla(A.rango(ao, 0.2, 1.0, 0.7, 0.0), color, srgb((0.12, 0.08, 0.06)), "MULTIPLY")
    n1 = A.relieve(A.ruido(v, 50, 5, 0.6), 0.2, 0.003)
    n2 = A.relieve(liquen, 0.3, 0.002, n1)
    return A.superficie(color, 0.82, n2, especular=0.3)


def canto():
    """Canto rodado del empedrado: cada piedra de su color (caliza, cuarcita, pedernal),
    gastada y con barro en la parte baja."""
    A = Arbol("canto")
    isla = A.isla()
    v = A.coord()
    color = A.rampa(isla, [(0.0, srgb((0.27, 0.26, 0.24))), (0.2, srgb((0.36, 0.34, 0.31))),
                           (0.4, srgb((0.33, 0.28, 0.22))), (0.6, srgb((0.42, 0.40, 0.37))),
                           (0.75, srgb((0.22, 0.22, 0.23))), (0.9, srgb((0.38, 0.32, 0.25))),
                           (1.0, srgb((0.48, 0.46, 0.43)))])
    color = A.mezcla(A.rango(A.ruido(v, 30, 4), 0.3, 0.7, 0, 0.3), color, srgb((0.3, 0.28, 0.25)), "MULTIPLY")
    x, y, z = A.separar(v)
    barro = A.rango(A.mate("ADD", z, A.mate("MULTIPLY", A.ruido(v, 1.5, 3), 0.02)), 0.022, 0.006)
    color = A.mezcla(barro, color, srgb((0.17, 0.14, 0.11)))
    sucio = A.rango(A.ruido(v, 0.35, 4, 0.6), 0.45, 0.7, 0.0, 0.6)
    color = A.mezcla(sucio, color, srgb((0.22, 0.19, 0.15)), "MULTIPLY")
    # Manchas grandes de barro y humedad: rompen la uniformidad de la calle.
    charco = A.rango(A.ruido(A.coord((1.0, 1.6, 1.0)), 0.22, 5, 0.6, distorsion=0.5), 0.5, 0.66)
    color = A.mezcla(A.mate("MULTIPLY", charco, 0.75), color, srgb((0.11, 0.095, 0.08)))
    n = A.relieve(A.ruido(v, 60, 4), 0.25, 0.002)
    rug = A.mate("MINIMUM", A.rango(barro, 0, 1, 0.45, 0.8), A.rango(charco, 0, 1, 0.8, 0.25))
    return A.superficie(color, rug, n, especular=0.45)


def tierra():
    """Tierra apisonada y barro entre las piedras."""
    A = Arbol("tierra")
    v = A.coord()
    color = A.rampa(A.ruido(v, 3, 6, 0.6), [(0.3, srgb((0.13, 0.11, 0.09))), (0.7, srgb((0.22, 0.18, 0.14)))])
    paja = A.rango(A.onda(A.coord((1.0, 3.0, 1.0)), 40, "BANDS", "X", 25, 2), 0.93, 1.0, 0.0, 0.5)
    color = A.mezcla(A.mate("MULTIPLY", paja, A.rango(A.ruido(v, 2, 2), 0.55, 0.65)), color,
                     srgb((0.42, 0.36, 0.22)))
    humedo = A.rango(A.ruido(v, 0.8, 3), 0.55, 0.62)
    n = A.relieve(A.ruido(v, 25, 6, 0.7), 0.4, 0.006)
    return A.superficie(color, A.rango(humedo, 0, 1, 0.9, 0.35), n, especular=0.3)


def agua():
    """Charcos: agua sucia y quieta que refleja el cielo."""
    A = Arbol("agua")
    v = A.coord()
    n = A.relieve(A.ruido(v, 8, 2), 0.04, 0.002)
    return A.superficie(srgb((0.03, 0.03, 0.03)), 0.04, n, especular=0.6)


def mortero():
    A = Arbol("mortero")
    v = A.coord()
    color = A.rampa(A.ruido(v, 6, 6, 0.6), [(0.3, srgb((0.45, 0.42, 0.37))), (0.7, srgb((0.62, 0.59, 0.52)))])
    n = A.relieve(A.ruido(v, 30, 6, 0.7), 0.5, 0.006)
    return A.superficie(color, 0.95, n, especular=0.2)


def losa():
    """Losas de caliza del soportal, pulidas por el paso en el centro."""
    A = Arbol("losa")
    isla = A.isla()
    v = A.vsum(A.coord(), A.combinar(A.mate("MULTIPLY", isla, 13.0), 0, 0))
    color = A.rampa(A.ruido(v, 2.0, 7, 0.6), [(0.3, srgb((0.34, 0.33, 0.30))), (0.7, srgb((0.47, 0.45, 0.41)))])
    color = A.tono(color, 0.5, 1.0, A.rango(isla, 0, 1, 0.8, 1.1))
    mugre = A.rango(A.ruido(v, 5, 4, 0.6), 0.45, 0.75, 0, 0.45)
    color = A.mezcla(mugre, color, srgb((0.26, 0.24, 0.21)), "MULTIPLY")
    ao = A.oclusion(0.05)
    color = A.mezcla(A.rango(ao, 0.2, 1.0, 0.8, 0.0), color, srgb((0.12, 0.11, 0.1)), "MULTIPLY")
    n1 = A.relieve(A.ruido(v, 30, 6, 0.65), 0.3, 0.003)
    n2 = A.relieve(A.voronoi(v, 25.0), 0.15, 0.004, n1)
    return A.superficie(color, A.rango(mugre, 0, 0.45, 0.55, 0.9), n2, especular=0.4)


def hierro():
    """Hierro de forja: negro, con óxido en los rincones."""
    A = Arbol("hierro")
    v = A.coord()
    oxido = A.rango(A.ruido(v, 12, 6, 0.65), 0.55, 0.7, 0.0, 0.8)
    color = A.mezcla(oxido, srgb((0.06, 0.055, 0.05)), srgb((0.22, 0.10, 0.05)))
    rug = A.rango(oxido, 0, 0.8, 0.45, 0.9)
    metal = A.rango(oxido, 0, 0.8, 0.75, 0.1)
    n = A.relieve(A.ruido(v, 80, 4, 0.6), 0.3, 0.002)
    return A.superficie(color, rug, n, metal=metal, especular=0.5)


def cera(color, rugosidad=0.45, sub=0.3):
    A = Arbol(f"cera_{color[0]:.2f}")
    v = A.coord()
    c = A.mezcla(A.rango(A.ruido(v, 40, 3), 0.3, 0.7, 0, 0.12), srgb(color), (0, 0, 0), "MULTIPLY")
    return A.superficie(c, rugosidad, A.relieve(A.ruido(v, 60, 3), 0.1, 0.001), subsuperficie=sub, especular=0.5)


def llama():
    A = Arbol("llama")
    em = A.nodo("ShaderNodeEmission", {"Color": srgb((1.0, 0.72, 0.38)), "Strength": 60.0})
    A.nt.links.new(em.outputs[0], A.salida.inputs["Surface"])
    return A.mat


def lienzo_imagen(ruta):
    """Material con una imagen (la pintura de la hornacina, hecha con PIL; ChatGPT la
    pintará de verdad)."""
    A = Arbol("lienzo_imagen")
    tc = A.nodo("ShaderNodeTexCoord")
    img = A.nodo("ShaderNodeTexImage", {"Vector": tc.outputs["UV"]})
    img.image = bpy.data.images.load(str(ruta))
    img.extension = "EXTEND"
    return A.superficie(img.outputs["Color"], 0.4, None, especular=0.5, brillo_capa=0.5)


def oro_viejo():
    A = Arbol("oro_viejo")
    v = A.coord()
    c = A.mezcla(A.rango(A.ruido(v, 30, 4), 0.4, 0.7, 0, 0.6), srgb((0.55, 0.40, 0.18)), srgb((0.18, 0.12, 0.06)))
    return A.superficie(c, 0.45, A.relieve(A.ruido(v, 90, 3), 0.2, 0.001), metal=0.8, especular=0.5)


def hollin():
    """Mancha de hollín sobre la cal (encima de la vela)."""
    A = Arbol("hollin")
    v = A.coord()
    c = A.rampa(A.ruido(v, 8, 5), [(0.3, srgb((0.06, 0.05, 0.05))), (0.7, srgb((0.14, 0.12, 0.11)))])
    return A.superficie(c, 0.95, A.relieve(A.ruido(v, 40, 3), 0.2, 0.002), especular=0.1)


def tela(color=(0.36, 0.29, 0.19)):
    """Arpillera de sacos y lonas."""
    A = Arbol(f"tela_{color[0]:.2f}")
    v = A.coord()
    x, y, z = A.separar(v)
    trama = A.mate("MULTIPLY", A.mate("SINE", A.mate("MULTIPLY", A.mate("ADD", x, y), 900)),
                   A.mate("SINE", A.mate("MULTIPLY", z, 900)))
    c = A.mezcla(A.rango(A.ruido(v, 6, 5), 0.3, 0.7, 0, 0.35), srgb(color), srgb((0.15, 0.12, 0.08)), "MULTIPLY")
    n = A.relieve(trama, 0.15, 0.001, A.relieve(A.ruido(v, 15, 4), 0.3, 0.005))
    return A.superficie(c, 0.95, n, especular=0.15)


def paja():
    A = Arbol("paja")
    v = A.coord()
    fibra = A.onda(v, 60, "BANDS", "X", 12, 3)
    c = A.rampa(fibra, [(0.0, srgb((0.30, 0.24, 0.12))), (1.0, srgb((0.62, 0.52, 0.30)))])
    return A.superficie(c, 0.9, A.relieve(fibra, 0.4, 0.002), especular=0.2)


def oscuro():
    """Fondo de un hueco sin luz: interior que no hace falta modelar."""
    A = Arbol("oscuro")
    return A.superficie(srgb((0.03, 0.025, 0.02)), 1.0, None, especular=0.0)


def resplandor(color=(1.0, 0.62, 0.30), fuerza=3.0):
    """Interior encendido visto a través de un hueco (pared que recibe la luz del candil)."""
    A = Arbol(f"resplandor_{fuerza:.1f}")
    v = A.coord()
    c = A.rampa(A.ruido(v, 2, 4), [(0.3, srgb((0.30, 0.20, 0.12))), (0.7, srgb((0.45, 0.32, 0.20)))])
    em = A.mezcla(A.rango(A.ruido(v, 1.2, 3), 0.3, 0.7, 0.6, 1.0), (0, 0, 0), srgb(color))
    return A.superficie(c, 0.95, None, emision=em, fuerza_emision=fuerza, especular=0.1)


def arcilla():
    """Material único de la maqueta de forma."""
    A = Arbol("arcilla")
    v = A.coord()
    ao = A.oclusion(0.15)
    c = A.mezcla(A.rango(ao, 0.0, 1.0, 0.5, 0.0), srgb((0.74, 0.72, 0.68)), srgb((0.2, 0.2, 0.2)), "MULTIPLY")
    return A.superficie(c, 0.9, A.relieve(A.ruido(v, 40, 3), 0.05, 0.002), especular=0.2)


FABRICAS = {
    "cal_blanco": lambda: cal("blanco"),
    "cal_ocre": lambda: cal("ocre"),
    "cal_almagra": lambda: cal("almagra"),
    "cal_hornacina": lambda: cal("hornacina"),
    "cal_interior": lambda: cal("interior"),
    "tapial": tapial,
    "piedra": lambda: piedra(0),
    "piedra_b": lambda: piedra(1),
    "madera_x": lambda: madera("X", "oscura"),
    "madera_y": lambda: madera("Y", "oscura"),
    "madera_z": lambda: madera("Z", "oscura"),
    "madera_media_x": lambda: madera("X", "media"),
    "madera_media_z": lambda: madera("Z", "media"),
    "madera_media_y": lambda: madera("Y", "media"),
    "postigo_verde": lambda: madera("Z", "verde"),
    "postigo_almagra": lambda: madera("Z", "almagra"),
    "teja": teja,
    "mortero": mortero,
    "canto": canto,
    "tierra": tierra,
    "agua": agua,
    "losa": losa,
    "hierro": hierro,
    "cera_blanca": lambda: cera((0.86, 0.83, 0.74)),
    "cera_negra": lambda: cera((0.015, 0.014, 0.013), 0.25, 0.0),
    "llama": llama,
    "oro_viejo": oro_viejo,
    "hollin": hollin,
    "tela": tela,
    "paja": paja,
    "oscuro": oscuro,
    "resplandor": resplandor,
    "resplandor_tenue": lambda: resplandor((1.0, 0.6, 0.28), 1.2),
    "arcilla": arcilla,
}


def obtener(nombre):
    if nombre not in _CACHE:
        if nombre.startswith("imagen:"):
            _CACHE[nombre] = lienzo_imagen(nombre[7:])
        else:
            _CACHE[nombre] = FABRICAS[nombre]()
    return _CACHE[nombre]


def vaciar():
    _CACHE.clear()
