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

## Gráficos: fondo plano + oclusores

El arte llega como imágenes planas (ChatGPT), sin mapas de profundidad. Por eso:

- **Fondo**: una imagen de 2560 × 1440 por escenario, cámara isométrica 2:1 común.
- **Oclusores**: recortes del propio fondo con una línea base. El motor los ordena por
  altura con los personajes, y así una columna tapa al pesquisidor si pasa por detrás.
- **Navegación**: polígono transitable + obstáculos, convertidos en malla al cargar.
- **Personajes**: dos dibujos (frente y espaldas) más espejo; caminar es un balanceo
  por código. Evita pedir a ChatGPT fotogramas de animación coherentes, que es
  justo lo que peor hace.
- **Luz**: tono general con `CanvasModulate` y luces que parpadean encima.

Prueba en curso (octubre de 2026): **maqueta con texturas**. La geometría del escenario
se construye por código (`herramientas/maqueta_calle_mayor.py`) y se recubre con texturas
repetibles hechas con ChatGPT (`arte/entrada/texturas/`). Garantiza cámara y escala
exactas, y la zona transitable y los oclusores salen de la misma geometría. Se compara
con un fondo pintado entero por ChatGPT antes de decidir el método definitivo. La escena
usa el fondo con texturas; `generar_calle_mayor.py --fondo provisional` vuelve al dibujo
provisional.

Limitaciones conocidas:

- Lo que la imagen no pinta no existe: no se puede «ver detrás» de un voladizo.
  Condiciona el diseño de los escenarios (ver `docs/GUIA_ARTE.md`).
- La línea base de los oclusores es horizontal; los muros largos en diagonal se
  dividen en tramos.
- Sin mapas de normales, las luces iluminan por igual y no marcan relieve. Se puede
  añadir más adelante generando mapas aproximados.

## Reglas: facultades de Huarte de San Juan

Atributos provisionales tomados del *Examen de ingenios para las ciencias* (1575):
entendimiento, memoria e imaginativa. Tiradas de 2d6 + facultad contra dificultad,
con doble seis y doble uno automáticos. Valores entre 1 y 6.

## Pruebas

- `pruebas/Reglas.Pruebas`: pruebas unitarias de las reglas (sin Godot).
- `pruebas/humo/PruebaHumo.tscn`: arranca el juego y lo juega solo con varias semillas
  de dados; comprueba rutas, conversaciones, pistas y guardado. Puede sacar capturas.
