"""Proyección isométrica común a todas las herramientas de arte.

Convención del juego (no cambiar sin rehacer el arte):
  - Proyección ortográfica dimétrica 2:1: azimut 45°, elevación 30°.
  - Eje x del mundo: hacia abajo y a la derecha en pantalla.
  - Eje y del mundo: hacia abajo y a la izquierda en pantalla.
  - Eje z: altura.
  - 1 metro en el suelo avanza 76,4 px en horizontal y 38,2 px en vertical.
  - 1 metro de altura son 93,5 px. Una persona de 1,70 m mide unos 159 px.
  - Luz principal: de arriba a la izquierda.
"""

AX = 76.4   # px horizontales por metro de suelo
AY = 38.2   # px verticales por metro de suelo (la mitad: proporción 2:1)
ZH = 93.5   # px por metro de altura

ANCHO_FONDO = 2560
ALTO_FONDO = 1440


class Proyeccion:
    """Convierte coordenadas del mundo (metros) a píxeles de un fondo concreto."""

    def __init__(self, ox: float, oy: float):
        self.ox = ox
        self.oy = oy

    def p(self, x: float, y: float, z: float = 0.0) -> tuple[float, float]:
        return (self.ox + (x - y) * AX, self.oy + (x + y) * AY - z * ZH)

    def poligono(self, puntos) -> list[tuple[float, float]]:
        return [self.p(*pt) for pt in puntos]
