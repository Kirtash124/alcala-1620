using System.Collections.Generic;
using System.Linq;
using Godot;

namespace Alcala.Juego;

/// <summary>
/// Un escenario del juego: suelo, piezas (casas, objetos), zona por la que se puede
/// andar, obstáculos, personajes y puntos de interés.
///
/// Estructura esperada (ver escenas/lugares/CalleMayor.tscn):
///   Fondo (Sprite2D)          suelo del escenario, sin centrar, en el origen; marca los límites
///   Transitable (Polygon2D)   contorno del suelo por el que se anda
///   Obstaculos (Node2D)       Polygon2D con huecos dentro de lo transitable
///   Inicio (Marker2D)         dónde aparece el pesquisidor
///   Entidades (Node2D)        piezas, oclusores y personajes, ordenados por altura
///   Puntos (Node2D)           puntos de interés
/// Las huellas de las piezas (<see cref="Pieza"/>) también son obstáculos.
/// </summary>
[GlobalClass]
public partial class Lugar : Node2D
{
    [Export] public string Id { get; set; } = "";
    [Export] public string Titulo { get; set; } = "";
    /// <summary>Radio del pesquisidor para no rozar paredes, en píxeles.</summary>
    [Export] public float RadioAgente { get; set; } = 14f;
    /// <summary>
    /// Tono de los personajes en este lugar. La luz del escenario va ya pintada en las
    /// piezas, pero los personajes son dibujos neutros: se oscurecen y enfrían para
    /// que no parezca que están a pleno día.
    /// </summary>
    [Export] public Color TonoPersonajes { get; set; } = Colors.White;

    public Sprite2D Fondo { get; private set; } = null!;
    public Node2D Entidades { get; private set; } = null!;
    public NavigationRegion2D Navegacion { get; private set; } = null!;

    public override void _Ready()
    {
        Fondo = GetNode<Sprite2D>("Fondo");
        Fondo.ZIndex = -10;                 // por debajo de las piezas de fondo (z -1)
        Entidades = GetNode<Node2D>("Entidades");
        Entidades.YSortEnabled = true;
        foreach (Personaje p in Entidades.GetChildren().OfType<Personaje>())
            p.Modulate = TonoPersonajes;
        ConstruirNavegacion();
    }

    public IEnumerable<Pieza> Piezas =>
        Entidades.FindChildren("*", "", true, false).OfType<Pieza>();

    public Rect2 Limites => new(Fondo.Position, Fondo.Texture?.GetSize() ?? new Vector2(1920, 1080));

    public Vector2 Inicio => GetNodeOrNull<Marker2D>("Inicio")?.GlobalPosition ?? Limites.GetCenter();

    public IEnumerable<PuntoDeInteres> Puntos =>
        GetNodeOrNull("Puntos")?.GetChildren().OfType<PuntoDeInteres>() ?? Enumerable.Empty<PuntoDeInteres>();

    public PuntoDeInteres? Punto(string nombreNodo) => Puntos.FirstOrDefault(p => p.Name == nombreNodo);

    /// <summary>El punto de interés bajo el cursor. Si hay varios, gana el más pequeño.</summary>
    public PuntoDeInteres? PuntoEn(Vector2 puntoGlobal) =>
        Puntos.Where(p => p.Visible && p.Contiene(puntoGlobal)).OrderBy(p => p.Area).FirstOrDefault();

    public Rid Mapa => Navegacion.GetNavigationMap();

    public Vector2[] Ruta(Vector2 desde, Vector2 hasta) =>
        NavigationServer2D.MapGetPath(Mapa, desde, hasta, true);

    public Vector2 MasCercanoTransitable(Vector2 punto) =>
        NavigationServer2D.MapGetClosestPoint(Mapa, punto);

    /// <summary>
    /// Genera la malla de navegación a partir de los polígonos «Transitable» y «Obstaculos».
    /// Se hace al cargar el lugar, así basta con dibujar los polígonos en el editor.
    /// </summary>
    private void ConstruirNavegacion()
    {
        var transitable = GetNode<Polygon2D>("Transitable");
        var datos = new NavigationMeshSourceGeometryData2D();
        datos.AddTraversableOutline(Globales(transitable));
        foreach (Polygon2D obstaculo in GetNodeOrNull("Obstaculos")?.GetChildren().OfType<Polygon2D>() ?? Enumerable.Empty<Polygon2D>())
        {
            datos.AddObstructionOutline(Globales(obstaculo));
            obstaculo.Visible = false;
        }
        foreach (Pieza pieza in Piezas)
        {
            foreach (Vector2[] huella in pieza.Huellas(this))
                datos.AddObstructionOutline(huella);
        }
        transitable.Visible = false;

        var malla = new NavigationPolygon { AgentRadius = RadioAgente };
        NavigationServer2D.BakeFromSourceGeometryData(malla, datos, new Callable());

        Navegacion = new NavigationRegion2D { Name = "Navegacion", NavigationPolygon = malla };
        AddChild(Navegacion);
        if (malla.GetPolygonCount() == 0)
            GD.PushError($"El lugar «{Id}» no tiene zona transitable: revisa el polígono «Transitable».");
    }

    /// <summary>Vértices del polígono expresados en el espacio del lugar.</summary>
    private Vector2[] Globales(Polygon2D poligono)
    {
        Transform2D t = GlobalTransform.AffineInverse() * poligono.GlobalTransform;
        return poligono.Polygon.Select(p => t * p).ToArray();
    }
}
