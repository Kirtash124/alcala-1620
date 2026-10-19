using System;
using System.Collections.Generic;
using Godot;

namespace Alcala.Juego;

/// <summary>
/// Personaje con dos dibujos: de frente (mirando abajo a la derecha) y de espaldas
/// (mirando arriba a la derecha). Las otras dos direcciones se obtienen en espejo.
/// El caminar se anima por código (balanceo), así que no hacen falta fotogramas.
///
/// Hijos esperados: «Cuerpo» (Sprite2D) y, opcionalmente, «Sombra» (Sprite2D).
/// El origen del nodo está en los pies.
/// </summary>
[GlobalClass]
public partial class Personaje : Node2D
{
    [Export] public Texture2D? Frente { get; set; }
    [Export] public Texture2D? Espalda { get; set; }
    [Export] public float Velocidad { get; set; } = 240f;
    [Export] public bool MiraIzquierda { get; set; }
    [Export] public bool DeEspaldas { get; set; }

    private Sprite2D cuerpo = null!;
    private readonly Queue<Vector2> ruta = new();
    private Action? alLlegar;
    private float fasePaso;
    private float tiempo;

    public bool Andando => ruta.Count > 0;

    public override void _Ready()
    {
        cuerpo = GetNode<Sprite2D>("Cuerpo");
        tiempo = (float)GD.RandRange(0, 10);
        ActualizarAspecto();
    }

    public void SeguirRuta(IReadOnlyList<Vector2> puntos, Action? alTerminar = null)
    {
        ruta.Clear();
        foreach (Vector2 p in puntos)
        {
            if (p.DistanceSquaredTo(GlobalPosition) > 1f)
                ruta.Enqueue(p);
        }
        alLlegar = alTerminar;
        if (ruta.Count == 0)
            Llegar();
    }

    public void Detener()
    {
        ruta.Clear();
        alLlegar = null;
    }

    /// <summary>Coloca al personaje sin animación (al cargar partida o entrar en un lugar).</summary>
    public void Situar(Vector2 posicion)
    {
        Detener();
        GlobalPosition = posicion;
    }

    public void MirarHacia(Vector2 objetivo)
    {
        Vector2 d = objetivo - GlobalPosition;
        if (Mathf.Abs(d.X) > 2f)
            MiraIzquierda = d.X < 0;
        if (Mathf.Abs(d.Y) > 2f)
            DeEspaldas = d.Y < 0;
        ActualizarAspecto();
    }

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        tiempo += dt;

        if (ruta.Count > 0)
        {
            Vector2 destino = ruta.Peek();
            Vector2 hacia = destino - GlobalPosition;
            float paso = Velocidad * dt;
            if (hacia.Length() <= paso)
            {
                GlobalPosition = destino;
                ruta.Dequeue();
                if (ruta.Count == 0)
                    Llegar();
            }
            else
            {
                Vector2 dir = hacia.Normalized();
                GlobalPosition += dir * paso;
                if (Mathf.Abs(dir.X) > 0.15f) MiraIzquierda = dir.X < 0;
                if (Mathf.Abs(dir.Y) > 0.15f) DeEspaldas = dir.Y < 0;
                ActualizarAspecto();
            }
            fasePaso += dt * 11f;
            // Balanceo al andar: sube y baja con cada paso y se mece un poco.
            cuerpo.Position = new Vector2(0, -Mathf.Abs(Mathf.Sin(fasePaso)) * 5f);
            cuerpo.Rotation = Mathf.Sin(fasePaso) * 0.035f;
            cuerpo.Scale = Vector2.One;
        }
        else
        {
            fasePaso = 0;
            cuerpo.Position = Vector2.Zero;
            cuerpo.Rotation = 0;
            // Respiración en reposo, casi imperceptible.
            cuerpo.Scale = new Vector2(1f, 1f + Mathf.Sin(tiempo * 2.1f) * 0.006f);
        }
    }

    private void Llegar()
    {
        Action? callback = alLlegar;
        alLlegar = null;
        callback?.Invoke();
    }

    private void ActualizarAspecto()
    {
        if (cuerpo is null)
            return;
        Texture2D? textura = DeEspaldas && Espalda is not null ? Espalda : Frente;
        if (textura is not null && cuerpo.Texture != textura)
            cuerpo.Texture = textura;
        cuerpo.FlipH = MiraIzquierda;
    }
}
