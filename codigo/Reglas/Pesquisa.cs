using System;
using System.Collections.Generic;
using System.Linq;

namespace Alcala.Reglas;

/// <summary>Una pista anotada en el diario del pesquisidor.</summary>
public sealed record Pista(string Id, string Titulo, string Texto);

/// <summary>Diario de la pesquisa: las pistas reunidas, en el orden en que se hallaron.</summary>
public sealed class Pesquisa
{
    private readonly List<Pista> pistas = new();

    public IReadOnlyList<Pista> Pistas => pistas;

    public event Action<Pista>? PistaNueva;

    /// <summary>Anota una pista. Devuelve false si ya estaba (no se duplica).</summary>
    public bool Anotar(Pista pista)
    {
        if (string.IsNullOrWhiteSpace(pista.Id))
            throw new ArgumentException("La pista necesita un identificador.", nameof(pista));
        if (Tiene(pista.Id))
            return false;
        pistas.Add(pista);
        PistaNueva?.Invoke(pista);
        return true;
    }

    public bool Tiene(string id) => pistas.Any(p => p.Id == id);

    public void Restaurar(IEnumerable<Pista> guardadas)
    {
        pistas.Clear();
        pistas.AddRange(guardadas);
    }
}
