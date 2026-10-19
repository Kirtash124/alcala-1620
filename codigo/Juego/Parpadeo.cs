using Godot;

namespace Alcala.Juego;

/// <summary>
/// Luz de vela o de farol: tiembla de forma irregular, nunca en un ciclo regular.
/// Si no se le asigna textura, genera un degradado radial suave.
/// </summary>
[GlobalClass]
public partial class Parpadeo : PointLight2D
{
    [Export] public float EnergiaBase { get; set; } = 1.1f;
    [Export] public float Temblor { get; set; } = 0.18f;
    [Export] public float Rapidez { get; set; } = 1f;

    private float t;
    private float semilla;

    public override void _Ready()
    {
        semilla = (float)GD.RandRange(0, 1000);
        Texture ??= DegradadoRadial();
    }

    public override void _Process(double delta)
    {
        t += (float)delta * Rapidez;
        // Suma de senos de frecuencias que no encajan entre sí: no se nota el ciclo.
        float n = Mathf.Sin(t * 7.3f + semilla) * 0.5f
                + Mathf.Sin(t * 13.1f + semilla * 1.7f) * 0.3f
                + Mathf.Sin(t * 2.9f + semilla * 0.3f) * 0.2f;
        Energy = EnergiaBase * (1f + n * Temblor);
    }

    public static GradientTexture2D DegradadoRadial()
    {
        var gradiente = new Gradient();
        gradiente.SetColor(0, new Color(1, 1, 1, 1));
        gradiente.SetColor(1, new Color(1, 1, 1, 0));
        gradiente.AddPoint(0.35f, new Color(1, 1, 1, 0.55f));
        gradiente.AddPoint(0.7f, new Color(1, 1, 1, 0.12f));
        return new GradientTexture2D
        {
            Gradient = gradiente,
            Width = 512,
            Height = 512,
            Fill = GradientTexture2D.FillEnum.Radial,
            FillFrom = new Vector2(0.5f, 0.5f),
            FillTo = new Vector2(1f, 0.5f),
        };
    }
}
