# Alcalá 1620

RPG detectivesco isométrico ambientado en Alcalá de Henares en 1620, en un siglo XVII
alternativo donde los demonios conviven con los vivos.

**Estado: prototipo técnico.** Una calle, un cadáver, un alguacil y una hornacina, con
arte y textos provisionales, para comprobar que todo el sistema funciona.

## Qué hay ya

- Escenario isométrico 2D con cámara que sigue al pesquisidor.
- Moverse con el ratón por una zona transitable, esquivando obstáculos.
- Objetos del escenario que tapan al personaje cuando pasa por detrás.
- Conversaciones al estilo de Disco Elysium, escritas en Ink.
- Tiradas de facultad (entendimiento, memoria, imaginativa) con probabilidad visible.
- Diario de pistas.
- Noche con velas y faroles que parpadean.
- Guardar y cargar partida.

## Instalar y abrir en Windows

1. Instala el **SDK de .NET 10**: <https://dotnet.microsoft.com/download/dotnet/10.0>
   (la versión «SDK x64», no solo el «Runtime»).
2. Descarga **Godot 4.7.1, versión .NET**: <https://godotengine.org/download/windows/>
   (el enlace que dice *.NET*). Es un ZIP: descomprímelo donde quieras; no se instala.
3. Descarga el proyecto. Con [GitHub Desktop](https://desktop.github.com/):
   *File → Clone repository → Kirtash124/alcala-1620*. Sin él: botón verde *Code →
   Download ZIP* en GitHub y descomprimir.
4. Abre Godot, pulsa *Importar*, elige el archivo `project.godot` de la carpeta del
   proyecto y ábrelo.
5. **La primera vez**, Godot mostrará errores en rojo (fuentes que aún no se han
   importado y el aviso «GodotInk could not be loaded»). Es normal: el código todavía no
   se ha compilado y Godot desactiva el complemento de Ink.
   1. Pulsa el botón **Build** (el martillo, arriba a la derecha) y espera.
   2. Ve a *Proyecto → Configuración del proyecto → Plugins* y activa **ink**.
   3. Cierra Godot y vuelve a abrir el proyecto. Ya no debería haber errores.

   Si usas GitHub Desktop, verás `project.godot` como modificado tras el paso 2: no lo
   subas, es el mismo estado que ya tiene el repositorio.
6. Pulsa **F5** (o el botón ▶) para jugar.

## Controles

| | |
|---|---|
| Clic izquierdo | andar, o examinar lo que hay bajo el cursor |
| 1 a 9 | elegir opción en una conversación |
| D | abrir o cerrar el diario |
| F5 / F9 | guardar / cargar partida |

## Carpetas

| | |
|---|---|
| `arte/` | imágenes del juego: piezas del escenario, suelo, personajes (provisionales) |
| `dialogos/` | conversaciones en Ink |
| `escenas/` | escenas de Godot: principal, lugares, personajes |
| `codigo/` | código C#: `Reglas` (sin Godot), `Juego`, `Ui` |
| `docs/` | guías: arte, Ink, montar escenarios, decisiones de diseño |
| `herramientas/` | scripts de Python para arte y escenas (el escenario se modela en Blender por código) |
| `pruebas/` | pruebas automáticas |

## Guías

- [Guía de arte con ChatGPT](docs/GUIA_ARTE.md)
- [Escribir los diálogos en Ink](docs/ESCRIBIR_EN_INK.md)
- [Montar un escenario nuevo](docs/MONTAR_UN_LUGAR.md)
- [Decisiones de diseño técnico](docs/DISENO.md)

## Créditos de terceros

- [GodotInk](https://github.com/paulloz/godot-ink) (MIT) y [Ink](https://github.com/inkle/ink) (MIT).
- Tipografía EB Garamond (SIL Open Font License), ver `fuentes/OFL-EBGaramond.txt`.
