# Suelo de la calle Mayor: peticiones para ChatGPT

El suelo mide 3200 × 1800 px y ChatGPT no pinta tanto de una vez, así que se pide en
trozos de 1536 × 1024 con solape (`suelo_N_luz.png`). Lo magenta es donde van las casas.
`herramientas/procesar_suelo.py` encaja cada trozo, iguala el color entre ellos y los cose.

Solo hacen falta tres trozos: `suelo_1`, `suelo_3` y `suelo_4`. El `suelo_2` es casi todo
magenta y lo poco que se ve ya sale en los otros.

Adjuntos de cada petición: imagen 1 el trozo (`suelo_N_luz.png`), imagen 2 la casa de la
hornacina pintada. Pinta los tres en la misma conversación, uno detrás de otro, para que
ChatGPT mantenga la mano. Me los pasas como `suelo_N_pintada.png`.

## Trozo `suelo_1`

```text
Adjunto dos imágenes. Imagen 1: un trozo del suelo de una calle de un videojuego isométrico, renderizado con la luz definitiva; la parte magenta es donde van las casas. Imagen 2: una casa de esa misma calle ya pintada: es la referencia de estilo, de color y de acabado.

Tarea. Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la imagen 2, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente la misma composición: cada mancha de barro, cada charco, las roderas, el canalillo de losas del centro, las hileras de piedras mayores que cruzan la calle (maestras) y las sombras quedan donde están. El magenta (#FF00FF) queda magenta liso: no pintes nada encima ni lo bordees. Es uno de varios trozos de un suelo más grande que se van a coser: la luz tiene que ser pareja de un borde a otro, sin viñeteado, sin esquinas más oscuras, sin marco ni degradados.

Qué es. El suelo de la calle Mayor de Alcalá de Henares hacia 1620, de noche, después de llover. Empedrado de canto rodado (piedras de río redondeadas, grises, ocres y pardas) asentado en tierra, con hileras de piedras mayores de través y un canalillo de losas en medio de la calle por donde corre el agua. Muy sucio: barro espeso y oscuro que entierra las piedras a manchas, roderas de carro marcadas en el barro, charcos poco hondos de agua turbia que dejan ver las piedras del fondo y reflejan algo del cielo, pisadas, paja suelta, boñigas de las caballerías, alguna teja rota, hojas y restos de verdura. Este trozo es la parte de arriba a la izquierda de la calle: arriba, la calle sigue antes de la primera casa; a la derecha, el borde del soportal. La sombra alargada de abajo es la de un carro que el juego pone encima: píntala como sombra en el suelo, sin dibujar el carro.

Estilo. Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José de Ribera y Francisco de Zurbarán: sombras casi negras y cálidas, nunca azul saturado; el detalle y la textura se concentran donde cae la luz. Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras. Paleta terrosa: tierras, sienas, ocres, pardos y grises de piedra; la luna enfría y apaga los colores. Nada de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio.

Luz (no la cambies: es la misma en todo el suelo y en las casas). Es de noche. La única luz es la luna, fría y tenue, desde arriba a la izquierda de la imagen. Los charcos y el barro mojado tienen brillos sutiles. Respeta las sombras de la imagen 1: su dirección, su forma y dónde caen. No añadas luces nuevas.

Continuidad. La misma mano y la misma paleta que la imagen 2. Y entre los trozos del suelo: misma densidad de piedras, mismo color del barro y el mismo grado de suciedad en todos, para que no se note dónde se unen.

Rigor histórico. Castilla, hacia 1620. Nada de asfalto, bordillos modernos, alcantarillas, rejillas, tapas de registro, marcas de neumáticos, plástico, vidrio, latas ni colillas. Sin personas, animales, objetos sueltos grandes, texto, firmas ni marcos.
```

## Trozo `suelo_3`

