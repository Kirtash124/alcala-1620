using System;
using Godot;

namespace Alcala.Juego;

/// <summary>
/// Prueba de marcha mediante una malla sobre la pintura existente. No modifica
/// los PNG ni dirige la navegación. Se añade como hijo del Personaje para probarla.
/// </summary>
public partial class DibujoArticulado : Node2D
{
    [Export] public bool Activo { get; set; } = true;
    [Export(PropertyHint.Range, "32,96,1")] public float LongitudCiclo { get; set; } = 64f;
    [Export(PropertyHint.Range, "0,12,0.5")] public float AlturaPaso { get; set; } = 5f;

    public float Fase { get; private set; }
    public bool EnReposo => intensidad < 0.001f;

    private Personaje personaje = null!;
    private Sprite2D original = null!;
    private Polygon2D malla = null!;
    private Vector2[] baseVertices = Array.Empty<Vector2>();
    private Vector2[] vertices = Array.Empty<Vector2>();
    private Texture2D? textura;
    private Vector2 anterior;
    private Vector2 direccion = new(0.8944272f, 0.4472136f);
    private float intensidad;
    private float tiempo;

    public override void _Ready()
    {
        personaje = GetParent<Personaje>();
        original = personaje.GetNode<Sprite2D>("Cuerpo");
        anterior = personaje.GlobalPosition;
        malla = new Polygon2D { Name = "Pintura", Antialiased = false };
        AddChild(malla);
    }

    public override void _ExitTree()
    {
        if (IsInstanceValid(original))
            original.Visible = true;
    }

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        tiempo += dt;
        Vector2 movimiento = personaje.GlobalPosition - anterior;
        anterior = personaje.GlobalPosition;
        original.Visible = !Activo;
        malla.Visible = Activo;
        if (!Activo)
        {
            intensidad = 0;
            Fase = 0;
            return;
        }

        if (original.Texture is null)
            return;
        if (textura != original.Texture)
            PrepararMalla(original.Texture);

        float distancia = movimiento.Length();
        bool traslado = distancia > MathF.Max(2f, personaje.Velocidad * dt * 1.6f);
        bool andando = !traslado && distancia > 0.0001f;
        if (traslado)
        {
            intensidad = 0;
            Fase = 0;
        }
        else if (andando)
        {
            direccion = movimiento / distancia;
            Fase = (Fase + distancia / MathF.Max(1f, LongitudCiclo)) % 1f;
        }

        intensidad = Mathf.MoveToward(intensidad, andando ? 1f : 0f, dt * 7f);
        if (EnReposo)
            Fase = 0;

        // El espejo se hace alrededor del origen de los pies, igual que en el
        // Sprite2D original. Las deformaciones siguen la dirección real del paseo.
        Scale = new Vector2(personaje.MiraIzquierda ? -1f : 1f, 1);
        malla.Position = original.Offset;
        Vector2 dirLocal = new(direccion.X * Scale.X, direccion.Y);
        float ancho = textura!.GetWidth();
        float alto = textura.GetHeight();
        float separacion = ancho * (personaje.DeEspaldas ? 0.45f : 0.51f);
        float cadera = alto * (personaje.DeEspaldas ? 0.67f : 0.62f);
        float respiracion = MathF.Sin(tiempo * 2.1f) * 0.003f;
        float balanceo = MathF.Sin(Fase * MathF.Tau) * intensidad * 0.45f;
        float subida = -MathF.Abs(MathF.Sin(Fase * MathF.Tau)) * intensidad;

        for (int i = 0; i < baseVertices.Length; i++)
        {
            Vector2 p = baseVertices[i];
            bool piernaIzquierda = p.X < separacion;
            float suela = alto * (personaje.DeEspaldas
                ? (piernaIzquierda ? 0.90f : 0.97f)
                : (piernaIzquierda ? 0.98f : 0.87f));
            float pesoPie = Mathf.Clamp((p.Y - cadera) / (suela - cadera - 9f), 0, 1);
            float fasePie = Fase + (piernaIzquierda ? 0 : 0.5f);
            CicloMarcha.Pie pie = CicloMarcha.Evaluar(fasePie, LongitudCiclo, AlturaPaso);
            Vector2 paso = dirLocal * pie.Avance + Vector2.Up * pie.Elevacion;
            float torso = 1f - pesoPie;
            Vector2 gesto = new(balanceo * torso,
                subida * torso - MathF.Max(0, cadera - p.Y) * respiracion * (1f - intensidad));
            vertices[i] = p + paso * pesoPie * intensidad + gesto;
        }
        malla.Polygon = vertices;
    }

    private void PrepararMalla(Texture2D nueva)
    {
        textura = nueva;
        malla.Texture = nueva;
        int columnas = (int)MathF.Ceiling(nueva.GetWidth() / 4f);
        int filas = (int)MathF.Ceiling(nueva.GetHeight() / 4f);
        baseVertices = new Vector2[(columnas + 1) * (filas + 1)];
        vertices = new Vector2[baseVertices.Length];
        var triangulos = new Godot.Collections.Array();
        for (int y = 0; y <= filas; y++)
        for (int x = 0; x <= columnas; x++)
        {
            int i = y * (columnas + 1) + x;
            baseVertices[i] = new Vector2((float)x / columnas * nueva.GetWidth(),
                                          (float)y / filas * nueva.GetHeight());
            if (x == columnas || y == filas)
                continue;
            int abajo = i + columnas + 1;
            triangulos.Add(new[] { i, i + 1, abajo + 1 });
            triangulos.Add(new[] { i, abajo + 1, abajo });
        }
        malla.Polygon = baseVertices;
        malla.UV = baseVertices;
        malla.Polygons = triangulos;
    }
}
