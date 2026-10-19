using System;

namespace Alcala.Juego;

/// <summary>Trayectoria de un pie respecto al cuerpo durante un ciclo completo.</summary>
public static class CicloMarcha
{
    public const float FraccionApoyo = 0.6f;

    public readonly record struct Pie(float Avance, float Elevacion);

    public static Pie Evaluar(float fase, float longitudCiclo, float alturaPaso)
    {
        fase -= MathF.Floor(fase);
        float extremo = longitudCiclo * FraccionApoyo / 2f;
        if (fase < FraccionApoyo)
        {
            // Mientras el cuerpo avanza, el pie retrocede exactamente la misma
            // distancia local. Su punto de apoyo permanece fijo en el mundo.
            return new Pie(extremo - longitudCiclo * fase, 0);
        }

        float t = (fase - FraccionApoyo) / (1f - FraccionApoyo);
        float suave = t * t * (3f - 2f * t);
        return new Pie(-extremo + 2f * extremo * suave,
                       alturaPaso * MathF.Sin(MathF.PI * t));
    }
}
