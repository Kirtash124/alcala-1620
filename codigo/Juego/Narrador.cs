using System;
using System.Collections.Generic;
using System.Linq;
using Alcala.Reglas;
using Godot;
using GodotInk;

namespace Alcala.Juego;

/// <summary>Cada cosa que el panel de diálogo tiene que mostrar, en orden.</summary>
public abstract record Entrada;
public sealed record EntradaLinea(LineaDialogo Linea) : Entrada;
public sealed record EntradaTirada(ResultadoTirada Resultado) : Entrada;
public sealed record EntradaPista(Pista Pista) : Entrada;

public sealed record OpcionVista(int Indice, string Texto, ComprobacionOpcion? Comprobacion);

/// <summary>Lo que sale de avanzar la historia hasta la siguiente decisión.</summary>
public sealed record Paso(IReadOnlyList<Entrada> Entradas, IReadOnlyList<OpcionVista> Opciones)
{
    public bool Terminado => Opciones.Count == 0;
}

/// <summary>
/// Puente entre Ink y el juego. Ink decide qué se dice; el juego resuelve las
/// tiradas, anota pistas y guarda el estado.
///
/// Funciones que Ink puede llamar (declaradas con EXTERNAL en dialogos/principal.ink):
///   tirada(facultad, dificultad) -> bool   resuelve 2d6 + facultad
///   facultad(nombre) -> int                valor actual de una facultad
///   pista(id, titulo, texto)               anota una pista en el diario
/// </summary>
public sealed class Narrador
{
    private readonly InkStory historia;
    private readonly Ficha ficha;
    private readonly Pesquisa pesquisa;
    private readonly IDados dados;
    private readonly List<Entrada> pendientes = new();

    public Narrador(InkStory historia, Ficha ficha, Pesquisa pesquisa, IDados dados)
    {
        this.historia = historia;
        this.ficha = ficha;
        this.pesquisa = pesquisa;
        this.dados = dados;

        historia.BindExternalFunction<string, int>("tirada", Tirar);
        historia.BindExternalFunction<string>("facultad", nombre => ficha[Facultades.Analizar(nombre)], lookaheadSafe: true);
        historia.BindExternalFunction<string, string, string>("pista", AnotarPista);
        historia.ErrorError += mensaje => Errores.Add(mensaje);
        historia.AuthorError += mensaje => Errores.Add(mensaje);
    }

    /// <summary>Errores de Ink acumulados. Las pruebas comprueban que siga vacío.</summary>
    public List<string> Errores { get; } = new();

    public bool EnCurso { get; private set; }

    public Paso Empezar(string nudo)
    {
        historia.ChoosePathString(nudo);
        EnCurso = true;
        return Avanzar();
    }

    public Paso Elegir(int indice)
    {
        historia.ChooseChoiceIndex(indice);
        return Avanzar();
    }

    public string GuardarEstado() => historia.SaveState();

    public void CargarEstado(string json)
    {
        if (!string.IsNullOrEmpty(json))
            historia.LoadState(json);
        EnCurso = false;
    }

    public Variant Variable(string nombre) => historia.FetchVariable(nombre);

    private Paso Avanzar()
    {
        var entradas = new List<Entrada>();
        while (historia.CanContinue)
        {
            string texto = historia.Continue();
            // Lo que pasó durante la línea (tiradas, pistas) va antes que la línea.
            entradas.AddRange(pendientes);
            pendientes.Clear();
            if (!string.IsNullOrWhiteSpace(texto))
                entradas.Add(new EntradaLinea(LineaDialogo.Analizar(texto)));
        }
        entradas.AddRange(pendientes);
        pendientes.Clear();

        var opciones = historia.CurrentChoices
            .Select(c => new OpcionVista(c.Index, c.Text.Trim(), ComprobacionOpcion.DesdeEtiquetas(c.Tags)))
            .ToList();
        if (opciones.Count == 0)
            EnCurso = false;
        return new Paso(entradas, opciones);
    }

    private Variant Tirar(string nombreFacultad, int dificultad)
    {
        Facultad f = Facultades.Analizar(nombreFacultad);
        ResultadoTirada r = Tirada.Resolver(f, ficha[f], dificultad, dados);
        pendientes.Add(new EntradaTirada(r));
        return r.Exito;
    }

    private void AnotarPista(string id, string titulo, string texto)
    {
        var pista = new Pista(id, titulo, texto);
        if (pesquisa.Anotar(pista))
            pendientes.Add(new EntradaPista(pista));
    }
}