```text
Adjunto dos imágenes. Imagen 1: un trozo del suelo de una calle de un videojuego isométrico, renderizado con la luz definitiva; la parte magenta es donde van las casas. Imagen 2: una casa de esa misma calle ya pintada: es la referencia de estilo, de color y de acabado.

Tarea. Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la imagen 2, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente la misma composición: cada mancha de barro, cada charco, las roderas, el canalillo de losas del centro, las hileras de piedras mayores que cruzan la calle (maestras) y las sombras quedan donde están. El magenta (#FF00FF) queda magenta liso: no pintes nada encima ni lo bordees. Es uno de varios trozos de un suelo más grande que se van a coser: la luz tiene que ser pareja de un borde a otro, sin viñeteado, sin esquinas más oscuras, sin marco ni degradados.

Qué es. El suelo de la calle Mayor de Alcalá de Henares hacia 1620, de noche, después de llover. Empedrado de canto rodado (piedras de río redondeadas, grises, ocres y pardas) asentado en tierra, con hileras de piedras mayores de través y un canalillo de losas en medio de la calle por donde corre el agua. Muy sucio: barro espeso y oscuro que entierra las piedras a manchas, roderas de carro marcadas en el barro, charcos poco hondos de agua turbia que dejan ver las piedras del fondo y reflejan algo del cielo, pisadas, paja suelta, boñigas de las caballerías, alguna teja rota, hojas y restos de verdura. Este trozo es la parte de abajo a la izquierda de la calle, la más amplia. La sombra alargada de arriba es la de un carro que el juego pone encima: píntala como sombra en el suelo, sin dibujar el carro.

Estilo. Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José de Ribera y Francisco de Zurbarán: sombras casi negras y cálidas, nunca azul saturado; el detalle y la textura se concentran donde cae la luz. Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras. Paleta terrosa: tierras, sienas, ocres, pardos y grises de piedra; la luna enfría y apaga los colores. Nada de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio.

Luz (no la cambies: es la misma en todo el suelo y en las casas). Es de noche. La única luz es la luna, fría y tenue, desde arriba a la izquierda de la imagen. Los charcos y el barro mojado tienen brillos sutiles. Respeta las sombras de la imagen 1: su dirección, su forma y dónde caen. No añadas luces nuevas.

Continuidad. La misma mano y la misma paleta que la imagen 2. Y entre los trozos del suelo: misma densidad de piedras, mismo color del barro y el mismo grado de suciedad en todos, para que no se note dónde se unen.

Rigor histórico. Castilla, hacia 1620. Nada de asfalto, bordillos modernos, alcantarillas, rejillas, tapas de registro, marcas de neumáticos, plástico, vidrio, latas ni colillas. Sin personas, animales, objetos sueltos grandes, texto, firmas ni marcos.
```

## Trozo `suelo_4`

```text
Adjunto dos imágenes. Imagen 1: un trozo del suelo de una calle de un videojuego isométrico, renderizado con la luz definitiva; la parte magenta es donde van las casas. Imagen 2: una casa de esa misma calle ya pintada: es la referencia de estilo, de color y de acabado.

Tarea. Repinta la imagen 1 como una pintura al óleo con el mismo estilo que la imagen 2, con el mismo tamaño de lienzo, la misma cámara isométrica y exactamente la misma composición: cada mancha de barro, cada charco, las roderas, el canalillo de losas del centro, las hileras de piedras mayores que cruzan la calle (maestras) y las sombras quedan donde están. El magenta (#FF00FF) queda magenta liso: no pintes nada encima ni lo bordees. Es uno de varios trozos de un suelo más grande que se van a coser: la luz tiene que ser pareja de un borde a otro, sin viñeteado, sin esquinas más oscuras, sin marco ni degradados.

Qué es. El suelo de la calle Mayor de Alcalá de Henares hacia 1620, de noche, después de llover. Empedrado de canto rodado (piedras de río redondeadas, grises, ocres y pardas) asentado en tierra, con hileras de piedras mayores de través y un canalillo de losas en medio de la calle por donde corre el agua. Muy sucio: barro espeso y oscuro que entierra las piedras a manchas, roderas de carro marcadas en el barro, charcos poco hondos de agua turbia que dejan ver las piedras del fondo y reflejan algo del cielo, pisadas, paja suelta, boñigas de las caballerías, alguna teja rota, hojas y restos de verdura. Este trozo es la parte de abajo a la derecha: arriba, el borde de los soportales; a la derecha, la bocacalle que sale tras la casa de la esquina. Las dos manchas oscuras redondas son las sombras de dos barriles que el juego pone encima: píntalas como sombras, sin dibujar los barriles.

Estilo. Pintura al óleo de tenebrismo español del siglo XVII, en la línea de José de Ribera y Francisco de Zurbarán: sombras casi negras y cálidas, nunca azul saturado; el detalle y la textura se concentran donde cae la luz. Pincelada visible pero contenida, empastes en las luces, veladuras en las sombras. Paleta terrosa: tierras, sienas, ocres, pardos y grises de piedra; la luna enfría y apaga los colores. Nada de contornos negros, nada de aspecto de dibujos animados ni de render 3D limpio.

Luz (no la cambies: es la misma en todo el suelo y en las casas). Es de noche. La única luz es la luna, fría y tenue, desde arriba a la izquierda de la imagen. Los charcos y el barro mojado tienen brillos sutiles. Respeta las sombras de la imagen 1: su dirección, su forma y dónde caen. No añadas luces nuevas.

Continuidad. La misma mano y la misma paleta que la imagen 2. Y entre los trozos del suelo: misma densidad de piedras, mismo color del barro y el mismo grado de suciedad en todos, para que no se note dónde se unen.

Rigor histórico. Castilla, hacia 1620. Nada de asfalto, bordillos modernos, alcantarillas, rejillas, tapas de registro, marcas de neumáticos, plástico, vidrio, latas ni colillas. Sin personas, animales, objetos sueltos grandes, texto, firmas ni marcos.
```
