# Decisiones de diseño técnico

Registro de por qué el proyecto está hecho como está. Si una decisión cambia, se
anota aquí con la fecha y el motivo, sin borrar la anterior.

## Motor: Godot 4.7 (.NET)

- Licencia MIT, sin cuotas ni regalías.
- Escenas y recursos en texto plano: se pueden revisar en Git y editar sin el editor.
- Funciona en Windows, Mac y Linux, también en ARM.
- 2D sólido: orden por altura (*Y Sort*), luces 2D, polígonos de navegación.
- Se usa el renderizador **Compatibilidad** (OpenGL), suficiente para 2D y el que
  mejor funciona en gráficas modestas.
- Godot 4.8 está en beta (octubre de 2026). Pasaremos cuando salga estable; el
  proyecto ya apunta a .NET 10, que es lo que exige 4.8.

## Lenguaje: C#

La primera idea era GDScript. Se cambió al comprobar que las integraciones de diálogo
maduras para Godot (GodotInk, Yarn Spinner C#) requieren C#. Ventajas añadidas: tipos
estrictos, avisos tratados como errores y pruebas unitarias con herramientas estándar.

## Diálogos: Ink + GodotInk

- Ink (inkle) es un lenguaje maduro, usado en juegos publicados, con editor gratuito
  (Inky) para escribir y probar sin abrir el juego.
- GodotInk compila los `.ink` al importarlos y usa el motor oficial de Ink en C#.
- Descartados: Yarn Spinner para GDScript (alfa, sus autores desaconsejan usarlo en un
  juego publicado), Yarn Spinner C# (versión 0.3, sin soporte oficial), Dialogic 2
  (alfa con cambios incompatibles entre versiones), articy:draft (herramienta gráfica,
  difícil de mantener en Git).
- Inconveniente asumido: traducir Ink requiere herramientas externas. No hay versión
  en inglés prevista de inicio.

## Gráficos: piezas renderizadas en Blender + repintado

**Octubre de 2026.** Los escenarios se componen de piezas (cada casa, cada objeto fijo)
que se **modelan por código en Blender** (`herramientas/blender/`, `herramientas/kit_calle_mayor.py`)
con geometría de verdad y se **renderizan con la cámara exacta del juego** y la luz de
la escena ya hecha. ChatGPT repinta cada pieza encima, sin mover contornos, y
`herramientas/procesar_pieza.py` comprueba la silueta y la encaja. La pintura se
respeta tal cual (decisión de Esteban con la primera casa, más cálida y clara que el
render); si alguna pieza se desvía de la noche de las demás, `--luz render` conserva
su textura y le impone la luz del render.

- **Cámara**: ortográfica, acimut 45°, elevación 30°, 108,05 px por metro en el plano de
  la cámara. Reproduce la proyección 2:1 del juego (comprobado punto a punto).
- **Luz**: luna fría desde arriba a la izquierda y rasante a las fachadas, para que el
  relieve se lea y los soportales queden en penumbra; velas y ventanas encendidas con
  luz cálida. Toda la calle se construye a la vez: al renderizar una pieza, las demás
  hacen sombra y rebotan luz, y las que quedan delante la recortan (holdout), así que
  cada imagen contiene solo lo que de verdad se ve.
- **Orden de dibujo**: las casas van detrás de los personajes y solo tapan sus columnas
  (recortes con la silueta exacta y su línea base). Los objetos sueltos se dibujan en
  tiras verticales, cada una con su línea base.
- **Navegación**: polígono transitable + huellas de las piezas, convertidos en malla al
  cargar.
- **Personajes**: dos dibujos (frente y espaldas) más espejo; caminar es un balanceo
  por código. El lugar les aplica un tono (`TonoPersonajes`) para encajarlos en la luz.
- **Luces del motor**: solo para el temblor de las velas y el farol del alguacil.

Por qué: la primera prueba (un fondo plano pintado entero por ChatGPT con oclusores
dibujados a mano) y la segunda (maqueta por código recubierta con texturas de ChatGPT)
daban una calidad insuficiente. ChatGPT no mantiene cámara ni escala entre imágenes, y
las texturas planas sobre cajas parecían de cartón. Con geometría de verdad, cada
teja, tabla, clavo y balaustre existe, las sombras son correctas y la pintura de
ChatGPT solo tiene que añadir mano de pintor.

Requisitos para regenerar el arte: Python 3.13 con `bpy` (Blender como módulo),
NumPy, SciPy, scikit-image y Pillow. El juego no los necesita.

Limitaciones conocidas:

- Lo que la imagen no pinta no existe: no se puede «ver detrás» de un voladizo. Bajo el
  soportal solo se ve el muro hasta 1,76 m; lo examinable tiene que estar por debajo.
- La línea base de cada recorte es horizontal: un objeto largo en diagonal se parte en
  tiras, y en el borde entre dos tiras el personaje puede quedar medio tapado un instante.
- Sin mapas de normales, las luces del motor iluminan por igual; por eso la luz va
  pintada en las piezas y las del motor solo tiemblan.

### Decisiones anteriores (sustituidas)

- **Fondo plano + oclusores** (septiembre de 2026): una imagen de 2560 × 1440 por
  escenario pintada por ChatGPT, con recortes del propio fondo dibujados a mano para
  tapar al personaje. Se abandonó porque ChatGPT no respeta cámara ni escala.
- **Maqueta con texturas** (octubre de 2026): geometría por código recubierta con
  texturas repetibles de ChatGPT. Se abandonó por calidad: parecía de cartón.

## Reglas: facultades de Huarte de San Juan

Atributos provisionales tomados del *Examen de ingenios para las ciencias* (1575):
entendimiento, memoria e imaginativa. Tiradas de 2d6 + facultad contra dificultad,
con doble seis y doble uno automáticos. Valores entre 1 y 6.

## Pruebas

- `pruebas/Reglas.Pruebas`: pruebas unitarias de las reglas (sin Godot).
- `pruebas/humo/PruebaHumo.tscn`: arranca el juego y lo juega solo con varias semillas
  de dados; comprueba rutas, conversaciones, pistas y guardado. Puede sacar capturas.
