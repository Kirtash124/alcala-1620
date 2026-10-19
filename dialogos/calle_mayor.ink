// =====================================================================
//  CALLE MAYOR, JUNTO A LOS SOPORTALES · noche
//  Escena de prueba. Texto provisional, para reescribir.
// =====================================================================


=== alguacil ===
{ alguacil > 1: -> de_nuevo }
El alguacil te alumbra la cara con el farol antes de apartar la vara.
ALGUACIL: Vuesa merced será el pesquisidor que manda el corregidor. Llega tarde. La ronda lo halló pasada la medianoche y ya han dado las dos en la Magistral.
ALGUACIL: Yo no he tocado nada. Ni pienso.
-> preguntas

= de_nuevo
ALGUACIL: ¿Más preguntas? Pregunte, que la noche no se va a acabar sola.
-> preguntas

= preguntas
* [¿Quién es el muerto?]
    ALGUACIL: Gaspar de Ribera, bachiller en Artes. Estudiante, por el manteo. Vivía de pupilo en una casa de la calle de Santiago.
    ALGUACIL: Siendo estudiante, el rector querrá meter las manos en esto antes de que amanezca. Ya sabe vuesa merced cómo guardan su fuero los de la Universidad.
    ~ sabe_nombre = true
    ~ pista("nombre", "El muerto", "Gaspar de Ribera, bachiller en Artes. Vivía de pupilo en la calle de Santiago. Al ser estudiante, el rector reclamará el caso para su jurisdicción.")
    -> preguntas
* [¿Quién lo encontró?]
    ALGUACIL: La ronda. Dos corchetes y yo. Venían de la plaza del Mercado y lo vieron tendido bajo el soportal, con la vela de la hornacina todavía encendida.
    ALGUACIL: Una vieja asomada a ese balcón dice que oyó reír a alguien. A la una. Que no era risa de hombre.
    -> preguntas
* {vio_cera} [Hay cera negra junto a la mano del muerto.]
    El alguacil se santigua sin darse cuenta de que lo hace.
    ALGUACIL: Eso no lo he visto yo. Y si vuesa merced es prudente, tampoco lo ha visto.
    -> preguntas
* [Su farol tiembla más que su mano. ¿De qué tiene miedo? #tirada: imaginativa 12]
    ~ temp ok_miedo = tirada("imaginativa", 12)
    { ok_miedo:
        IMAGINATIVA: Mira cómo evita mirar la esquina de los barriles. No es al muerto a quien teme.
        El alguacil baja la voz.
        ALGUACIL: Cuando llegamos, había alguien junto a esos barriles. Alto. Se fue hacia la plaza sin hacer ruido. Y el farol no le sacaba sombra, señor. Ninguna.
        ~ alguacil_confia = true
        ~ pista("sin_sombra", "Una figura sin sombra", "El alguacil vio a alguien alto junto a los barriles al llegar la ronda. Se marchó hacia la plaza del Mercado. Asegura que el farol no le hacía sombra.")
    - else:
        ALGUACIL: ¿Miedo? Hace frío, y llevo de ronda desde las diez. Pregunte lo que tenga que preguntar.
    }
    -> preguntas
+ [Despedirse.]
    ALGUACIL: Aquí estaré, hasta que vengan por el cuerpo.
    -> DONE


=== cadaver ===
{ cadaver == 1:
    Un hombre joven tendido boca arriba sobre las losas, el manteo abierto como un ala. Tiene los ojos entornados, como si le hubieran interrumpido a mitad de una frase.
- else:
    El muerto sigue ahí. La vela de la hornacina hace que su sombra se mueva aunque él no se mueva.
}
-> examinar

= examinar
* [Examinar las manos. #tirada: entendimiento 10]
    ~ temp ok_manos = tirada("entendimiento", 10)
    { ok_manos:
        ENTENDIMIENTO: Bajo las uñas hay cera. Negra, todavía blanda. No se la manchó al caer: la estuvo rascando de algún sitio, con prisa.
        ~ pista("cera", "Cera negra", "Bajo las uñas del muerto hay cera negra, aún blanda. La rascó de algún sitio poco antes de morir. Hay gotas iguales en el suelo, junto a la mano.")
    - else:
        Te manchas los dedos de algo negro y pegajoso. Las gotas forman un pequeño reguero junto a la mano. No sabes qué es, pero no es sangre.
        ~ pista("cera", "Gotas negras", "Gotas negras y pegajosas junto a la mano del muerto. No es sangre.")
    }
    ~ vio_cera = true
    -> examinar
* [Buscar en el manteo. #tirada: memoria 8]
    ~ temp ok_manteo = tirada("memoria", 8)
    { ok_manteo:
        MEMORIA: Los colegiales de San Ildefonso visten beca. Este no la lleva. Era manteísta, de los que estudian sin colegio y viven de pupilos. Pobre, entonces.
        En un bolsillo interior, un papel doblado con una sola palabra escrita a tinta: «Sábado».
        ~ pista("sabado", "Una nota", "En el manteo, un papel con una sola palabra: «Sábado». El muerto era manteísta, estudiante sin colegio.")
    - else:
        Unas monedas de vellón, un rosario de cuentas de madera y un papel tan arrugado que no consigues leerlo con esta luz.
    }
    -> examinar
* [Mirar su sombra. #tirada: imaginativa 12]
    ~ temp ok_sombra = tirada("imaginativa", 12)
    { ok_sombra:
        IMAGINATIVA: La vela está a su izquierda. La sombra debería caer a la derecha. Cae hacia la vela.
        IMAGINATIVA: Como si algo tirase de ella.
        ~ pista("sombra", "La sombra que no obedece", "La sombra del cadáver apunta hacia la vela de la hornacina, en contra de la luz.")
    - else:
        Te quedas mirando demasiado rato. Te escuecen los ojos y no ves nada que no sea un muerto.
    }
    -> examinar
+ [Dejarlo estar.]
    -> DONE


=== hornacina ===
Una hornacina encalada en el muro del soportal, con una estampa de San Diego y una vela blanca a medio consumir. Por debajo de la vela, en el borde de piedra, la cera no es blanca.
-> mirar

= mirar
* [Recordar quién cuida de la hornacina. #tirada: memoria 10]
    ~ temp ok_cerero = tirada("memoria", 10)
    { ok_cerero:
        MEMORIA: La vela la pone cada noche la mujer del cerero de la esquina. Velas blancas, de las que vende. Nunca negras.
        ~ pista("cerero", "El cerero de la esquina", "La mujer del cerero enciende cada noche la vela de la hornacina. Solo usan velas blancas.")
    - else:
        Hay una cofradía detrás de esto, seguro. Ahora mismo no recuerdas cuál.
    }
    -> mirar
* [Oler la cera negra.]
    Huele a sebo, a humo y, por debajo, a algo agrio que te raspa la garganta. Azufre.
    ~ huele_azufre = true
    { vio_cera:
        ENTENDIMIENTO: Es la misma cera que tenía el muerto bajo las uñas. La rascó de aquí.
        ~ pista("cera_hornacina", "De dónde salió la cera", "La cera negra de las uñas del muerto procede de la hornacina. Huele a azufre.")
    }
    -> mirar
+ [Apartarte.]
    -> DONE


=== salida ===
La calle sigue hacia la plaza del Mercado. Más allá, todo está a oscuras.
Aquí termina el prototipo.
-> DONE
