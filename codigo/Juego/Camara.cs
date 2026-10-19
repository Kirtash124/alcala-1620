using Godot;

namespace Alcala.Juego;

/// <summary>Cámara que sigue al pesquisidor sin salirse del fondo.</summary>
[GlobalClass]
public partial class Camara : Camera2D
{
    public Node2D? Objetivo { get; set; }

    /// <summary>Desplazamiento horizontal deseado (se usa para dejar sitio al panel de diálogo).</summary>
    public float DesplazamientoX { get; set; }

    public override void _Ready()
    {
        PositionSmoothingEnabled = true;
        PositionSmoothingSpeed = 4.5f;
    }

    public void Encuadrar(Rect2 limites)
    {
        LimitLeft = (int)limites.Position.X;
        LimitTop = (int)limites.Position.Y;
        LimitRight = (int)limites.End.X;
        LimitBottom = (int)limites.End.Y;
        if (Objetivo is not null)
        {
            GlobalPosition = Objetivo.GlobalPosition;
            ResetSmoothing();
        }
    }

    public override void _Process(double delta)
    {
        if (Objetivo is not null)
            GlobalPosition = Objetivo.GlobalPosition + new Vector2(0, -80);
        Offset = Offset.Lerp(new Vector2(DesplazamientoX, 0), 1f - Mathf.Exp(-(float)delta * 4f));
    }
}
