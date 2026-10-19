# Piezas de la calle Mayor: peticiones para ChatGPT

Cada pieza del escenario (cada casa, el carro, los barriles) está modelada por código en
Blender y renderizada con la cámara y la luz del juego. ChatGPT solo tiene que
**repintarla con mano de pintor sin mover ningún contorno**. Este documento trae, pieza
a pieza, la petición completa: se copia entera, sin quitar nada.

## Archivos de cada pieza (en esta carpeta)

| Archivo | Para qué |
|---|---|
| `<pieza>_luz.png` | **Imagen 1**: el render con la luz de noche definitiva. Es la que se repinta. |
| `<pieza>_maqueta.png` | **Imagen 2**: la misma pieza en arcilla gris, para que se entiendan los volúmenes. |

Las dos están sobre magenta puro (#FF00FF) y tienen el tamaño nativo de ChatGPT
(1024 × 1536 las casas, 1536 × 1024 el carro, 1024 × 1024 los barriles).

## Orden de trabajo

1. **Primero la casa de la hornacina (`casa_3`)**. Es la pieza de referencia: hasta que
   no te guste, no se pasa a las demás.
2. Cuando esté aprobada, en todas las demás se adjunta también como **imagen 3**
   (referencia de estilo). Usa la versión que me pases ya procesada, la de
   `arte/piezas/casa_3.png`, o la pintada original.
3. Una conversación por pieza. Si algo sale mal, se pide **un solo cambio cada vez**.

## Antes de pasármela, comprueba

- **El contorno es el mismo.** Pon la pintura encima del render (en cualquier visor que
  permita superponer, o pasando de una a otra): no puede moverse nada, ni crecer, ni
  encoger. Mi herramienta mide la coincidencia y por debajo del 92 % la rechaza.
- **El fondo sigue magenta liso**, también en los huecos (entre los radios del carro,
  entre los barrotes del balcón).
- **La luz viene de arriba a la izquierda** y las sombras caen como en el render.
- **No ha inventado nada**: ni personas, ni letreros, ni macetas, ni farolas.
- En la casa de la hornacina, **la cera negra se ve**.

Si cambia el contorno, esta frase suele bastar: *«Mantén exactamente la silueta, el
encuadre y la posición de todo de la imagen 1; solo cambia la pintura de dentro.»*

## Cómo me la pasas

PNG original (no captura), con el nombre `<pieza>_pintada.png` (por ejemplo
`casa_3_pintada.png`), en `arte/entrada/piezas/` del repositorio o adjunta en la
conversación. Yo la meto con `herramientas/procesar_pieza.py`.

---

## Casa de la hornacina (`casa_3`) · pieza de referencia

Adjuntos: imagen 1 `casa_3_luz.png`, imagen 2 `casa_3_maqueta.png`.

> Adjunto dos imágenes de la misma pieza de un videojuego isométrico. Imagen 1: render
> con la luz definitiva de la escena. Imagen 2: la misma pieza en arcilla gris, para que
> veas bien los volúmenes.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo, con el mismo tamaño de
> lienzo, la misma cámara isométrica y exactamente el mismo contorno. Cada borde, cada
> hueco, cada columna, cada teja y cada barrote tienen que quedar donde están. No añadas
> nada fuera de la silueta ni quites nada de dentro. El fondo magenta (#FF00FF) queda
> magenta liso, sin sombras, sin degradados y sin halo alrededor de la pieza.
>
> **Qué es.** La casa de la hornacina, en la calle Mayor de Alcalá de Henares hacia
> 1620, de noche. Casa de dos plantas y desván, enlucida de almagra (un rojo tierra
> apagado, gastado y desconchado), con soportal en la planta baja.
> Arriba: a la izquierda una ventana con una hoja entornada hacia dentro que deja ver
> oscuridad; a la derecha un balcón de hierro forjado con la puerta de tablas cerrada;
> bajo el alero, un ventanuco de desván cerrado con una tablilla. Recercados de cal
> blanca alrededor de los huecos. Alero de canecillos de madera y tejado de teja árabe
> con su caballete. En el costado derecho, por encima del tejado de la casa vecina, la
> medianera de tapial con verdugadas de ladrillo (aparejo toledano), sin enlucir.
> Abajo, el soportal: dos columnas toscanas de piedra (en la calle Mayor muchas son
> romanas, reaprovechadas de Complutum: que se noten viejas y no idénticas), zapatas de
> madera talladas y una viga corrida; en la columna de la izquierda, una argolla de
> hierro para atar caballerías. En el muro del fondo, sobre un zócalo de mampostería:
> a la izquierda la hornacina, con su arco, su repisa de piedra moldurada, un lienzo
> devoto pequeño y muy oscurecido por el humo (una Virgen con manto) y una vela blanca
> encendida; en la repisa y bajando por el muro, **goterones de cera negra**: es una
> pista del juego, tiene que verse sin exagerarla. A la derecha, una puerta de tablas
> claveteada, con pernios y aldaba de hierro y jambas de sillares. Suelo del soportal de
> losas de piedra gastadas.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. La mayor parte de la imagen queda en penumbra profunda: sombras casi negras y
> cálidas, nunca azul saturado. El detalle y la textura se concentran donde cae la luz.
> Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras.
> Paleta terrosa: tierras, sienas, ocres, cal sucia, almagra apagada, grises de piedra;
> la luna enfría y apaga los colores; la luz de vela es ámbar y se apaga enseguida. Nada
> de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio:
> superficies gastadas, polvo, hollín, humedad, desconchones, madera reseca.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> luz general es la luna, fría y tenue, que entra desde arriba a la izquierda de la
> imagen y roza las fachadas casi de lado: marca el relieve de la cal, la piedra y la
> madera con sombras largas hacia la derecha. Bajo el soportal hay penumbra. Respeta las
> sombras de la imagen 1: su dirección, su forma y dónde caen. La única luz cálida de
> esta casa es la vela de la hornacina: ilumina el nicho, la repisa y el arranque del
> muro, y a un palmo ya se apaga.
>
> **Continuidad.** Esta pieza se monta junto a otras casas en la misma calle, y es la
> referencia de estilo para todas. Las columnas, zapatas, viga, tejas y losas tienen que
> poder repetirse igual en las casas vecinas: nada de rasgos únicos en ellas.
>
> **Rigor histórico.** Castilla, hacia 1620. Ventanas sin vidrieras, con hojas y
> postigos de madera. Hierro de forja negro y oxidado. No pueden aparecer: farolas,
> cristales, rótulos o letreros, canalones o bajantes de chapa, cables, rejas o
> barandillas de fundición, persianas, ladrillo industrial, macetas, carteles. Sin
> personas, animales, texto, firmas ni marcos.

---

## Casa del zapatero (`casa_1`)

Adjuntos: imagen 1 `casa_1_luz.png`, imagen 2 `casa_1_maqueta.png`, imagen 3 la casa
de la hornacina ya aprobada.

> Adjunto tres imágenes. Imagen 1: render con la luz definitiva de una pieza de un
> videojuego isométrico. Imagen 2: la misma pieza en arcilla gris, para que veas bien
> los volúmenes. Imagen 3: otra pieza de la misma calle, ya pintada: es la referencia
> de estilo, de color y de acabado.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la
> imagen 3, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente el
> mismo contorno. Cada borde, cada hueco, cada columna, cada teja y cada barrote tienen
> que quedar donde están. No añadas nada fuera de la silueta ni quites nada de dentro.
> El fondo magenta (#FF00FF) queda magenta liso, sin sombras, sin degradados y sin halo.
>
> **Qué es.** La casa del zapatero, en la calle Mayor de Alcalá de Henares hacia 1620,
> de noche. Casa de dos plantas y desván, enlucida de ocre (cal teñida, gastada y con
> desconchones que dejan ver el ladrillo), con soportal. Arriba: a la izquierda un
> balcón de hierro forjado con la puerta cerrada; a la derecha una ventana con una hoja
> entornada hacia dentro. Recercados de cal blanca. Alero de canecillos de madera y
> tejado de teja árabe. Abajo, el soportal: dos columnas toscanas de piedra, viejas y no
> idénticas, con zapatas de madera y viga corrida. En el muro del fondo, sobre un zócalo
> de mampostería: a la izquierda una puerta de tablas claveteada entre jambas de
> sillares; a la derecha la tienda del zapatero, cerrada por la noche: tableros de
> tablas, un peinazo y una barra de hierro cruzada con candado. Suelo de losas.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. La mayor parte de la imagen queda en penumbra profunda: sombras casi negras y
> cálidas, nunca azul saturado. El detalle y la textura se concentran donde cae la luz.
> Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras.
> Paleta terrosa: tierras, sienas, ocres, cal sucia, almagra apagada, grises de piedra;
> la luna enfría y apaga los colores. Nada de contornos negros, nada de aspecto de
> dibujos animados ni de render 3D limpio: superficies gastadas, polvo, hollín,
> humedad, desconchones, madera reseca.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> luz general es la luna, fría y tenue, que entra desde arriba a la izquierda de la
> imagen y roza las fachadas casi de lado, con sombras largas hacia la derecha. Bajo el
> soportal hay penumbra. Respeta las sombras de la imagen 1. En esta casa no hay
> ninguna luz cálida: todo es luna y sombra.
>
> **Continuidad.** Columnas, zapatas, viga, tejas, losas, hierros y la textura de la
> cal tienen que ser los de la imagen 3: es la misma calle, la misma noche y la misma
> mano. Solo cambia el color del enlucido (aquí ocre) y lo que hay en cada hueco.
>
> **Rigor histórico.** Castilla, hacia 1620. Las tiendas no tienen letreros ni
> escaparates: de noche se cierran con tableros. Ventanas sin vidrieras, con hojas y
> postigos de madera. Hierro de forja negro y oxidado. No pueden aparecer: farolas,
> cristales, rótulos o letreros, canalones o bajantes de chapa, cables, rejas o
> barandillas de fundición, persianas, ladrillo industrial, macetas, carteles. Sin
> personas, animales, texto, firmas ni marcos.

---

## Casa de la ventana encendida (`casa_2`)

Adjuntos: imagen 1 `casa_2_luz.png`, imagen 2 `casa_2_maqueta.png`, imagen 3 la casa
de la hornacina ya aprobada.

> Adjunto tres imágenes. Imagen 1: render con la luz definitiva de una pieza de un
> videojuego isométrico. Imagen 2: la misma pieza en arcilla gris, para que veas bien
> los volúmenes. Imagen 3: otra pieza de la misma calle, ya pintada: es la referencia
> de estilo, de color y de acabado.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la
> imagen 3, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente el
> mismo contorno. Cada borde, cada hueco, cada columna, cada teja y cada barrote tienen
> que quedar donde están. No añadas nada fuera de la silueta ni quites nada de dentro.
> El fondo magenta (#FF00FF) queda magenta liso, sin sombras, sin degradados y sin halo.
>
> **Qué es.** Una casa de la calle Mayor de Alcalá de Henares hacia 1620, de noche.
> Casa de dos plantas y desván, encalada de blanco (cal sucia, con chorretones y
> humedad en la parte baja), con soportal. Arriba: a la izquierda un balcón de hierro
> forjado con la puerta cerrada; a la derecha otro balcón con las hojas abiertas hacia
> dentro y la habitación iluminada por un candil. Recercados de cal ocre. Alero de
> canecillos de madera y tejado de teja árabe. Abajo, el soportal: dos columnas
> toscanas de piedra, viejas y no idénticas, con zapatas de madera y viga corrida. En
> el muro del fondo, sobre un zócalo de mampostería: a la izquierda una puerta de tablas
> pintada de almagra, desconchada, entre jambas de sillares; a la derecha una ventana
> con recercado de piedra, reja de hierro de cuadradillo con pletinas y postigos verdes
> cerrados. Suelo de losas.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. La mayor parte de la imagen queda en penumbra profunda: sombras casi negras y
> cálidas, nunca azul saturado. El detalle y la textura se concentran donde cae la luz.
> Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras.
> Paleta terrosa: tierras, sienas, ocres, cal sucia, almagra apagada, grises de piedra;
> la luna enfría y apaga los colores; la luz del candil es ámbar y se apaga enseguida.
> Nada de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio:
> superficies gastadas, polvo, hollín, humedad, desconchones, madera reseca.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> luz general es la luna, fría y tenue, que entra desde arriba a la izquierda de la
> imagen y roza las fachadas casi de lado, con sombras largas hacia la derecha. Bajo el
> soportal hay penumbra. Respeta las sombras de la imagen 1. La única luz cálida es la
> del balcón de la derecha: el candil de dentro baña de ámbar las jambas, las hojas
> abiertas y los barrotes del balcón, y apenas toca la fachada de alrededor. Es el punto
> más luminoso de la pieza.
>
> **Continuidad.** Columnas, zapatas, viga, tejas, losas, hierros y la textura de la
> cal tienen que ser los de la imagen 3: es la misma calle, la misma noche y la misma
> mano. Solo cambia el color del enlucido (aquí blanco) y lo que hay en cada hueco.
>
> **Rigor histórico.** Castilla, hacia 1620. Ventanas sin vidrieras, con hojas y
> postigos de madera; dentro, luz de candil de aceite o de vela, nunca de lámpara.
> Hierro de forja negro y oxidado. No pueden aparecer: farolas, cristales, rótulos o
> letreros, canalones o bajantes de chapa, cables, rejas o barandillas de fundición,
> persianas, cortinas de encaje, ladrillo industrial, macetas, carteles. Sin personas
> (tampoco siluetas en la ventana), animales, texto, firmas ni marcos.

---

## Cerería de la esquina (`casa_4`)

Adjuntos: imagen 1 `casa_4_luz.png`, imagen 2 `casa_4_maqueta.png`, imagen 3 la casa
de la hornacina ya aprobada.

> Adjunto tres imágenes. Imagen 1: render con la luz definitiva de una pieza de un
> videojuego isométrico. Imagen 2: la misma pieza en arcilla gris, para que veas bien
> los volúmenes. Imagen 3: otra pieza de la misma calle, ya pintada: es la referencia
> de estilo, de color y de acabado.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la
> imagen 3, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente el
> mismo contorno. Cada borde, cada hueco, cada columna, cada teja y cada barrote tienen
> que quedar donde están. No añadas nada fuera de la silueta ni quites nada de dentro.
> El fondo magenta (#FF00FF) queda magenta liso, sin sombras, sin degradados y sin halo.
>
> **Qué es.** La cerería de la esquina, en la calle Mayor de Alcalá de Henares hacia
> 1620, de noche. Casa de esquina de dos plantas y desván, encalada de blanco sucio,
> con soportal; se ve también su costado, que da a una bocacalle, con un piñón de
> tejado rematado de tejas. Arriba: a la izquierda un balcón de hierro forjado con las
> hojas abiertas y la habitación iluminada por un candil; a la derecha una ventana con
> una hoja entornada. En el costado, una ventana alta cerrada y, abajo, una ventana con
> reja. Alero de canecillos y tejado de teja árabe. Abajo, el soportal: columnas
> toscanas de piedra, viejas y no idénticas (la de la esquina con dos zapatas
> cruzadas), viga corrida. En el muro del fondo: a la izquierda una puerta de tablas
> pintada de almagra; a la derecha la cerería, abierta: el tablero bajo hace de
> mostrador, las hojas de la tienda (pintadas de verde, gastadas) están abiertas contra
> el muro; dentro, anaqueles con velas; de un varal cuelgan manojos de velas blancas
> colgadas por el pabilo; en el mostrador, una caja de velas y un cabo encendido en una
> palmatoria de hierro.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. La mayor parte de la imagen queda en penumbra profunda: sombras casi negras y
> cálidas, nunca azul saturado. El detalle y la textura se concentran donde cae la luz.
> Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras.
> Paleta terrosa: tierras, sienas, ocres, cal sucia, almagra apagada, grises de piedra;
> la luna enfría y apaga los colores; la luz de vela es ámbar y se apaga enseguida.
> Nada de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio:
> superficies gastadas, polvo, hollín, humedad, desconchones, madera reseca.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> luz general es la luna, fría y tenue, que entra desde arriba a la izquierda de la
> imagen y roza las fachadas casi de lado, con sombras largas hacia la derecha. Bajo el
> soportal hay penumbra. Respeta las sombras de la imagen 1. Luces cálidas: la vela del
> mostrador, que dora las velas colgadas y el mostrador (es la escena más «La Tour» de
> la calle); un resplandor de candil al fondo de la tienda; y el balcón encendido de
> arriba a la izquierda.
>
> **Continuidad.** Columnas, zapatas, viga, tejas, losas, hierros y la textura de la
> cal tienen que ser los de la imagen 3: es la misma calle, la misma noche y la misma
> mano. Solo cambia el color del enlucido (aquí blanco) y lo que hay en cada hueco.
>
> **Rigor histórico.** Castilla, hacia 1620. Las velas de cera blanca se vendían
> colgadas por el pabilo en manojos; las tiendas no tienen letreros ni escaparates.
> Ventanas sin vidrieras, con hojas y postigos de madera. Hierro de forja negro y
> oxidado. No pueden aparecer: farolas, cristales, rótulos o letreros, canalones o
> bajantes de chapa, cables, rejas o barandillas de fundición, persianas, ladrillo
> industrial, macetas, carteles, velas de colores ni de formas modernas. Sin personas
> (tampoco el cerero), animales, texto, firmas ni marcos.

---

## Carro de varas (`carro`)

Adjuntos: imagen 1 `carro_luz.png`, imagen 2 `carro_maqueta.png`, imagen 3 la casa de
la hornacina ya aprobada.

> Adjunto tres imágenes. Imagen 1: render con la luz definitiva de un objeto de un
> videojuego isométrico. Imagen 2: el mismo objeto en arcilla gris, para que veas bien
> los volúmenes. Imagen 3: otra pieza de la misma calle, ya pintada: es la referencia
> de estilo, de color y de acabado.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la
> imagen 3, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente el
> mismo contorno. Cada rueda, cada radio, cada estaca y cada tabla quedan donde están.
> No añadas nada fuera de la silueta ni quites nada de dentro. El fondo magenta
> (#FF00FF) queda magenta liso, también entre los radios y entre las estacas, sin
> sombras, sin degradados y sin halo. No pintes sombra en el suelo: la pone el juego.
>
> **Qué es.** Un carro de dos ruedas y varas, desenganchado, en la calle Mayor de
> Alcalá de Henares hacia 1620, de noche: las varas apoyadas en el suelo con sus
> puntas de hierro. Ruedas de radios con pinas de madera, llanta de hierro claveteada y
> cubo con aros; eje de madera; lecho de tablas y adrales de estacas con largueros.
> Carga: dos sacos de arpillera atados por la boca y una gavilla de paja atada por el
> medio. Madera vieja, reseca y gris, con barro seco en las ruedas y en la parte baja.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. Sombras casi negras y cálidas, nunca azul saturado; el detalle se concentra
> donde cae la luz. Pincelada visible pero contenida, empastes en las luces, veladuras
> en las sombras. Paleta terrosa; la luna enfría y apaga los colores. Nada de contornos
> negros, nada de aspecto de dibujos animados ni de render 3D limpio.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> única luz es la luna, fría y tenue, desde arriba a la izquierda de la imagen. Respeta
> las luces y sombras de la imagen 1.
>
> **Continuidad.** La madera y el hierro tienen que ser los de la imagen 3 (zapatas,
> puertas, pernios): la misma calle, la misma noche y la misma mano.
>
> **Rigor histórico.** Castilla, hacia 1620. La paja va en gavillas atadas, no en pacas
> prensadas. Nada de tornillos, ruedas de radios metálicos, neumáticos ni ballestas.
> Sin animales (el carro está desenganchado), personas, texto, firmas ni marcos.

---

## Dos barriles (`barriles`)

Adjuntos: imagen 1 `barriles_luz.png`, imagen 2 `barriles_maqueta.png`, imagen 3 la
casa de la hornacina ya aprobada.

> Adjunto tres imágenes. Imagen 1: render con la luz definitiva de un objeto de un
> videojuego isométrico. Imagen 2: el mismo objeto en arcilla gris, para que veas bien
> los volúmenes. Imagen 3: otra pieza de la misma calle, ya pintada: es la referencia
> de estilo, de color y de acabado.
>
> **Tarea.** Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la
> imagen 3, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente el
> mismo contorno. No añadas nada fuera de la silueta ni quites nada de dentro. El fondo
> magenta (#FF00FF) queda magenta liso, sin sombras, sin degradados y sin halo. No
> pintes sombra en el suelo: la pone el juego.
>
> **Qué es.** Dos barriles de duelas de madera, de pie en la calle Mayor de Alcalá de
> Henares hacia 1620, de noche, con aros de hierro oxidados y fondos de tablas. Madera
> vieja y oscura, con manchas de salmuera o de pez en las duelas y barro en la base:
> que parezcan barriles de salazón (sardinas, arenques) o de pez, no toneles de vino;
> en Castilla el vino viajaba en cueros (como los que acuchilla don Quijote en la
> venta) y se guardaba en tinajas.
>
> **Estilo.** Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José
> de Ribera y Francisco de Zurbarán, y de las escenas a la luz de una vela de Georges de
> La Tour. Sombras casi negras y cálidas, nunca azul saturado; el detalle se concentra
> donde cae la luz. Pincelada visible pero contenida, empastes en las luces, veladuras
> en las sombras. Paleta terrosa; la luna enfría y apaga los colores. Nada de contornos
> negros, nada de aspecto de dibujos animados ni de render 3D limpio.
>
> **Luz (no la cambies: es la misma en todas las piezas de la calle).** Es de noche. La
> única luz es la luna, fría y tenue, desde arriba a la izquierda de la imagen. Respeta
> las luces y sombras de la imagen 1.
>
> **Continuidad.** La madera y el hierro tienen que ser los de la imagen 3: la misma
> calle, la misma noche y la misma mano.
>
> **Rigor histórico.** Castilla, hacia 1620. Nada de etiquetas, marcas pintadas con
> letras, grifos ni tapones modernos. Sin personas, animales, texto, firmas ni marcos.

---

## Lo que no se pide a ChatGPT

- **El suelo** (empedrado de canto rodado con maestras, canalillo de losas, charcos):
  lo modelo yo piedra a piedra y ya lleva las sombras de todo.
- **El cadáver**: es un dibujo provisional; se pedirá como personaje suelto.
