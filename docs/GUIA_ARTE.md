# Guía de arte con ChatGPT

Cómo hacer el arte para que encaje en el juego sin retoques. La regla de oro: **todas
las imágenes comparten cámara, escala y luz**. Si una sola se sale de eso, se nota en
cuanto el pesquisidor camina por encima.

## 1. Cómo se hacen los escenarios

Los escenarios no se piden enteros: se componen de **piezas** (cada casa, el carro, los
barriles) que se montan en Godot sobre un suelo.

1. **Yo modelo cada pieza por código en Blender** (`herramientas/kit_calle_mayor.py`):
   cada teja, cada tabla, cada clavo, cada balaustre. Así la cámara, la escala, las
   sombras y los contornos son exactos, y el juego sabe dónde está cada columna.
2. **Lo renderizo con la luz de la escena** (luna fría desde arriba a la izquierda,
   velas cálidas). Ese render ya entra en el juego tal cual.
3. **Tú se lo das a ChatGPT para que lo repinte** con mano de pintor (la textura, el
   desgaste, la pincelada) sin mover un solo contorno. Las peticiones completas, pieza
   a pieza, están en [`docs/arte/piezas/README.md`](arte/piezas/README.md).
4. Yo meto la pintura con `herramientas/procesar_pieza.py`, que comprueba que respeta la
   silueta y la encaja en su sitio. Si no la respeta, se repite.

El suelo de la calle (empedrado, canalillo, charcos) lo hago yo entero.

## 2. Plantillas y datos de la cámara

Están en `docs/arte/`. Sirven para personajes y objetos sueltos.

- **`plantilla_perspectiva.png`**: la cámara del juego. Rejilla isométrica 2:1, un bloque
  de 3 × 3 × 3 m, un muro con puerta de 2,20 m y una persona de 1,70 m.
- **`plantilla_personaje.png`**: las dos poses que necesito de cada personaje.

| | |
|---|---|
| Proyección | isométrica 2:1, ortográfica (sin fuga), giro 45°, elevación 30° |
| Suelo | las líneas bajan 1 px por cada 2 px en horizontal |
| Escala | 1 m de suelo ≈ 76 px en horizontal · 1 m de altura ≈ 94 px |
| Persona de 1,70 m | ≈ 159 px (con sombrero, ≈ 180 px) |
| Luz | de noche: luna fría desde arriba a la izquierda, rasante a las fachadas; velas cálidas |
| Lienzo del suelo | 3200 × 1800 |

## 3. Bloque de estilo (va en todas las peticiones)

Una vez fijado, no se toca: cada variación de este texto es una variación de estilo.

> Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José de Ribera y
> Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de La Tour. La
> mayor parte de la imagen queda en penumbra profunda: sombras casi negras y cálidas,
> nunca azul saturado. El detalle y la textura se concentran donde cae la luz. Pincelada
> visible pero contenida, empastes en las luces, veladuras en las sombras. Paleta
> terrosa: tierras, sienas, ocres, cal sucia, almagra apagada, grises de piedra; la luna
> enfría y apaga los colores; la luz de vela es ámbar y se apaga enseguida. Nada de
> contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio:
> superficies gastadas, polvo, hollín, humedad, desconchones, madera reseca.

## 4. Personajes

Cada personaje necesita **dos dibujos**: de frente (mirando abajo a la derecha) y de
espaldas (mirando arriba a la derecha). Las otras dos direcciones las saco en espejo.
Caminar lo animo yo con un balanceo, así que no hacen falta fotogramas.

### Qué pedir

- Cuerpo entero, de pies a cabeza, sin cortar el sombrero ni los pies.
- **Fondo transparente**. Si no lo consigue, **fondo magenta puro (#FF00FF)**, liso,
  sin sombras ni degradados. Evita el magenta en la ropa del personaje.
- La misma cámara que los escenarios: se le ve un poco desde arriba.
- Postura neutra, brazos que no se separen mucho del cuerpo.
- Sin sombra en el suelo (la pone el juego).

### Cómo mantener al mismo personaje

1. Primero pide un **retrato de referencia** del personaje y ajústalo hasta que te guste.
2. Después, en la **misma conversación**, pide las dos poses adjuntando ese retrato y la
   plantilla de personaje: «el mismo personaje de la imagen 1, en las dos poses de la
   imagen 2».
3. Si una pose sale bien y la otra no, pide rehacer solo la que falla y repite los
   rasgos clave (ropa, colores, barba, sombrero).

### Petición tipo

> Imagen 1: retrato del personaje. Imagen 2: plantilla de poses.
> Dibuja al personaje de la imagen 1 de cuerpo entero en las dos poses de la imagen 2:
> a la izquierda de frente, mirando abajo a la derecha; a la derecha de espaldas,
> mirando arriba a la derecha. Vista ligeramente desde arriba, como en un juego
> isométrico. Fondo magenta puro (#FF00FF) liso, sin sombra en el suelo, sin texto.
> [Rasgos clave: alguacil de unos cincuenta años, ropilla parda, capotillo corto,
> sombrero negro, vara de justicia en la mano izquierda, farol en la derecha.]
> [Bloque de estilo]

## 5. Objetos sueltos

Los objetos fijos del escenario (carro, barriles) son piezas como las casas: los modelo
yo y ChatGPT los repinta. Lo que se mueve o aparece y desaparece (un cadáver que se
llevan, una carta en el suelo) se pide como los personajes: suelto, con fondo
transparente o magenta y con la plantilla de perspectiva adjunta para la escala.

## 6. Cómo me lo pasas

- Descarga siempre el **PNG original** de ChatGPT, no una captura de pantalla.
- Nombres sin espacios ni tildes: `casa_3_pintada.png`, `alguacil_frente.png`,
  `alguacil_espaldas.png`.
- Súbelos a la carpeta `arte/entrada/` del repositorio (en GitHub: *Add file → Upload
  files*), o déjamelos en una carpeta del PC que conectes a la conversación.
- Dime qué es cada cosa y dónde va.

## 7. Qué hago yo con ellos

1. Piezas: `herramientas/procesar_pieza.py <pieza> <imagen>` quita el magenta, encaja la
   pintura sobre la silueta, mide cuánto coincide (por debajo del 92 % no la acepta) y
   la deja en `arte/piezas/`. Figuras: `herramientas/procesar_arte.py` (sin fondo y a la
   altura del juego).
2. La zona por la que se camina, los obstáculos y los recortes que tapan al pesquisidor
   (columnas, el carro en tiras) salen de la misma geometría que la pieza.
3. Coloco los puntos de interés, las luces que parpadean y el punto de entrada.
4. Lo pruebo con capturas y te lo enseño.

## 8. Aviso sobre Steam

Si el juego llega a venderse en Steam, Valve obliga a declarar en la ficha de la tienda
el contenido generado con IA que ve el jugador (imágenes, textos, voces). Las
herramientas de programación con IA no hay que declararlas. Conviene apuntar desde ya
qué imágenes salen de ChatGPT y cuáles retocas tú, para declararlo bien cuando toque.
