using System.Linq;
using Godot;

namespace Alcala.Juego;

/// <summary>
/// Trozo del fondo que debe tapar a los personajes cuando pasan por detrás
/// (una columna, un carro, una esquina). Es una copia recortada del propio fondo.
///
/// Cómo se usa en el editor:
///   1. Crear un Polygon2D con este script dentro del nodo «Entidades» del lugar,
///      sin moverlo del origen.
///   2. Ponerle como textura la imagen de fondo del lugar.
///   3. Dibujar el polígono alrededor del objeto con la herramienta de polígonos.
///   4. La línea base es la altura (y) del punto del objeto que toca el suelo más
///      cerca de la cámara. Si se deja en -1 se usa el punto más bajo del polígono.
/// Un personaje cuyos pies queden por encima de la línea base se dibuja detrás.
/// </summary>
[GlobalClass]
public partial class Oclusor : Polygon2D
{
    [Export] public float LineaBase { get; set; } = -1f;

    public override void _Ready()
    {
        if (Engine.IsEditorHint() || Polygon.Length < 3)
            return;

        Vector2 origen = Position;
        Vector2[] absolutos = Polygon.Select(p => p + origen).ToArray();
        float baseY = LineaBase >= 0 ? LineaBase : absolutos.Max(p => p.Y);

        // La textura se sigue leyendo en coordenadas del fondo...
        if (UV.Length != Polygon.Length)
            UV = absolutos;
        // ...pero el nodo se coloca en su línea base para que el orden por altura funcione.
        Position = new Vector2(0, baseY);
        Polygon = absolutos.Select(p => p - Position).ToArray();
        Color = Colors.White;
    }
}
