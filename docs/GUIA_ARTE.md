# Guía de arte con ChatGPT

Cómo generar fondos, personajes y objetos para que encajen en el juego sin retoques.
La regla de oro: **todas las imágenes comparten cámara, escala y luz**. Si una sola
imagen se sale de eso, se nota en cuanto el pesquisidor camina por encima.

## 1. Las dos plantillas

Están en `docs/arte/`. Adjúntalas a ChatGPT siempre que pidas algo nuevo.

- **`plantilla_perspectiva.png`**: la cámara del juego. Rejilla isométrica 2:1, un bloque
  de 3 × 3 × 3 m, un muro con puerta de 2,20 m y una persona de 1,70 m. Sirve para
  fondos y objetos.
- **`plantilla_personaje.png`**: las dos poses que necesito de cada personaje.

Datos de la cámara, por si ChatGPT pregunta o se desvía:

| | |
|---|---|
| Proyección | isométrica 2:1, ortográfica (sin fuga), giro 45°, elevación 30° |
| Suelo | las líneas bajan 1 px por cada 2 px en horizontal |
| Escala | 1 m de suelo ≈ 76 px en horizontal · 1 m de altura ≈ 94 px |
| Persona de 1,70 m | ≈ 159 px (con sombrero, ≈ 180 px) |
| Luz principal | desde arriba a la izquierda |
| Lienzo de un escenario | 2560 × 1440 (16:9) |

## 2. Bloque de estilo (pégalo en todas las peticiones)

Es una propuesta de partida. Cámbialo a tu gusto, pero una vez fijado no lo toques:
cada variación de este texto es una variación de estilo.

> Pintura digital con aspecto de óleo, pincelada visible pero contenida. Paleta terrosa:
> ocres, sienas, cal sucia, grises azulados. Contraste entre luz cálida de vela y noche
> fría azulada. Arquitectura castellana de principios del siglo XVII: piedra, ladrillo,
> enfoscado de cal, madera vieja, teja árabe, forja. Nada de contornos negros ni aspecto
> de dibujos animados. Texturas ricas y realistas, desgaste y suciedad creíbles.

## 3. Fondos de escenario

### Qué pedir

- El escenario **vacío**: sin personas, sin animales, sin texto, sin marcos ni firmas.
- Formato **16:9 apaisado**, la mayor resolución que te dé (lo ideal, 2560 × 1440).
- La **misma cámara** que la plantilla de perspectiva, adjuntándola.
- La luz que tendrá la escena en el juego (noche con velas, mediodía...). Las luces que
  parpadean (velas, faroles) las añado yo encima, pero el fondo tiene que pintarlas ya
  encendidas y con su resplandor.

### Lo que la cámara no puede enseñar (importante)

El fondo es una imagen plana: el juego no puede ver lo que la imagen no pinta.

- **Nada de voladizos profundos sobre zonas donde se camina.** Un soportal muy hondo
  esconde su interior bajo el piso de arriba, y el pesquisidor desaparecería al entrar.
  Soportales de unos 2 m de fondo y techos altos funcionan; los de 3 m, no.
- **El suelo transitable tiene que verse.** Ni callejones tapados por tejados ni
  rincones detrás de esquinas.
- **Nada importante tapado.** Si algo se puede examinar (una puerta, una hornacina, un
  cadáver), que se vea entero.
- **Objetos en primer plano, con mesura.** Un carro o unos barriles delante dan
  profundidad y los sé recortar para que el pesquisidor pase por detrás. Una pared
  entera delante, no.

### Petición tipo

> Adjunto una plantilla de cámara. Pinta un escenario de videojuego isométrico con
> **exactamente** esa perspectiva y esa escala (la figura gris mide 1,70 m), en formato
> 16:9 a la máxima resolución posible.
> Escenario: [describe el lugar: la calle Mayor de Alcalá de Henares en 1620, de noche,
> con soportales de unos 2 m de fondo sobre columnas de piedra, empedrado, una hornacina
> con una vela...].
> Sin personas ni animales. Sin texto. La luz principal viene de arriba a la izquierda.
> [Bloque de estilo]

Si ChatGPT tuerce la cámara, no pidas «arréglalo»: pide un solo cambio cada vez
(«mantén todo igual y alinea las líneas del suelo con las de la plantilla»).

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

Cosas que se mueven o aparecen y desaparecen (un cadáver que se llevan, una carta en el
suelo, una puerta que se abre): igual que los personajes, sueltas, con fondo
transparente o magenta y con la plantilla de perspectiva adjunta para la escala.
Lo que no cambia nunca va pintado en el fondo.

## 6. Cómo me lo pasas

- Descarga siempre el **PNG original** de ChatGPT, no una captura de pantalla.
- Nombres sin espacios ni tildes: `fondo_calle-mayor_v2.png`, `alguacil_frente.png`,
  `alguacil_espaldas.png`.
- Súbelos a la carpeta `arte/entrada/` del repositorio (en GitHub: *Add file → Upload
  files*), o déjamelos en una carpeta del PC que conectes a la conversación.
- Dime qué es cada cosa y dónde va.

## 7. Qué hago yo con ellos

1. Los limpio y los escalo con `herramientas/procesar_arte.py` (fondos a 2560 × 1440;
   figuras sin fondo y a la altura del juego).
2. Dibujo la zona por la que se camina, los obstáculos y los recortes que tapan al
   pesquisidor cuando pasa por detrás (columnas, carros, esquinas).
3. Coloco los puntos de interés, las luces que parpadean y el punto de entrada.
4. Lo pruebo con capturas y te lo enseño.

## 8. Aviso sobre Steam

Si el juego llega a venderse en Steam, Valve obliga a declarar en la ficha de la tienda
el contenido generado con IA que ve el jugador (imágenes, textos, voces). Las
herramientas de programación con IA no hay que declararlas. Conviene apuntar desde ya
qué imágenes salen de ChatGPT y cuáles retocas tú, para declararlo bien cuando toque.
