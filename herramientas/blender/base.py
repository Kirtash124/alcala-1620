"""Utilidades para construir y renderizar piezas isométricas en Blender desde Python.

Se usa el módulo `bpy` (pip install bpy, Python 3.13), sin abrir Blender.

Coordenadas: todo el código de modelado trabaja en las coordenadas del juego
(metros; x hacia abajo a la derecha, y hacia abajo a la izquierda, z arriba; ver
isometria.py). Ese sistema es zurdo, así que al pasar a Blender se invierte la y:
B(x, y, z) = (x, -y, z). Con esa conversión, la cámara ortográfica de abajo
reproduce exactamente la proyección del juego.
"""
import math
import random
import warnings
from contextlib import contextmanager
from pathlib import Path

import bpy  # noqa: I001 (bpy debe ir antes que bmesh y mathutils)
import bmesh
import numpy as np
from mathutils import Matrix, Vector

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from isometria import AX, AY, ZH  # noqa: E402

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Cámara: acimut 45°, elevación 30°. K = píxeles por metro en el plano de la cámara.
K = AX / math.cos(math.radians(45))
_C, _S = math.cos(math.radians(30)), math.sin(math.radians(30))
HACIA_CAMARA = Vector((_C / math.sqrt(2), -_C / math.sqrt(2), _S))


def B(x, y, z=0.0) -> Vector:
    """Nuestras coordenadas → Blender."""
    return Vector((x, -y, z))


def pantalla(x, y, z=0.0):
    return ((x - y) * AX, (x + y) * AY - z * ZH)


def srgb(c):
    """Color sRGB (0..1) → lineal, que es lo que esperan los nodos."""
    def f(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c)


# ------------------------------------------------------------------ escena

def reiniciar(hilos=2):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.render.threads_mode = "FIXED"
    s.render.threads = hilos
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.02
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 6
    s.cycles.diffuse_bounces = 2
    s.cycles.glossy_bounces = 1
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.transmission_bounces = 2
    s.cycles.transparent_max_bounces = 4
    s.cycles.sample_clamp_indirect = 8.0
    s.cycles.light_sampling_threshold = 0.01
    s.render.film_transparent = True
    s.render.resolution_percentage = 100
    s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.render.image_settings.color_depth = "8"
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "None"
    s.render.filter_size = 1.2
    cam_datos = bpy.data.cameras.new("Camara")
    cam_datos.type = "ORTHO"
    cam_datos.clip_start, cam_datos.clip_end = 0.5, 400.0
    cam = bpy.data.objects.new("Camara", cam_datos)
    s.collection.objects.link(cam)
    s.camera = cam
    return s


def encuadrar(ancho, alto, ancla, escala=1.0, origen=(0.0, 0.0, 0.0)):
    """Coloca la cámara para que el punto `origen` (nuestras coordenadas) caiga en
    el píxel `ancla` de una imagen de ancho × alto, a `escala` veces la del juego."""
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = int(ancho), int(alto)
    a = (ancho / 2 - ancla[0]) / (AX * escala)       # x - y del punto central
    b = (alto / 2 - ancla[1]) / (AY * escala)        # x + y del punto central
    centro = B(origen[0] + (a + b) / 2, origen[1] + (b - a) / 2, origen[2])
    cam = s.camera
    cam.location = centro + HACIA_CAMARA * 120
    cam.rotation_euler = (-HACIA_CAMARA).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = max(ancho, alto) / (K * escala)
    cam.data.sensor_fit = "AUTO"


def renderizar(ruta, muestras=96):
    s = bpy.context.scene
    s.cycles.samples = muestras
    s.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)


def solo_visibles(objetos, recortan=(), ocultos=()):
    """Prepara la visibilidad para renderizar una pieza.

    - `objetos`: lo que sale en la imagen.
    - `recortan`: objetos que tapan a la pieza donde están delante (holdout): la imagen
      queda transparente ahí, así que la pieza solo contiene lo que de verdad se ve.
    - el resto (`ocultos` y lo no nombrado) no sale en la imagen.
    Todos siguen haciendo sombra y rebotando luz."""
    ids = {o.name for o in objetos}
    recorte = {o.name for o in recortan}
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.visible_camera = o.name in ids or o.name in recorte
            o.is_holdout = o.name in recorte


