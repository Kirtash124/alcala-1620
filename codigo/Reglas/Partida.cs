using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace Alcala.Reglas;

/// <summary>Todo lo que hace falta para reconstruir una partida guardada.</summary>
public sealed class EstadoPartida
{
    public int Version { get; set; } = 1;
    public string Lugar { get; set; } = "";
    public float JugadorX { get; set; }
    public float JugadorY { get; set; }
    public Dictionary<string, int> Facultades { get; set; } = new();
    public List<Pista> Pistas { get; set; } = new();
    /// <summary>Estado completo de Ink (variables, nudos visitados, opciones ya elegidas), en JSON.</summary>
    public string EstadoInk { get; set; } = "";
}

public static class Guardado
{
    private static readonly JsonSerializerOptions Opciones = new() { WriteIndented = true };

    public static EstadoPartida Capturar(string lugar, float x, float y, Ficha ficha, Pesquisa pesquisa, string estadoInk) => new()
    {
        Lugar = lugar,
        JugadorX = x,
        JugadorY = y,
        Facultades = Reglas.Facultades.Todas.ToDictionary(f => f.Nombre(), f => ficha[f]),
        Pistas = pesquisa.Pistas.ToList(),
        EstadoInk = estadoInk,
    };

    public static string AJson(EstadoPartida estado) => JsonSerializer.Serialize(estado, Opciones);

    public static EstadoPartida DesdeJson(string json) =>
        JsonSerializer.Deserialize<EstadoPartida>(json, Opciones)
        ?? throw new JsonException("El archivo de partida está vacío o dañado.");

    public static void Aplicar(EstadoPartida estado, Ficha ficha, Pesquisa pesquisa)
    {
        foreach ((string nombre, int valor) in estado.Facultades)
            ficha.Poner(Reglas.Facultades.Analizar(nombre), valor);
        pesquisa.Restaurar(estado.Pistas);
    }
}
