# Alcalá 1620 · notas para trabajar en el proyecto

RPG detectivesco isométrico 2D (estilo Disco Elysium) en Alcalá de Henares, 1620
alternativo con demonios. Autor y director creativo: Esteban. El código lo escribe
Claude; el arte lo genera Esteban con ChatGPT; los diálogos los escribe Esteban
(los actuales son provisionales).

Lee `docs/DISENO.md` antes de cambiar nada estructural.

## Pila

- Godot **4.7.1 .NET**, C# sobre **.NET 10**, renderizador Compatibilidad.
- Diálogos en **Ink** (`dialogos/`), compilados al importar por **GodotInk** (`addons/GodotInk`, no modificar).
- Python 3.13 + `bpy` (Blender como módulo) + NumPy, SciPy, scikit-image y Pillow para
  las herramientas de arte (`herramientas/`). El escenario se modela y renderiza por
  código en Blender (`herramientas/blender/`).

## Órdenes

Con `G` apuntando al ejecutable de Godot 4.7.1 mono:

```bash
dotnet build Alcala1620.csproj                       # compilar el juego
$G --headless --path . --import                      # importar recursos y compilar Ink
dotnet test pruebas/Reglas.Pruebas                   # pruebas unitarias de reglas
$G --headless --path . res://pruebas/humo/PruebaHumo.tscn            # prueba de humo (código de salida 0 = bien)
xvfb-run -a -s "-screen 0 1920x1080x24" $G --path . --rendering-driver opengl3 \
    --resolution 1920x1080 res://pruebas/humo/PruebaHumo.tscn -- --capturas=$PWD/pruebas/salida/capturas
python3 herramientas/kit_calle_mayor.py [--solo casa_3] [--rapido] [--sin-render]   # modela y renderiza piezas y suelo (~1 h)
python3 herramientas/generar_calle_mayor.py         # escena CalleMayor.tscn a partir de las fichas
python3 herramientas/procesar_pieza.py casa_3 pintada.png   # mete una pieza repintada por ChatGPT
python3 herramientas/arte_provisional.py            # personajes y objetos provisionales
python3 herramientas/plantillas_arte.py              # plantillas para ChatGPT (docs/arte)
python3 herramientas/procesar_arte.py fondo|figura entrada.png salida.png
```

Antes de dar algo por terminado: compilar, pruebas unitarias, prueba de humo y, si
cambia algo visible, capturas revisadas a ojo.

## Estructura del código

- `codigo/Reglas/`: lógica pura sin Godot (facultades, tiradas, pistas, guardado,
  análisis de líneas y etiquetas de Ink). Se prueba con xUnit.
- `codigo/Juego/`: nodos de Godot. `ControlJuego` dirige la partida; `Lugar`, `Pieza`
  (casa u objeto renderizado: imagen, huella, recortes), `Personaje`, `Oclusor`,
  `PuntoDeInteres`, `Parpadeo`, `Camara`; `Narrador` es el puente con Ink (funciones
  externas `tirada`, `facultad`, `pista`).
- `herramientas/blender/`: `base` (cámara del juego, geometría, render), `materiales`
  (procedurales), `modelos` (columna, zapata, puerta, balcón, teja árabe...).
- `codigo/Ui/`: interfaz construida por código (`PanelDialogo`, `Diario`, `Hud`, `Estilo`).

## Convenciones

- Identificadores, comentarios, documentación y textos en **español peninsular**.
- En textos y documentación, **sin rayas largas** (—): comas, puntos o paréntesis.
- Avisos del compilador = errores (salvo el CS0108 de GodotInk).
- Proyección isométrica 2:1 fija: 1 m de suelo = 76,4 px horizontales, 1 m de altura =
  93,5 px, luz de arriba a la izquierda (`herramientas/isometria.py`). Todo el arte la respeta.
- Escenarios por piezas: casas y objetos renderizados en Blender con la cámara del juego;
  suelo de 3200 × 1800. Personajes: dos dibujos (frente SE, espaldas NE) + espejo.
- En Blender se modela en nuestras coordenadas y se convierte con `B(x, y, z) = (x, -y, z)`.
  Nada de caras coplanarias entre piezas (se hacen sombra: franjas negras).
- Los polígonos de `Oclusor` se dibujan con el nodo en el origen, en coordenadas del fondo.
- Ink: «NOMBRE: texto» para hablar; opciones con `#tirada: facultad N`; pistas con
  `~ pista(id, título, texto)`; cada conversación acaba en `-> DONE`; los `temp` deben
  tener nombres distintos dentro de un mismo nudo.
- Rigor histórico: nada de anacronismos (en 1620 no hay serenos ni golilla; sí
  lechuguilla, corchetes, alguaciles con vara, fuero universitario). Ante la duda,
  documentarse antes de escribir.