def vertices(obj) -> np.ndarray:
    """Vértices del objeto en nuestras coordenadas (n × 3)."""
    me = obj.data
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    M = np.array(obj.matrix_world)
    a = a @ M[:3, :3].T + M[:3, 3]
    a[:, 1] *= -1
    return a


# ------------------------------------------------------------------ luces

def luna(direccion, fuerza, color, angulo=0.6):
    """Sol frío. `direccion`: vector hacia la luna en nuestras coordenadas."""
    d = B(*direccion).normalized()
    datos = bpy.data.lights.new("Luna", "SUN")
    datos.energy = fuerza
    datos.color = color
    datos.angle = math.radians(angulo)
    ob = bpy.data.objects.new("Luna", datos)
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob


def cielo(color, fuerza):
    mundo = bpy.data.worlds.new("Noche")
    bpy.context.scene.world = mundo
    nt = mundo.node_tree
    fondo = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    fondo.inputs["Color"].default_value = (*color, 1.0)
    fondo.inputs["Strength"].default_value = fuerza
    return mundo


def punto_luz(nombre, posicion, potencia, color, radio=0.02):
    datos = bpy.data.lights.new(nombre, "POINT")
    datos.energy = potencia
    datos.color = color
    datos.shadow_soft_size = radio
    ob = bpy.data.objects.new(nombre, datos)
    ob.location = B(*posicion)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def area_luz(nombre, posicion, potencia, color, tamano=(1.0, 1.0), mirando=(0, 1, 0)):
    """Luz de área en `posicion`, emitiendo hacia `mirando` (nuestras coordenadas)."""
    datos = bpy.data.lights.new(nombre, "AREA")
    datos.energy = potencia
    datos.color = color
    datos.shape = "RECTANGLE"
    datos.size, datos.size_y = tamano
    ob = bpy.data.objects.new(nombre, datos)
    ob.location = B(*posicion)
    ob.rotation_euler = B(*mirando).normalized().to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ geometría

def giro_z(angulo_grados, centro):
    """Giro alrededor de un eje vertical que pasa por `centro` (nuestras coordenadas).
    Ángulo positivo: de +x hacia +y en nuestro sistema."""
    c = B(*centro)
    return Matrix.Translation(c) @ Matrix.Rotation(-math.radians(angulo_grados), 4, "Z") @ Matrix.Translation(-c)


def giro_x(angulo_grados, centro):
    """Giro alrededor de un eje paralelo a x. Positivo: de +y hacia +z."""
    c = B(*centro)
    return Matrix.Translation(c) @ Matrix.Rotation(-math.radians(angulo_grados), 4, "X") @ Matrix.Translation(-c)


def giro_y(angulo_grados, centro):
    """Giro alrededor de un eje paralelo a y. Positivo: de +z hacia +x."""
    c = B(*centro)
    return Matrix.Translation(c) @ Matrix.Rotation(-math.radians(angulo_grados), 4, "Y") @ Matrix.Translation(-c)


