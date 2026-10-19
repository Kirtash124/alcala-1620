# Primera prueba de marcha del Pesquisidor

19 de octubre de 2026.

El juego ya incluye los dibujos corregidos de frente y espaldas. `Personaje.cs`
resuelve el paseo, los giros y la colocación por los pies, y mueve el dibujo entero
con un balanceo. Esta prueba permite comparar ese movimiento con una marcha que
desplaza por separado ambas piernas, conservando las imágenes originales.

## Probarlo

1. Abrir el proyecto con Godot 4.7.1 .NET y compilar.
2. Abrir `pruebas/animacion/PruebaAnimacion.tscn` y ejecutar esa escena con F6.
3. Pulsar en la calle para andar. Pulsar A para alternar la marcha experimental y
   el balanceo original, a la misma velocidad de paseo.

F5 sigue abriendo la partida habitual. No se modifica su personaje ni se sustituyen
sus PNG. Las conversaciones, el diario, las sombras, la navegación y la colocación
por delante o detrás de las columnas conservan el sistema del juego.

## Cómo funciona

`DibujoArticulado` se añade como hijo del jugador en esta escena de prueba. Oculta
el sprite original y dibuja su misma textura mediante una malla de triángulos.
Al deformar la malla, las dos piernas avanzan alternativamente y los pies se elevan
solo durante el vuelo. El tronco acompaña el paso con un movimiento contenido.

La fase depende de la distancia recorrida. Durante el apoyo, el pie retrocede
respecto al tronco la misma distancia que avanza el personaje por el escenario.
Al parar, el gesto vuelve a la postura de reposo. Al recolocar al jugador, se descarta
la fase anterior para no interpretar una carga de partida como una zancada.

Se mantienen las dos texturas, el espejo para las cuatro direcciones y el tono
que aplica el lugar. La sombra queda anclada al personaje, fuera de la malla.
El ensayo usa 105 píxeles por segundo y un ciclo de 64 píxeles de recorrido. Son
valores de partida para revisar visualmente, no medidas definitivas del juego.

## Alcance y siguientes pasos

Es una prueba de deformación de la pintura, no un ciclo nuevo dibujado. Las uniones
de la ropa y las perspectivas de los zapatos siguen siendo las del dibujo original.
Los brazos y el ferreruelo todavía no tienen articulaciones independientes.

Antes de adoptarla como marcha definitiva hay que revisar el apoyo de las suelas,
las rodillas, los giros y el aspecto a la escala real de la calle. Si la deformación
resulta visible, el siguiente paso es preparar capas completas de cada miembro,
incluidas sus partes ocultas, o un personaje 3D animado con render a sprites.

## Comprobaciones

Las pruebas unitarias cubren que el pie apoyado se mantenga en su sitio, que siempre
haya al menos uno apoyado y que el ciclo no salte en los cambios entre apoyo y vuelo.

La escena también admite un recorrido automático que comprueba la llegada, el
reposo, la recolocación y la vuelta al dibujo original:

```powershell
godot --headless --path . res://pruebas/animacion/PruebaAnimacion.tscn -- --automatico
```

Con ventana, `--capturas=carpeta` guarda imágenes del recorrido. El resto de las
comprobaciones del proyecto se ejecuta como indica `CLAUDE.md`.
