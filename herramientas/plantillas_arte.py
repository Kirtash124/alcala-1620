#!/usr/bin/env python3
"""Genera las plantillas que se adjuntan a ChatGPT para que respete cámara y escala.

  docs/arte/plantilla_perspectiva.png   rejilla isométrica 2:1 con medidas y figura humana
  docs/arte/plantilla_personaje.png     poses de referencia: de frente y de espaldas

Uso:  python3 herramientas/plantillas_arte.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import arte_provisional as ap
from isometria import AX, ZH, ANCHO_FONDO, ALTO_FONDO, Proyeccion

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs/arte"


def fuente(tam):
    for ruta in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def perspectiva():
    W, H = ANCHO_FONDO, ALTO_FONDO
    img = Image.new("RGB", (W, H), (214, 212, 206))
    d = ImageDraw.Draw(img)
    pr = Proyeccion(1100, 760)
    p = pr.p

    # Rejilla del suelo: un metro por casilla, línea gruesa cada cinco.
    for i in range(-20, 30):
        tono, grosor = ((160, 158, 152), 2) if i % 5 == 0 else ((186, 184, 178), 1)
        d.line([p(i, -20), p(i, 30)], fill=tono, width=grosor)
        d.line([p(-20, i), p(30, i)], fill=tono, width=grosor)

    # Ejes, lejos de los objetos.
    o = (-4, 6)
    d.line([p(*o), p(o[0] + 3, o[1])], fill=(170, 60, 50), width=5)
    d.line([p(*o), p(o[0], o[1] + 3)], fill=(50, 110, 170), width=5)
    d.line([p(*o), p(o[0], o[1], 3)], fill=(60, 140, 70), width=5)

    # Bloque de 3 × 3 × 3 m.
    frontal = [p(0, 2, 0), p(3, 2, 0), p(3, 2, 3), p(0, 2, 3)]
    lateral = [p(3, -1, 0), p(3, 2, 0), p(3, 2, 3), p(3, -1, 3)]
    tapa = [p(0, -1, 3), p(3, -1, 3), p(3, 2, 3), p(0, 2, 3)]
    for cara, tono in zip([frontal, lateral, tapa], [(150, 148, 142), (118, 116, 112), (172, 170, 164)]):
        d.polygon(cara, fill=tono, outline=(80, 80, 80))
    # Muro de 3 m con una puerta de 1,20 × 2,20 m.
    d.polygon([p(6, -3, 0), p(11, -3, 0), p(11, -3, 3), p(6, -3, 3)], fill=(160, 158, 152), outline=(80, 80, 80))
    d.polygon([p(8, -3, 0), p(9.2, -3, 0), p(9.2, -3, 2.2), p(8, -3, 2.2)], fill=(96, 92, 86), outline=(60, 60, 60))

    # Figura humana de 1,70 m (con sombrero llega a unos 1,92 m).
    silueta = ap.pesquisidor(False)
    gris = Image.new("RGBA", silueta.size, (70, 70, 74, 255))
    gris.putalpha(silueta.split()[3])
    pie = p(6, 4)
    img.paste(gris, (int(pie[0] - 60), int(pie[1] - 191)), gris)

    f, fg, fp = fuente(30), fuente(44), fuente(24)
    d.text((60, 50), "PLANTILLA DE CÁMARA · Alcalá 1620", font=fg, fill=(40, 40, 40))
    lineas = [
        "Proyección isométrica 2:1 (cámara ortográfica, giro 45°, elevación 30°).",
        "Las líneas del suelo bajan 1 px por cada 2 px en horizontal.",
        f"1 m de suelo = {AX:.0f} px en horizontal · 1 m de altura = {ZH:.0f} px.",
        "Persona de 1,70 m ≈ 159 px (con sombrero, ≈ 180 px). Puerta de 2,20 m ≈ 206 px.",
        "Luz principal desde arriba a la izquierda.",
        "Lienzo de referencia: 2560 × 1440.",
    ]
    for i, l in enumerate(lineas):
        d.text((60, 120 + i * 42), l, font=f, fill=(55, 55, 55))
    d.text((p(o[0] + 3.2, o[1])[0] + 6, p(o[0] + 3.2, o[1])[1] - 6), "x", font=fp, fill=(170, 60, 50))
    d.text((p(o[0], o[1] + 3.2)[0] - 26, p(o[0], o[1] + 3.2)[1] - 6), "y", font=fp, fill=(50, 110, 170))
    d.text((p(*o, 3.1)[0] + 8, p(*o, 3.1)[1] - 14), "3 m de altura", font=fp, fill=(60, 140, 70))
    d.text((p(3, -1)[0] + 24, p(3, -1, 1.5)[1]), "bloque 3 × 3 × 3 m", font=fp, fill=(55, 55, 55))
    d.text((pie[0] + 50, pie[1] - 110), "persona 1,70 m", font=fp, fill=(55, 55, 55))
    d.text((p(11.2, -3, 2)[0] + 10, p(11.2, -3, 2)[1]), "muro 3 m · puerta 2,20 m", font=fp, fill=(55, 55, 55))
    img.save(SALIDA / "plantilla_perspectiva.png", optimize=True)


def personaje():
    W, H = 1024, 1536
    img = Image.new("RGB", (W, H), (214, 212, 206))
    d = ImageDraw.Draw(img)
    f, fg = fuente(30), fuente(40)
    d.text((50, 40), "POSES DE REFERENCIA · personajes", font=fg, fill=(40, 40, 40))
    d.multiline_text((50, 100), "Cuerpo entero, pies abajo, fondo liso.\nMisma cámara que los escenarios.", font=f, fill=(60, 60, 60), spacing=8)
    for i, (espaldas, rotulo) in enumerate([(False, "DE FRENTE\nmira abajo a la derecha"), (True, "DE ESPALDAS\nmira arriba a la derecha")]):
        fig = ap.pesquisidor(espaldas)
        alfa = fig.split()[3].resize((fig.width * 4, fig.height * 4), Image.LANCZOS)
        gris = Image.new("RGBA", alfa.size, (80, 80, 84, 255))
        gris.putalpha(alfa)
        x = 60 + i * 480
        img.paste(gris, (x, 380), gris)
        d.multiline_text((x + 40, 1220), rotulo, font=f, fill=(50, 50, 50), spacing=8)
    img.save(SALIDA / "plantilla_personaje.png", optimize=True)


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    perspectiva()
    personaje()
    print("Plantillas generadas en docs/arte/")