class Malla:
    """Acumula geometría en un bmesh con un material por cara. Cada pieza suelta
    (una teja, una tabla, un clavo) es una isla, y los materiales usan
    «Random Per Island» para que ninguna sea igual a otra."""

    def __init__(self, nombre, semilla=0):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.materiales = []
        self.rng = random.Random(semilla)
        self.pila = [Matrix.Identity(4)]
        self.siluetas = {}           # etiqueta -> lista de nubes de puntos convexas (nuestras coords)

    # --- utilidades internas
    @property
    def M(self):
        return self.pila[-1]

    @contextmanager
    def transformada(self, matriz):
        self.pila.append(self.M @ matriz)
        try:
            yield
        finally:
            self.pila.pop()

    def _indice(self, mat):
        if mat not in self.materiales:
            self.materiales.append(mat)
        return self.materiales.index(mat)

    def _asignar(self, caras, mat, liso=False):
        i = self._indice(mat)
        for f in caras:
            f.material_index = i
            f.smooth = liso

    def _v(self, p):
        return self.bm.verts.new(self.M @ B(*p))

    def _silueta(self, etiqueta, verts_bl):
        if etiqueta:
            pts = np.array([[v.co.x, -v.co.y, v.co.z] if hasattr(v, 'co') else [v.x, -v.y, v.z] for v in verts_bl])
            self.siluetas.setdefault(etiqueta, []).append(pts)

    def azar(self, a, b):
        return self.rng.uniform(a, b)

    # --- primitivas
    def poligono(self, puntos, mat, liso=False, uvs=None):
        vs = [self._v(p) for p in puntos]
        f = self.bm.faces.new(vs)
        self._asignar([f], mat, liso)
        if uvs:
            capa = self.bm.loops.layers.uv.verify()
            for bucle, uv in zip(f.loops, uvs):
                bucle[capa].uv = uv
        return f

    def caja(self, x0, y0, z0, x1, y1, z1, mat, bisel=0.0, segmentos=1, desorden=0.0, giro=None,
             etiqueta=None):
        """Caja entre dos esquinas (nuestras coordenadas), con aristas biseladas.
        `desorden` mueve cada esquina al azar (piedra labrada a mano). `giro`: matriz
        de Blender aplicada alrededor del centro de la caja."""
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = r["verts"]
        c = B((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        tam = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        G = giro if giro is not None else Matrix.Identity(4)
        T = self.M @ Matrix.Translation(c) @ G @ Matrix.Diagonal((*tam, 1.0))
        for v in vs:
            v.co = T @ v.co
            if desorden:
                v.co += Vector((self.azar(-desorden, desorden) for _ in range(3)))
        self._silueta(etiqueta, vs)
        caras = list({f for v in vs for f in v.link_faces})
        self._asignar(caras, mat)
        if bisel > 0:
            aristas = list({e for v in vs for e in v.link_edges})
            res = bmesh.ops.bevel(self.bm, geom=vs + aristas, offset=min(bisel, 0.45 * min(tam)),
                                  offset_type="OFFSET", segments=segmentos, profile=0.5, affect="EDGES",
                                  clamp_overlap=True)
            self._asignar(res["faces"], mat)

    def solido(self, puntos, caras, mat, liso=False, etiqueta=None):
        """Sólido cerrado a partir de vértices (nuestras coords) e índices de caras."""
        vs = [self._v(p) for p in puntos]
        nuevas = []
        for c in caras:
            try:
                nuevas.append(self.bm.faces.new([vs[i] for i in c]))
            except ValueError:
                pass
        bmesh.ops.recalc_face_normals(self.bm, faces=nuevas)
        self._asignar(nuevas, mat, liso)
        self._silueta(etiqueta, vs)
        return vs

    def prisma(self, perfil, plano, a0, a1, mat, bisel=0.0, liso=False, etiqueta=None):
        """Extruye un perfil 2D. plano 'xz': puntos (x, z) extruidos en y de a0 a a1;
        'yz': (y, z) extruidos en x; 'xy': (x, y) extruidos en z."""
        def p3(u, v, a):
            if plano == "xz":
                return (u, a, v)
            if plano == "yz":
                return (a, u, v)
            return (u, v, a)
        n = len(perfil)
        pts = [p3(u, v, a0) for u, v in perfil] + [p3(u, v, a1) for u, v in perfil]
        caras = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
        caras += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        vs = self.solido(pts, caras, mat, liso, etiqueta)
        if bisel > 0:
            aristas = list({e for v in vs for e in v.link_edges})
            res = bmesh.ops.bevel(self.bm, geom=vs + aristas, offset=bisel, offset_type="OFFSET",
                                  segments=1, profile=0.5, affect="EDGES", clamp_overlap=True)
            self._asignar(res["faces"], mat, liso)

    def torno(self, perfil, centro, mat, lados=24, eje="z", liso=True, tapas=True, etiqueta=None,
              ruido=0.0, angulo=(0.0, 2 * math.pi)):
        """Sólido de revolución. perfil: lista de (radio, altura) de abajo arriba,
        medida a lo largo del eje desde `centro`. eje: 'x', 'y' o 'z' (nuestros)."""
        c = B(*centro)
        if eje == "z":
            u, v, w = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
        elif eje == "x":
            u, v, w = Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
        else:
            u, v, w = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))
        completo = abs(angulo[1] - angulo[0] - 2 * math.pi) < 1e-6
        pasos = lados if completo else lados + 1
        anillos = []
        fase = self.azar(0, 10)
        for k, (r, h) in enumerate(perfil):
            anillo = []
            for i in range(pasos):
                t = angulo[0] + (angulo[1] - angulo[0]) * i / lados
                rr = r * (1 + (ruido * math.sin(3 * t + fase + 1.7 * h) * math.cos(2 * t - 1.1 * h) if ruido else 0))
                anillo.append(self.bm.verts.new(self.M @ (c + u * (rr * math.cos(t)) + v * (rr * math.sin(t)) + w * h)))
            anillos.append(anillo)
        caras = []
        for a, b in zip(anillos, anillos[1:]):
            for i in range(lados if completo else lados):
                j = (i + 1) % pasos if completo else i + 1
                try:
                    caras.append(self.bm.faces.new([a[i], a[j], b[j], b[i]]))
                except ValueError:
                    pass
        self._asignar(caras, mat, liso)
        tapas_f = []
        if tapas and completo:
            for anillo, r in ((anillos[0], perfil[0][0]), (anillos[-1], perfil[-1][0])):
                if r > 1e-4:
                    tapas_f.append(self.bm.faces.new(anillo))
            self._asignar(tapas_f, mat, False)
        todas = caras + tapas_f
        if todas:
            bmesh.ops.recalc_face_normals(self.bm, faces=todas)
        for a, b in zip(anillos, anillos[1:]):
            self._silueta(etiqueta, a + b)
        return anillos

    def barra(self, p0, p1, ancho, alto=None, mat="hierro", bisel=0.0, arriba=(0, 0, 1)):
        """Prisma rectangular de p0 a p1 (nuestras coords)."""
        alto = alto or ancho
        a, b = self.M @ B(*p0), self.M @ B(*p1)
        eje = b - a
        largo = eje.length
        if largo < 1e-6:
            return
        w = eje.normalized()
        ref = (self.M.to_3x3() @ B(*arriba)).normalized()
        if abs(w.dot(ref)) > 0.95:
            ref = Vector((1, 0, 0)) if abs(w.x) < 0.9 else Vector((0, 1, 0))
        u = ref.cross(w).normalized()
        v = w.cross(u).normalized()
        R = Matrix((u, v, w)).transposed().to_4x4()
        T = Matrix.Translation((a + b) / 2) @ R @ Matrix.Diagonal((ancho, alto, largo, 1.0))
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for vtx in r["verts"]:
            vtx.co = T @ vtx.co
        caras = list({f for vtx in r["verts"] for f in vtx.link_faces})
        self._asignar(caras, mat)
        if bisel > 0:
            aristas = list({e for vtx in r["verts"] for e in vtx.link_edges})
            res = bmesh.ops.bevel(self.bm, geom=r["verts"] + aristas, offset=min(bisel, 0.45 * min(ancho, alto)),
                                  offset_type="OFFSET", segments=1, profile=0.5, affect="EDGES",
                                  clamp_overlap=True)
            self._asignar(res["faces"], mat)

    def tubo(self, puntos, radio, mat, lados=8, cerrado=False, liso=True, radios=None):
        """Barra de sección circular a lo largo de una polilínea (forja, aros, cuerdas)."""
        P = [self.M @ B(*p) for p in puntos]
        n = len(P)
        if n < 2:
            return
        tang = []
        for i in range(n):
            if cerrado:
                t = P[(i + 1) % n] - P[i - 1]
            else:
                t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
            tang.append(t.normalized())
        ref = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
        u = ref.cross(tang[0]).normalized()
        anillos = []
        for i in range(n):
            if i > 0:                        # transporte paralelo del marco
                u = (u - tang[i] * u.dot(tang[i])).normalized()
            v = tang[i].cross(u)
            r = radios[i] if radios else radio
            anillos.append([self.bm.verts.new(P[i] + (u * math.cos(2 * math.pi * k / lados) +
                                                      v * math.sin(2 * math.pi * k / lados)) * r)
                            for k in range(lados)])
        caras = []
        pares = list(zip(anillos, anillos[1:]))
        if cerrado:
            pares.append((anillos[-1], anillos[0]))
        for a, b in pares:
            for k in range(lados):
                caras.append(self.bm.faces.new([a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]]))
        self._asignar(caras, mat, liso)
        if not cerrado:
            tapas = [self.bm.faces.new(anillos[0]), self.bm.faces.new(anillos[-1])]
            self._asignar(tapas, mat)
            caras += tapas
        bmesh.ops.recalc_face_normals(self.bm, faces=caras)

    def esfera(self, centro, radios, mat, segmentos=10, anillos=6, desorden=0.0, liso=True):
        r = bmesh.ops.create_uvsphere(self.bm, u_segments=segmentos, v_segments=anillos, radius=1.0)
        c = B(*centro)
        T = self.M @ Matrix.Translation(c) @ Matrix.Diagonal((radios[0], radios[1], radios[2], 1.0))
        for v in r["verts"]:
            v.co = T @ v.co
            if desorden:
                v.co += Vector((self.azar(-desorden, desorden) for _ in range(3)))
        caras = list({f for v in r["verts"] for f in v.link_faces})
        self._asignar(caras, mat, liso)

    # --- salida
    def objeto(self, materiales, pieza=None, coleccion=None):
        """Crea el objeto. `materiales`: función nombre → bpy.types.Material."""
        me = bpy.data.meshes.new(self.nombre)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.materiales:
            me.materials.append(materiales(m))
        ob = bpy.data.objects.new(self.nombre, me)
        (coleccion or bpy.context.scene.collection).objects.link(ob)
        if pieza:
            ob["pieza"] = pieza
        return ob


