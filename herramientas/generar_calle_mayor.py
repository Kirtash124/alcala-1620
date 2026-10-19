#!/usr/bin/env python3
"""Monta escenas/lugares/CalleMayor.tscn a partir de herramientas/datos/calle_mayor.json
(lo escribe kit_calle_mayor.py) y de las fichas de cada pieza.

La escena se compone del suelo, las piezas (casas, carro, barriles, cadáver) con sus
huellas y recortes, el alguacil, la luz de la vela, los puntos de interés y dos
marcadores que usa la prueba de humo.
"""
import json
from pathlib import Path

from isometria import AX, AY

RAIZ = Path(__file__).resolve().parent.parent
datos = json.loads((RAIZ / "herramientas/datos/calle_mayor.json").read_text(encoding="utf-8"))


def v2(pt):
    return f"Vector2({pt[0]:.1f}, {pt[1]:.1f})"


def poly(pts):
    return "PackedVector2Array(" + ", ".join(f"{a:.1f}, {b:.1f}" for a, b in pts) + ")"


def enteros(vals):
    return "PackedInt32Array(" + ", ".join(str(int(v)) for v in vals) + ")"


def reales(vals):
    return "PackedFloat32Array(" + ", ".join(f"{v:.1f}" for v in vals) + ")"


def color(c):
    return "Color(" + ", ".join(f"{v:.3f}" for v in c) + ", 1)"


ext = []


def recurso(tipo, ruta):
    for i, (t, r) in enumerate(ext, 1):
        if r == ruta:
            return f'ExtResource("{i}")'
    ext.append((tipo, ruta))
    return f'ExtResource("{len(ext)}")'


N = []


def nodo(nombre, tipo, padre=None, **props):
    cab = f'[node name="{nombre}" type="{tipo}"' + (f' parent="{padre}"' if padre is not None else '') + ']'
    N.append(cab)
    for k, v in props.items():
        N.append(f'{k} = {v}')
    N.append('')


nodo("CalleMayor", "Node2D", script=recurso("Script", "res://codigo/Juego/Lugar.cs"), Id='"calle_mayor"',
     Titulo='"Calle Mayor, junto a los soportales"', TonoPersonajes=color(datos["tono_personajes"]))
nodo("Fondo", "Sprite2D", ".", texture=recurso("Texture2D", datos["suelo"]), centered="false", z_index="-10")
nodo("Transitable", "Polygon2D", ".", color="Color(0.2, 1, 0.4, 0.3)", polygon=poly(datos["transitable"]))
nodo("Obstaculos", "Node2D", ".")
for i, h in enumerate(datos["obstaculos"], 1):
    nodo(f"Obstaculo{i}", "Polygon2D", "Obstaculos", color="Color(1, 0.2, 0.2, 0.35)", polygon=poly(h))
nodo("Inicio", "Marker2D", ".", position=v2(datos["inicio"]))

nodo("Entidades", "Node2D", ".", y_sort_enabled="true")
for p in datos["piezas"]:
    f = datos["fichas"][p["id"]]
    huellas = [[((x - y) * AX, (x + y) * AY) for x, y in h] for h in f["huella"]]
    recortes = f["recortes"]
    nodo(p["nodo"], "Node2D", "Entidades", script=recurso("Script", "res://codigo/Juego/Pieza.cs"),
         position=v2(p["posicion"]), Imagen=recurso("Texture2D", f["imagen"]), Ancla=v2(f["ancla"]),
         Fondo="true" if f["fondo"] else "false",
         HuellaPuntos=poly([q for h in huellas for q in h]), HuellaTamanos=enteros(len(h) for h in huellas),
         RecortesPuntos=poly([q for r in recortes for q in r["poligono"]]),
         RecortesTamanos=enteros(len(r["poligono"]) for r in recortes),
         RecortesBases=reales(r["base"] for r in recortes))

alg = datos["alguacil"]
textura_alg = recurso("Texture2D", "res://arte/personajes/alguacil_se.png")
nodo("Alguacil", "Node2D", "Entidades", position=v2(alg), script=recurso("Script", "res://codigo/Juego/Personaje.cs"),
     Frente=textura_alg, MiraIzquierda="true")
nodo("Sombra", "Sprite2D", "Entidades/Alguacil", texture=recurso("Texture2D", "res://arte/objetos/sombra.png"),
     position="Vector2(0, -2)")
nodo("Cuerpo", "Sprite2D", "Entidades/Alguacil", texture=textura_alg, centered="false", offset="Vector2(-58, -191)")
# Posición del cristal del farol en el dibujo del alguacil (está en espejo: queda a la izquierda).
parpadeo = recurso("Script", "res://codigo/Juego/Parpadeo.cs")
nodo("Farol", "PointLight2D", "Entidades/Alguacil", position="Vector2(-24.0, -66.0)", script=parpadeo,
     color="Color(1, 0.72, 0.4, 1)", texture_scale="2.6", EnergiaBase="0.9", Temblor="0.22")

# La luz de las velas ya va pintada en las piezas; estas solo añaden el temblor.
nodo("Luces", "Node2D", ".")
for luz in datos["luces"]:
    nodo(luz["nombre"], "PointLight2D", "Luces", position=v2(luz["posicion"]), script=parpadeo,
         color="Color(1, 0.7, 0.4, 1)", texture_scale="1.1", EnergiaBase="0.45", Temblor="0.45", Rapidez="1.4")

nodo("Puntos", "Node2D", ".")
nombres = {
    "alguacil": ("Alguacil", "Alguacil", "alguacil"),
    "cadaver": ("Cadaver", "El muerto", "cadaver"),
    "hornacina": ("Hornacina", "Hornacina", "hornacina"),
    "salida": ("Salida", "Hacia la plaza del Mercado", "salida"),
}
punto = recurso("Script", "res://codigo/Juego/PuntoDeInteres.cs")
for clave, (nodo_nombre, rotulo, nudo) in nombres.items():
    pt = datos["puntos"][clave]
    nodo(nodo_nombre, "Node2D", "Puntos", script=punto, Nombre=f'"{rotulo}"', Nudo=f'"{nudo}"')
    nodo("Zona", "Polygon2D", f"Puntos/{nodo_nombre}", color="Color(1, 0.85, 0.2, 0.3)", polygon=poly(pt["zona"]))
    nodo("Llegada", "Marker2D", f"Puntos/{nodo_nombre}", position=v2(pt["llegada"]))

nodo("Pruebas", "Node2D", ".")
for nombre, pos in datos["pruebas"].items():
    nodo(nombre, "Marker2D", "Pruebas", position=v2(pos))

cabecera = [f'[gd_scene load_steps={len(ext) + 1} format=3]', '']
for i, (tipo, ruta) in enumerate(ext, 1):
    cabecera.append(f'[ext_resource type="{tipo}" path="{ruta}" id="{i}"]')
cabecera.append('')
destino = RAIZ / "escenas/lugares/CalleMayor.tscn"
destino.write_text("\n".join(cabecera + N), encoding="utf-8")
print(f"Escena escrita en {destino.relative_to(RAIZ)} ({len(datos['piezas'])} piezas)")
