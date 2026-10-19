#!/usr/bin/env python3
"""Monta escenas/lugares/CalleMayor.tscn a partir de herramientas/datos/calle_mayor.json.

Solo para el escenario provisional. Con arte definitivo, los polígonos se dibujan
a mano en el editor de Godot (ver docs/MONTAR_UN_LUGAR.md) y este script deja de usarse.
"""
import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
datos = json.loads((RAIZ / "herramientas/datos/calle_mayor.json").read_text(encoding="utf-8"))

# Qué fondo usa la escena: la maqueta con texturas (por defecto) o el dibujo provisional.
FONDOS = {
    "texturas": "res://arte/fondos/calle_mayor_texturas.png",
    "provisional": "res://arte/fondos/calle_mayor.png",
}
opciones = argparse.ArgumentParser(description=__doc__)
opciones.add_argument("--fondo", choices=FONDOS, default="texturas")
datos["fondo"] = FONDOS[opciones.parse_args().fondo]


def v2(pt):
    return f"Vector2({pt[0]:.1f}, {pt[1]:.1f})"


def poly(pts):
    return "PackedVector2Array(" + ", ".join(f"{a:.1f}, {b:.1f}" for a, b in pts) + ")"


ext = [
    ('Script', 'res://codigo/Juego/Lugar.cs'),            # 1
    ('Texture2D', datos["fondo"]),                         # 2
    ('Script', 'res://codigo/Juego/Oclusor.cs'),          # 3
    ('Script', 'res://codigo/Juego/PuntoDeInteres.cs'),   # 4
    ('Script', 'res://codigo/Juego/Personaje.cs'),        # 5
    ('Texture2D', 'res://arte/personajes/alguacil_se.png'),  # 6
    ('Texture2D', 'res://arte/objetos/sombra.png'),       # 7
    ('Texture2D', 'res://arte/objetos/cadaver.png'),      # 8
    ('Script', 'res://codigo/Juego/Parpadeo.cs'),         # 9
]
out = [f'[gd_scene load_steps={len(ext) + 1} format=3]', '']
for i, (tipo, ruta) in enumerate(ext, 1):
    out.append(f'[ext_resource type="{tipo}" path="{ruta}" id="{i}"]')
out.append('')

N = []


def nodo(nombre, tipo, padre=None, **props):
    cab = f'[node name="{nombre}" type="{tipo}"' + (f' parent="{padre}"' if padre is not None else '') + ']'
    N.append(cab)
    for k, v in props.items():
        N.append(f'{k} = {v}')
    N.append('')


nodo("CalleMayor", "Node2D", script='ExtResource("1")', Id='"calle_mayor"',
     Titulo='"Calle Mayor, junto a los soportales"')
nodo("Fondo", "Sprite2D", ".", texture='ExtResource("2")', centered="false")
nodo("Ambiente", "CanvasModulate", ".", color="Color(0.42, 0.45, 0.62, 1)")
nodo("Transitable", "Polygon2D", ".", color="Color(0.2, 1, 0.4, 0.3)",
     polygon=poly(datos["transitable"]["exterior"]))
nodo("Obstaculos", "Node2D", ".")
for i, h in enumerate(datos["transitable"]["huecos"], 1):
    nodo(f"Obstaculo{i}", "Polygon2D", "Obstaculos", color="Color(1, 0.2, 0.2, 0.35)", polygon=poly(h))
nodo("Inicio", "Marker2D", ".", position=v2(datos["jugador_inicio"]))

nodo("Entidades", "Node2D", ".", y_sort_enabled="true")
for o in datos["oclusores"]:
    nodo(o["nombre"], "Polygon2D", "Entidades", script='ExtResource("3")', texture='ExtResource("2")',
         polygon=poly(o["poligono"]), LineaBase=f'{float(o["linea_base"]):.1f}')

cad = datos["cadaver"]["centro"]
nodo("Cadaver", "Node2D", "Entidades", position=v2(cad))
nodo("Cuerpo", "Sprite2D", "Entidades/Cadaver", texture='ExtResource("8")', position="Vector2(0, -4)")

alg = datos["alguacil"]
nodo("Alguacil", "Node2D", "Entidades", position=v2(alg["pies"]), script='ExtResource("5")',
     Frente='ExtResource("6")', MiraIzquierda="true")
nodo("Sombra", "Sprite2D", "Entidades/Alguacil", texture='ExtResource("7")', position="Vector2(0, -2)")
nodo("Cuerpo", "Sprite2D", "Entidades/Alguacil", texture='ExtResource("6")', centered="false",
     offset="Vector2(-58, -191)")
# Posición del cristal del farol en el dibujo del alguacil (está en espejo: queda a la izquierda).
farol = [-24.0, -66.0]
nodo("Farol", "PointLight2D", "Entidades/Alguacil", position=v2(farol), script='ExtResource("9")',
     color="Color(1, 0.72, 0.4, 1)", texture_scale="2.6", EnergiaBase="1.25", Temblor="0.22")

nodo("Luces", "Node2D", ".")
nodo("VelaHornacina", "PointLight2D", "Luces", position=v2(datos["hornacina"]["llama"]), script='ExtResource("9")',
     color="Color(1, 0.78, 0.45, 1)", texture_scale="1.7", EnergiaBase="1.1", Temblor="0.3", Rapidez="1.4")

nodo("Puntos", "Node2D", ".")
nombres = {
    "alguacil": ("Alguacil", "Alguacil", "alguacil"),
    "cadaver": ("Cadaver", "El muerto", "cadaver"),
    "hornacina": ("Hornacina", "Hornacina", "hornacina"),
    "salida": ("Salida", "Hacia la plaza del Mercado", "salida"),
}
for clave, (nodo_nombre, rotulo, nudo) in nombres.items():
    pt = datos["puntos"][clave]
    nodo(nodo_nombre, "Node2D", "Puntos", script='ExtResource("4")', Nombre=f'"{rotulo}"', Nudo=f'"{nudo}"')
    nodo("Zona", "Polygon2D", f"Puntos/{nodo_nombre}", color="Color(1, 0.85, 0.2, 0.3)", polygon=poly(pt["zona"]))
    nodo("Llegada", "Marker2D", f"Puntos/{nodo_nombre}", position=v2(pt["llegada"]))

destino = RAIZ / "escenas/lugares/CalleMayor.tscn"
destino.write_text("\n".join(out + N), encoding="utf-8")
print(f"Escena escrita en {destino.relative_to(RAIZ)}")
