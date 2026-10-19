# Escribir los diálogos en Ink

Todos los diálogos están en `dialogos/`. Son archivos de texto en
[Ink](https://www.inklestudios.com/ink/), el lenguaje de inkle para historias ramificadas.

## Herramienta: Inky

Inky es el editor oficial de Ink, gratuito, para Windows, Mac y Linux. Abre
`dialogos/principal.ink` y a la derecha puedes jugar las conversaciones mientras escribes.
En Inky las tiradas se resuelven con dados al azar y las pistas se muestran entre
paréntesis; en el juego se usan los dados y el diario de verdad.

Al empezar, Inky muestra un **menú de pruebas** con todas las conversaciones. Cuando
escribas una nueva, añádela a ese menú (nudo `pruebas` de `principal.ink`). El juego
no usa ese menú: abre cada conversación directamente por su nudo.

## Cómo se conecta con el juego

- Cada cosa con la que se puede hablar o que se puede examinar tiene un **nudo**
  (`=== alguacil ===`). El juego lo abre por su nombre cuando el pesquisidor llega.
- Cada conversación termina con `-> DONE`.
- Las variables globales (`VAR vio_cera = false`) se guardan con la partida.

## Convenciones

### Quién habla

```
ALGUACIL: Vuesa merced llega tarde.
```

Nombre en mayúsculas, dos puntos y el texto. Una línea sin nombre es narración.
Las facultades del pesquisidor también hablan, con su color propio:

```
ENTENDIMIENTO: Bajo las uñas hay cera.
MEMORIA: Los colegiales de San Ildefonso visten beca.
IMAGINATIVA: La sombra cae hacia la vela.
```

### Opciones

```
* [Pregunta que desaparece al usarla.]
+ [Opción que se queda siempre, como «Despedirse».]
* {vio_cera} [Opción que solo aparece si vio_cera es verdadera.]
```

Lo que va entre corchetes es lo que ve el jugador en la lista; no se repite en el
registro.

### Tiradas

La etiqueta `#tirada:` en la opción hace que el juego muestre la facultad, la
dificultad y la probabilidad de éxito. Dentro, la función `tirada` tira los dados:

```
* [Examinar las manos. #tirada: entendimiento 10]
    ~ temp ok_manos = tirada("entendimiento", 10)
    { ok_manos:
        Texto si acierta.
    - else:
        Texto si falla.
    }
```

- Facultades: `entendimiento`, `memoria`, `imaginativa`.
- Se tiran 2d6 + facultad; hay que igualar o superar la dificultad. Doble seis siempre
  acierta y doble uno siempre falla.
- Dificultades: 6 trivial, 8 sencilla, 10 mediana, 12 exigente, 13 formidable,
  14 heroica, 15 legendaria, 16 milagrosa.
- Cada variable temporal (`temp`) necesita un nombre distinto dentro del mismo nudo:
  `ok_manos`, `ok_manteo`...
- Recomendación: que fallar también cuente algo. Un fallo que solo dice «no ves nada»
  es una puerta cerrada.

### Pistas

```
~ pista("cera", "Cera negra", "Texto completo que aparece en el diario.")
```

El primer dato es un identificador único, sin espacios ni tildes. Si la misma pista se
anota dos veces, el diario no la repite. Se puede anotar una versión pobre al fallar y
la buena al acertar con el mismo identificador: se queda la primera que se anote.

## Estilo

- Español peninsular. Tratamientos de época (vuesa merced, señor) sin abusar del
  arcaísmo: que se lea con fluidez.
- Sin rayas largas para los incisos: comas, puntos o paréntesis.
- Las líneas cortas leen mejor en el panel. Mejor tres líneas que un párrafo.
