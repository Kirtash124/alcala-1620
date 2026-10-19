using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace Alcala.Reglas;

/// <summary>Una línea de diálogo ya separada en hablante y texto.</summary>
public readonly record struct LineaDialogo(string? Hablante, string Texto)
{
    public bool EsNarracion => Hablante is null;

    // Convención de escritura en Ink: «ALGUACIL: Texto». El nombre va en mayúsculas.
    private static readonly Regex Patron = new(
        @"^\s*(?<nombre>[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ ]{0,29}):\s*(?<texto>.+)$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);

    public static LineaDialogo Analizar(string linea)
    {
        string limpia = linea.Trim();
        Match m = Patron.Match(limpia);
        if (m.Success)
            return new LineaDialogo(m.Groups["nombre"].Value.Trim(), m.Groups["texto"].Value.Trim());
        return new LineaDialogo(null, limpia);
    }
}

/// <summary>Una comprobación de facultad declarada en una opción de Ink con «#tirada: facultad dificultad».</summary>
public readonly record struct ComprobacionOpcion(Facultad Facultad, int Dificultad)
{
    private static readonly Regex Patron = new(
        @"^\s*tirada\s*:\s*(?<facultad>[\p{L}]+)\s+(?<dificultad>\d{1,2})\s*$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);

    public static ComprobacionOpcion? DesdeEtiquetas(IEnumerable<string> etiquetas)
    {
        foreach (string etiqueta in etiquetas)
        {
            Match m = Patron.Match(etiqueta);
            if (m.Success)
                return new ComprobacionOpcion(
                    Facultades.Analizar(m.Groups["facultad"].Value),
                    int.Parse(m.Groups["dificultad"].Value));
        }
        return null;
    }

    /// <summary>Texto del prefijo que ve el jugador: «[Entendimiento · Mediana 10 · 72 %]».</summary>
    public string Prefijo(Ficha ficha)
    {
        int porcentaje = (int)Math.Round(Tirada.Probabilidad(ficha[Facultad], Dificultad) * 100);
        return $"[{Facultad.Nombre()} · {Tirada.NombreDificultad(Dificultad)} {Dificultad} · {porcentaje} %]";
    }
}

public static class Etiquetas
{
    /// <summary>Busca una etiqueta «clave: valor» y devuelve el valor.</summary>
    public static string? Valor(IEnumerable<string> etiquetas, string clave) =>
        etiquetas
            .Select(e => e.Split(':', 2))
            .Where(partes => partes.Length == 2 && partes[0].Trim().Equals(clave, StringComparison.OrdinalIgnoreCase))
            .Select(partes => partes[1].Trim())
            .FirstOrDefault();
}
