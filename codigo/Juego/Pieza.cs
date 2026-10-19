using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace Alcala.Juego;

/// <summary>
/// Pieza del escenario dibujada aparte (una casa, un carro, unos barriles): una imagen
/// con la luz ya hecha, una huella que no se puede pisar y recortes que tapan a los
/// personajes cuando pasan por detrás.
///
/// - Con <see cref="Fondo"/> activo (casas), la imagen se dibuja siempre detrás de
///   los personajes; solo tapan sus recortes (las columnas).
/// - Sin él (objetos sueltos), la pieza entera se dibuja con recortes ordenados por
///   altura: un objeto largo en diagonal, como el carro, va partido en tiras, cada una
///   con su línea base, para que se pueda pasar por delante de una punta y por detrás
///   de la otra.
///
/// El nodo se coloca en el origen de la pieza (el punto del suelo que la sitúa en la
/// calle). Los datos los escribe herramientas/generar_calle_mayor.py a partir de las
/// fichas de herramientas/datos/piezas/.
/// </summary>
[Tool, GlobalClass]
public partial class Pieza : Node2D
{
    [Export] public Texture2D? Imagen { get; set; }
    /// <summary>Píxel de la imagen que cae en la posición del nodo.</summary>
    [Export] public Vector2 Ancla { get; set; }
    [Export] public bool Fondo { get; set; } = true;

    /// <summary>Huellas (obstáculos), en píxeles relativos al nodo, una detrás de otra.</summary>
    [Export] public Vector2[] HuellaPuntos { get; set; } = Array.Empty<Vector2>();
    [Export] public int[] HuellaTamanos { get; set; } = Array.Empty<int>();

    /// <summary>Recortes, en píxeles de la imagen, uno detrás de otro.</summary>
    [Export] public Vector2[] RecortesPuntos { get; set; } = Array.Empty<Vector2>();
    [Export] public int[] RecortesTamanos { get; set; } = Array.Empty<int>();
    /// <summary>Línea base de cada recorte (y en píxeles de la imagen).</summary>
    [Export] public float[] RecortesBases { get; set; } = Array.Empty<float>();

    public override void _Ready()
    {
        YSortEnabled = true;
        Construir();
    }

    private void Construir()
    {
        // En el editor, _Ready puede repetirse: se rehacen los hijos generados.
        foreach (Node hijo in GetChildren().Where(h => h.HasMeta("generado")))
        {
            RemoveChild(hijo);
            hijo.QueueFree();
        }
        if (Imagen is null)
            return;

        if (Fondo)
        {
            var dibujo = new Sprite2D
            {
                Name = "Imagen",
                Texture = Imagen,
                Centered = false,
                Offset = -Ancla,
                ZIndex = -1,
            };
            Generado(dibujo);
        }

        int inicio = 0;
        for (int k = 0; k < RecortesTamanos.Length; k++)
        {
            int n = RecortesTamanos[k];
            Vector2[] puntos = RecortesPuntos[inicio..(inicio + n)];
            inicio += n;
            float linea = RecortesBases[k] - Ancla.Y;
            var recorte = new Polygon2D
            {
                Name = $"Recorte{k}",
                Texture = Imagen,
                UV = puntos,
                Polygon = puntos.Select(p => p - Ancla - new Vector2(0, linea)).ToArray(),
                Position = new Vector2(0, linea),
            };
            Generado(recorte);
        }
    }

    private void Generado(Node2D nodo)
    {
        nodo.SetMeta("generado", true);
        AddChild(nodo);
    }

    /// <summary>Huellas expresadas en el espacio de <paramref name="referencia"/>.</summary>
    public IEnumerable<Vector2[]> Huellas(Node2D referencia)
    {
        Transform2D t = referencia.GlobalTransform.AffineInverse() * GlobalTransform;
        int inicio = 0;
        foreach (int n in HuellaTamanos)
        {
            yield return HuellaPuntos[inicio..(inicio + n)].Select(p => t * p).ToArray();
            inicio += n;
        }
    }
}
