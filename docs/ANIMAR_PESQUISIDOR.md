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
solo durante el vuelo. La pelvis y los hombros giran en sentidos contrarios, los
brazos oscilan en oposición a las piernas y el borde del ferreruelo responde con
un pequeño retraso. La cabeza y el sombrero conservan su forma como una pieza rígida.

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
Los brazos y el ferreruelo se mueven mediante pesos sobre la misma malla, no como
capas completas con las partes ocultas reconstruidas. Su recorrido debe mantenerse
contenido para evitar estirar la pintura o descubrir zonas que no están dibujadas.

Antes de adoptarla como marcha definitiva hay que revisar el apoyo de las suelas,
las rodillas, los giros y el aspecto a la escala real de la calle. Si la deformación
resulta visible, el siguiente paso es preparar capas completas de cada miembro,
incluidas sus partes ocultas, o un personaje 3D animado con render a sprites.

## Comprobaciones

Las pruebas unitarias cubren que el pie apoyado se mantenga en su sitio, que siempre
haya al menos uno apoyado y que el ciclo no salte en los cambios entre apoyo y vuelo.
También comprueban que el gesto corporal no arrastre las suelas, que no se estiren
la cabeza y el sombrero, y que la postura original se recupere al detenerse.

La escena también admite un recorrido automático que comprueba la llegada, el
reposo, la recolocación y la vuelta al dibujo original:

```powershell
godot --headless --path . res://pruebas/animacion/PruebaAnimacion.tscn -- --automatico
```

Con ventana, `--capturas=carpeta` guarda 24 fotogramas consecutivos de cada trayecto.
Para un vídeo a 24 imágenes por segundo, ejecutar Godot con `--fixed-fps 24`.
`--detalle` acerca la cámara al doble para revisar los gestos. El resto de las
comprobaciones del proyecto se ejecuta como indica `CLAUDE.md`.