def nube(nombre, centros, radios, angulos, material, desorden=0.0, segmentos=7, anillos=4, semilla=0):
    """Muchas piedras pequeñas (empedrado) de golpe, con numpy: miles de llamadas a
    bmesh serían lentísimas. centros, radios: n × 3 (nuestras coords); angulos: giro
    alrededor de z en grados. Cada piedra es una isla (su propio color)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segmentos, v_segments=anillos, radius=1.0)
    plantilla = np.array([v.co[:] for v in bm.verts])
    caras = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    n, k = len(centros), len(plantilla)
    rng = np.random.default_rng(semilla)
    c = np.asarray(centros, float).copy()
    c[:, 1] *= -1                                         # a Blender
    r = np.asarray(radios, float)
    a = -np.radians(np.asarray(angulos, float))
    cos, sin = np.cos(a), np.sin(a)
    v = plantilla[None, :, :] * r[:, None, :]
    x = v[:, :, 0] * cos[:, None] - v[:, :, 1] * sin[:, None]
    y = v[:, :, 0] * sin[:, None] + v[:, :, 1] * cos[:, None]
    v = np.stack([x, y, v[:, :, 2]], 2) + c[:, None, :]
    if desorden:
        v += rng.uniform(-desorden, desorden, v.shape)
    v = v.reshape(-1, 3)
    todas = [[i * k + j for j in cara] for i in range(n) for cara in caras]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(v.tolist(), [], todas)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material)
    me.update()
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob
