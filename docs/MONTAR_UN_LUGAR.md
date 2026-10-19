# Montar un escenario nuevo en Godot

Partimos de un fondo ya procesado en `arte/fondos/` (2560 × 1440).
La calle Mayor (`escenas/lugares/CalleMayor.tscn`) sirve de ejemplo de todo lo que sigue.

## Estructura de la escena

```
NombreDelLugar (Node2D, script Lugar.cs)   Id y Titulo
├─ Fondo (Sprite2D)            la imagen; «Centered» desactivado; en el origen
├─ Ambiente (CanvasModulate)   tono general (noche: azul oscuro; día: blanco)
├─ Transitable (Polygon2D)     contorno del suelo por el que se camina
├─ Obstaculos (Node2D)
│   └─ ... (Polygon2D)         huecos dentro de lo transitable: columnas, carros, cuerpos
├─ Inicio (Marker2D)           dónde aparece el pesquisidor
├─ Entidades (Node2D)          «Y Sort Enabled» activado
│   ├─ oclusores (Polygon2D, script Oclusor.cs)
│   └─ personajes y objetos sueltos
├─ Luces (Node2D)
│   └─ ... (PointLight2D, script Parpadeo.cs)
└─ Puntos (Node2D)
    └─ Nombre (Node2D, script PuntoDeInteres.cs)   Nombre, Nudo
        ├─ Zona (Polygon2D)    donde se hace clic
        └─ Llegada (Marker2D)  adonde camina el pesquisidor
```

## Pasos

1. **Duplica** `CalleMayor.tscn` y borra lo que no sirva, o crea la escena desde cero con
   la estructura de arriba.
2. **Fondo**: arrastra la imagen al campo *Texture* del nodo `Fondo`.
3. **Transitable**: selecciona el nodo y dibuja el contorno del suelo con la herramienta
   de polígonos (barra superior del lienzo). El color verde solo se ve en el editor.
4. **Obstáculos**: un `Polygon2D` dentro de `Obstaculos` por cada cosa que no se puede
   atravesar. Basta con su huella en el suelo.
5. **Oclusores**: para cada objeto que debe tapar al pesquisidor cuando pasa por detrás
   (columna, carro, esquina):
   - crea un `Polygon2D` dentro de `Entidades`, **sin moverlo del origen**;
   - asígnale el script `Oclusor.cs` y como *Texture* la misma imagen del fondo;
   - dibuja su silueta;
   - en *Linea Base*, la altura (y) del punto donde el objeto toca el suelo más cerca
     de la cámara. Con -1 se usa el punto más bajo del polígono.

   Limitación: la línea base es horizontal. En muros largos en diagonal, divídelos en
   varios oclusores estrechos.
6. **Puntos de interés**: un nodo con `PuntoDeInteres.cs` por cada cosa examinable, con
   su `Zona` y su `Llegada`. El campo *Nudo* es el nombre del nudo de Ink.
7. **Luces**: `PointLight2D` con `Parpadeo.cs` sobre cada vela, farol o fuego. Si no
   tiene textura, se le genera un degradado.
8. **Prueba**: ejecuta el juego. Para ver lo invisible, activa en el menú *Depurar* la
   opción de formas de navegación.
