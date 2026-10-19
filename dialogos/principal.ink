// =====================================================================
//  ALCALÁ 1620 · Punto de entrada de los diálogos
//
//  El juego no empieza por aquí: abre cada conversación por el nombre
//  de su nudo (alguacil, cadaver, hornacina, salida...).
//
//  CONVENCIONES (resumen; detalle en docs/ESCRIBIR_EN_INK.md)
//  · «NOMBRE: texto» es una línea dicha por alguien. Nombre en mayúsculas.
//  · Las facultades también hablan: «ENTENDIMIENTO: ...», «MEMORIA: ...»,
//    «IMAGINATIVA: ...».
//  · Una línea sin nombre es narración.
//  · Opción con tirada: * [Texto de la opción #tirada: entendimiento 10]
//    y dentro, ~ temp ok = tirada("entendimiento", 10)
//  · Pistas: ~ pista("id_unico", "Título", "Texto del diario")
//  · Opciones con * desaparecen al usarse; las de + se quedan.
//  · Cada conversación termina con -> DONE.
//
//  TEXTO PROVISIONAL: esta escena existe para probar el sistema.
// =====================================================================

EXTERNAL tirada(facultad_nombre, dificultad)
EXTERNAL facultad(nombre)
EXTERNAL pista(id, titulo, texto)

INCLUDE calle_mayor.ink

VAR vio_cera = false
VAR sabe_nombre = false
VAR huele_azufre = false
VAR alguacil_confia = false

// Menú de pruebas: solo se ve en Inky. El juego nunca empieza por aquí,
// sino por el nudo de cada conversación.
-> pruebas

=== pruebas ===
Menú de pruebas (solo Inky).
+ [El cadáver] -> cadaver
+ [La hornacina] -> hornacina
+ [El alguacil] -> alguacil
+ [La salida] -> salida


// ---------------------------------------------------------------------
//  Versiones de repuesto para probar los diálogos en Inky sin el juego.
//  En el juego se usan las de verdad (tiradas con dados, diario real).
// ---------------------------------------------------------------------

=== function tirada(facultad_nombre, dificultad)
~ temp dados = RANDOM(1, 6) + RANDOM(1, 6)
~ return dados + facultad(facultad_nombre) >= dificultad

=== function facultad(nombre)
{
- nombre == "entendimiento":
    ~ return 3
- nombre == "memoria":
    ~ return 2
- nombre == "imaginativa":
    ~ return 4
}
~ return 1

=== function pista(id, titulo, texto)
(Anotado en el diario: {titulo})
