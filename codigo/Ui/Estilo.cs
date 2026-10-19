using Alcala.Reglas;
using Godot;

namespace Alcala.Ui;

/// <summary>Colores y recursos de la interfaz, en un solo sitio.</summary>
public static class Estilo
{
    public static readonly Color Papel = new(0.86f, 0.82f, 0.74f);
    public static readonly Color PapelApagado = new(0.62f, 0.58f, 0.52f);
    public static readonly Color Oro = new(0.85f, 0.70f, 0.42f);
    public static readonly Color Sangre = new(0.78f, 0.32f, 0.28f);
    public static readonly Color Exito = new(0.55f, 0.75f, 0.45f);
    public static readonly Color Fondo = new(0.055f, 0.05f, 0.05f, 0.94f);

    public static Color ColorFacultad(Facultad f) => f switch
    {
        Facultad.Entendimiento => new Color(0.56f, 0.70f, 0.85f),
        Facultad.Memoria => new Color(0.79f, 0.66f, 0.42f),
        _ => new Color(0.71f, 0.56f, 0.85f),
    };

    public static string Hex(Color c) => c.ToHtml(false);

    public static Font Fuente(string peso = "400-normal") =>
        GD.Load<Font>($"res://fuentes/eb-garamond-latin-{peso}.woff2");

    public static StyleBoxFlat Caja(Color fondo, Color? borde = null, int bordeIzq = 0)
    {
        var caja = new StyleBoxFlat { BgColor = fondo };
        if (borde is Color b)
        {
            caja.BorderColor = b;
            caja.BorderWidthLeft = bordeIzq;
        }
        caja.ContentMarginLeft = caja.ContentMarginRight = 0;
        return caja;
    }
}
