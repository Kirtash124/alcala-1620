using System;

namespace Alcala.Reglas;

/// <summary>Fuente de dados. En el juego es aleatoria; en las pruebas, trucada.</summary>
public interface IDados
{
    /// <summary>Devuelve un entero entre 1 y 6.</summary>
    int D6();
}

public sealed class DadosAleatorios : IDados
{
    private readonly Random azar;

    public DadosAleatorios(int? semilla = null) => azar = semilla is int s ? new Random(s) : new Random();

    public int D6() => azar.Next(1, 7);
}

public readonly record struct ResultadoTirada(
    Facultad Facultad,
    int Dado1,
    int Dado2,
    int Bonificacion,
    int Dificultad,
    bool Exito)
{
    public int Total => Dado1 + Dado2 + Bonificacion;
    public bool Critico => Dado1 == 6 && Dado2 == 6;
    public bool Pifia => Dado1 == 1 && Dado2 == 1;
}

/// <summary>
/// Regla de tiradas: 2d6 + valor de la facultad, igual o mayor que la dificultad.
/// Doble seis siempre acierta y doble uno siempre falla, de modo que nada es
/// del todo seguro ni del todo imposible.
/// </summary>
public static class Tirada
{
    public static ResultadoTirada Resolver(Facultad facultad, int valor, int dificultad, IDados dados)
    {
        int a = dados.D6();
        int b = dados.D6();
        if (a is < 1 or > 6 || b is < 1 or > 6)
            throw new InvalidOperationException("Los dados deben devolver valores entre 1 y 6.");

        bool exito = (a, b) switch
        {
            (6, 6) => true,
            (1, 1) => false,
            _ => a + b + valor >= dificultad,
        };
        return new ResultadoTirada(facultad, a, b, valor, dificultad, exito);
    }

    /// <summary>Probabilidad exacta de éxito (0 a 1), contando las 36 combinaciones.</summary>
    public static double Probabilidad(int valor, int dificultad)
    {
        int aciertos = 0;
        for (int a = 1; a <= 6; a++)
        {
            for (int b = 1; b <= 6; b++)
            {
                bool exito = (a, b) switch
                {
                    (6, 6) => true,
                    (1, 1) => false,
                    _ => a + b + valor >= dificultad,
                };
                if (exito) aciertos++;
            }
        }
        return aciertos / 36.0;
    }

    /// <summary>Nombre de la dificultad, en la escala del juego.</summary>
    public static string NombreDificultad(int dificultad) => dificultad switch
    {
        <= 6 => "Trivial",
        <= 8 => "Sencilla",
        <= 10 => "Mediana",
        <= 12 => "Exigente",
        13 => "Formidable",
        14 => "Heroica",
        15 => "Legendaria",
        _ => "Milagrosa",
    };
}
