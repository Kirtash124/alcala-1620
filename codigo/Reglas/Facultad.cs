using System;
using System.Collections.Generic;

namespace Alcala.Reglas;

/// <summary>
/// Las tres potencias del alma racional según Juan Huarte de San Juan,
/// Examen de ingenios para las ciencias (Baeza, 1575). Huarte estudió medicina
/// en Alcalá y ligaba cada potencia a una cualidad del cerebro:
/// entendimiento a la sequedad, memoria a la humedad e imaginativa al calor.
/// Son los atributos provisionales del pesquisidor.
/// </summary>
public enum Facultad
{
    Entendimiento,
    Memoria,
    Imaginativa,
}

public static class Facultades
{
    public static readonly IReadOnlyList<Facultad> Todas =
        new[] { Facultad.Entendimiento, Facultad.Memoria, Facultad.Imaginativa };

    public static string Nombre(this Facultad f) => f switch
    {
        Facultad.Entendimiento => "Entendimiento",
        Facultad.Memoria => "Memoria",
        Facultad.Imaginativa => "Imaginativa",
        _ => throw new ArgumentOutOfRangeException(nameof(f)),
    };

    /// <summary>Acepta el nombre tal como se escribe en Ink, sin distinguir mayúsculas ni tildes.</summary>
    public static Facultad Analizar(string texto)
    {
        string limpio = Texto.SinTildes(texto).Trim().ToLowerInvariant();
        return limpio switch
        {
            "entendimiento" => Facultad.Entendimiento,
            "memoria" => Facultad.Memoria,
            "imaginativa" or "imaginacion" => Facultad.Imaginativa,
            _ => throw new FormatException($"Facultad desconocida: «{texto}»"),
        };
    }
}

/// <summary>Valores de las facultades de un personaje.</summary>
public sealed class Ficha
{
    public const int Minimo = 1;
    public const int Maximo = 6;

    private readonly Dictionary<Facultad, int> valores = new();

    public Ficha(int entendimiento, int memoria, int imaginativa)
    {
        Poner(Facultad.Entendimiento, entendimiento);
        Poner(Facultad.Memoria, memoria);
        Poner(Facultad.Imaginativa, imaginativa);
    }

    public int this[Facultad f] => valores[f];

    public void Poner(Facultad f, int valor)
    {
        if (valor < Minimo || valor > Maximo)
            throw new ArgumentOutOfRangeException(nameof(valor), $"{f.Nombre()} debe estar entre {Minimo} y {Maximo}.");
        valores[f] = valor;
    }

    /// <summary>Ficha inicial del pesquisidor en el prototipo.</summary>
    public static Ficha Pesquisidor() => new(entendimiento: 3, memoria: 2, imaginativa: 4);
}
