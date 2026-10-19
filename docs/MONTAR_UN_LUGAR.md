# Montar un escenario nuevo en Godot

Un escenario se compone de un **suelo** y de **piezas** (casas, objetos) que se modelan
y renderizan por código en Blender. La calle Mayor (`escenas/lugares/CalleMayor.tscn`)
sirve de ejemplo de todo lo que sigue.

## Estructura de la escena

```
NombreDelLugar (Node2D, script Lugar.cs)   Id, Titulo, TonoPersonajes
├─ Fondo (Sprite2D)            el suelo; «Centered» desactivado; en el origen; marca los límites
├─ Transitable (Polygon2D)     contorno del suelo por el que se camina
├─ Obstaculos (Node2D)
│   └─ ... (Polygon2D)         huecos que no son de ninguna pieza (el sitio del alguacil)
├─ Inicio (Marker2D)           dónde aparece el pesquisidor
├─ Entidades (Node2D)          «Y Sort Enabled» activado
│   ├─ piezas (Node2D, script Pieza.cs)      imagen, ancla, huella y recortes
│   ├─ oclusores (Polygon2D, script Oclusor.cs), si se recorta algo a mano
│   └─ personajes
├─ Luces (Node2D)
│   └─ ... (PointLight2D, script Parpadeo.cs)   solo el temblor: la luz ya va pintada
├─ Puntos (Node2D)
│   └─ Nombre (Node2D, script PuntoDeInteres.cs)   Nombre, Nudo
│       ├─ Zona (Polygon2D)    donde se hace clic
│       └─ Llegada (Marker2D)  adonde camina el pesquisidor
└─ Pruebas (Node2D)            marcadores que usa la prueba de humo
```

## Piezas

Cada `Pieza` se coloca en su punto de origen en el suelo y trae:

- **Imagen** y **Ancla** (el píxel de la imagen que cae en ese punto).
- **Fondo**: activado en las casas. Su imagen se dibuja siempre detrás de los personajes
  y solo tapan sus **recortes** (las columnas), cada uno con su línea base.
- Desactivado en los objetos sueltos: la pieza entera se dibuja en tiras verticales,
  cada una con su línea base, para poder pasar por delante de una punta del carro y por
  detrás de la otra.
- **Huella**: lo que ocupa en el suelo; se convierte en obstáculo al cargar el lugar.
- **Sombra** y **SombraAncla**: la sombra que la pieza echa en el suelo, renderizada en
  Blender con un atrapasombras (`kit_calle_mayor.py --sombras`). Se dibuja encima del
  suelo y debajo de todo lo demás, así que el suelo (pintado o no) no tiene que traer
  las sombras del carro o de los barriles, y si se quita una pieza su sombra se va con ella.

Todo eso lo escribe `herramientas/generar_calle_mayor.py` a partir de las fichas de
`herramientas/datos/piezas/` (las genera `herramientas/kit_calle_mayor.py`). No se dibuja
a mano.

## Pasos para un lugar nuevo

1. **Kit**: copia `herramientas/kit_calle_mayor.py` y define las piezas del lugar con los
   modelos de `herramientas/blender/modelos.py` (o añade los que falten).
2. **Render**: ejecuta el kit. Salen las piezas, el suelo, las fichas y la composición.
3. **Escena**: copia `generar_calle_mayor.py` y ajusta los puntos de interés, la zona
   transitable, el alguacil o quien haga falta.
4. **Puntos de interés**: un nodo con `PuntoDeInteres.cs` por cada cosa examinable, con
   su `Zona` y su `Llegada`. El campo *Nudo* es el nombre del nudo de Ink.
5. **Luces**: `PointLight2D` con `Parpadeo.cs` sobre cada vela o farol, con poca energía:
   la luz ya está en las piezas, esto solo la hace temblar.
6. **Tono de los personajes**: en el nodo del lugar, *TonoPersonajes* apaga y enfría a
   los personajes para que encajen con la luz pintada (de noche, un gris azulado).
7. **Prueba**: ejecuta el juego. Para ver lo invisible, activa en el menú *Depurar* la
   opción de formas de navegación.

## Recortar a mano (si hace falta)

Para tapar algo que no sea una pieza (una esquina pintada en el suelo, por ejemplo):

- crea un `Polygon2D` dentro de `Entidades`, **sin moverlo del origen**;
- asígnale el script `Oclusor.cs` y como *Texture* la imagen que hay que recortar;
- dibuja su silueta y, en *Linea Base*, pon la altura (y) del punto donde toca el suelo
  más cerca de la cámara (con -1 se usa el punto más bajo del polígono).
