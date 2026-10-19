using Godot;

namespace Alcala.Juego;

/// <summary>
/// Algo con lo que se puede interactuar: una persona, un objeto, una salida.
/// Necesita dos hijos:
///   «Zona» (Polygon2D): la superficie en pantalla donde se puede hacer clic.
///   «Llegada» (Marker2D): el punto del suelo al que camina el pesquisidor.
/// Al llegar, el juego arranca el nudo de Ink indicado en «Nudo».
/// </summary>
[GlobalClass]
public partial class PuntoDeInteres : Node2D
{
    [Export] public string Nombre { get; set; } = "";
    [Export] public string Nudo { get; set; } = "";
    /// <summary>Hacia dónde mira el pesquisidor al llegar. Si está vacío, mira al centro de la zona.</summary>
    [Export] public NodePath MirarA { get; set; } = new();

    private Polygon2D? zona;
    private Marker2D? llegada;

    public override void _Ready()
    {
        zona = GetNodeOrNull<Polygon2D>("Zona");
        llegada = GetNodeOrNull<Marker2D>("Llegada");
        if (!Engine.IsEditorHint() && zona is not null)
            zona.Visible = false;
        if (zona is null)
            GD.PushError($"El punto de interés «{Name}» no tiene hijo «Zona».");
    }

    public Vector2 Llegada => llegada?.GlobalPosition ?? GlobalPosition;

    public Vector2 Centro
    {
        get
        {
            if (zona is null || zona.Polygon.Length == 0)
                return GlobalPosition;
            Vector2 suma = Vector2.Zero;
            foreach (Vector2 p in zona.Polygon)
                suma += p;
            return zona.ToGlobal(suma / zona.Polygon.Length);
        }
    }

    public bool Contiene(Vector2 puntoGlobal)
    {
        if (zona is null)
            return false;
        return Geometry2D.IsPointInPolygon(zona.ToLocal(puntoGlobal), zona.Polygon);
    }

    public float Area
    {
        get
        {
            if (zona is null) return float.MaxValue;
            Vector2[] p = zona.Polygon;
            float a = 0;
            for (int i = 0; i < p.Length; i++)
            {
                Vector2 u = p[i], v = p[(i + 1) % p.Length];
                a += u.X * v.Y - v.X * u.Y;
            }
            return Mathf.Abs(a) / 2f;
        }
    }
}
