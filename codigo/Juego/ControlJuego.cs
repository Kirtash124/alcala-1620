using System;
using System.Linq;
using Alcala.Reglas;
using Alcala.Ui;
using Godot;
using GodotInk;

namespace Alcala.Juego;

/// <summary>
/// Director de la partida: carga el lugar, coloca al pesquisidor, traduce los clics
/// en paseos e interacciones, abre las conversaciones y guarda o carga la partida.
/// </summary>
public partial class ControlJuego : Node
{
    public const string RutaHistoria = "res://dialogos/principal.ink";
    public const string RutaPesquisidor = "res://escenas/personajes/Pesquisidor.tscn";
    public const string LugarInicial = "res://escenas/lugares/CalleMayor.tscn";
    public const string RutaPartida = "user://partida.json";

    public Ficha Ficha { get; } = Ficha.Pesquisidor();
    public Pesquisa Pesquisa { get; } = new();
    public Narrador Narrador { get; private set; } = null!;
    public Lugar LugarActual { get; private set; } = null!;
    public Personaje Jugador { get; private set; } = null!;
    public PanelDialogo Panel { get; private set; } = null!;
    public bool Listo { get; private set; }
    public bool EnDialogo => Panel.Abierto;

    private Node2D mundo = null!;
    private Camara camara = null!;
    private Diario diario = null!;
    private Hud hud = null!;
    private PuntoDeInteres? puntoBajoCursor;

    public override async void _Ready()
    {
        mundo = GetNode<Node2D>("Mundo");
        camara = GetNode<Camara>("Camara");
        Panel = GetNode<PanelDialogo>("Interfaz/PanelDialogo");
        diario = GetNode<Diario>("Interfaz/Diario");
        hud = GetNode<Hud>("Interfaz/Hud");

        var historia = (InkStory)ResourceLoader.Load(RutaHistoria, null, ResourceLoader.CacheMode.Ignore);
        Narrador = new Narrador(historia, Ficha, Pesquisa, new DadosAleatorios(LeerSemilla()));
        Panel.OpcionElegida += AlElegirOpcion;

        CargarLugar(LugarInicial);

        // El servidor de navegación incorpora la malla en un fotograma de física posterior.
        // Hasta entonces las rutas salen vacías, así que no se acepta ningún clic.
        for (int i = 0; i < 120; i++)
        {
            await ToSignal(GetTree(), SceneTree.SignalName.PhysicsFrame);
            // Vale solo si la malla que responde es la de este lugar (al cambiar de lugar,
            // la del anterior puede seguir un instante en el mapa).
            if (NavigationServer2D.MapGetIterationId(LugarActual.Mapa) > 0
                && NavigationServer2D.MapGetClosestPointOwner(LugarActual.Mapa, LugarActual.Inicio) == LugarActual.Navegacion.GetRid())
                break;
        }
        Listo = true;
    }

    private void CargarLugar(string ruta)
    {
        LugarActual?.QueueFree();
        LugarActual = GD.Load<PackedScene>(ruta).Instantiate<Lugar>();
        mundo.AddChild(LugarActual);

        Jugador = GD.Load<PackedScene>(RutaPesquisidor).Instantiate<Personaje>();
        Jugador.Name = "Jugador";
        LugarActual.Entidades.AddChild(Jugador);
        Jugador.Situar(LugarActual.Inicio);

        camara.Objetivo = Jugador;
        camara.Encuadrar(LugarActual.Limites);
    }

    // ---------------------------------------------------------------- entrada

    public override void _UnhandledInput(InputEvent evento)
    {
        if (!Listo)
            return;

        if (evento is InputEventMouseButton { ButtonIndex: MouseButton.Left, Pressed: true } && !EnDialogo && !diario.Visible)
        {
            Vector2 punto = mundo.GetGlobalMousePosition();
            PuntoDeInteres? objetivo = LugarActual.PuntoEn(punto);
            if (objetivo is not null)
                Interactuar(objetivo);
            else
                IrA(punto);
            GetViewport().SetInputAsHandled();
        }
        else if (evento is InputEventKey { Pressed: true, Echo: false } tecla)
        {
            switch (tecla.Keycode)
            {
                case Key.D when !EnDialogo:
                    diario.Alternar(Pesquisa);
                    break;
                case Key.Escape when diario.Visible:
                    diario.Visible = false;
                    break;
                case Key.F5:
                    IntentarGuardar();
                    break;
                case Key.F9:
                    IntentarCargar();
                    break;
            }
        }
    }

    public override void _Process(double delta)
    {
        if (!Listo || EnDialogo || diario.Visible)
        {
            hud.MostrarRotulo(null, Vector2.Zero);
            Input.SetDefaultCursorShape();
            return;
        }
        puntoBajoCursor = LugarActual.PuntoEn(mundo.GetGlobalMousePosition());
        hud.MostrarRotulo(puntoBajoCursor?.Nombre, GetViewport().GetMousePosition());
        Input.SetDefaultCursorShape(puntoBajoCursor is null ? Input.CursorShape.Arrow : Input.CursorShape.PointingHand);
    }

    // ---------------------------------------------------------------- acciones

    public void IrA(Vector2 destino, Action? alLlegar = null)
    {
        Vector2[] ruta = LugarActual.Ruta(Jugador.GlobalPosition, destino);
        if (ruta.Length == 0)
            ruta = LugarActual.Ruta(Jugador.GlobalPosition, LugarActual.MasCercanoTransitable(destino));
        Jugador.SeguirRuta(ruta, alLlegar);
    }

    public void Interactuar(PuntoDeInteres punto)
    {
        IrA(punto.Llegada, () =>
        {
            Jugador.MirarHacia(punto.Centro);
            if (!string.IsNullOrEmpty(punto.Nudo))
                AbrirDialogo(punto);
        });
    }

    /// <summary>Atajo para pruebas: interactúa con un punto por el nombre de su nodo.</summary>
    public void Interactuar(string nombreNodo) =>
        Interactuar(LugarActual.Punto(nombreNodo) ?? throw new ArgumentException($"No hay punto «{nombreNodo}»."));

    private void AbrirDialogo(PuntoDeInteres punto)
    {
        Panel.Abrir(punto.Nombre, () => Ficha);
        camara.DesplazamientoX = GetViewport().GetVisibleRect().Size.X * PanelDialogo.FraccionAncho / 2f;
        Panel.Mostrar(Narrador.Empezar(punto.Nudo));
    }

    private void AlElegirOpcion(int indice)
    {
        if (indice < 0)
        {
            Panel.Cerrar();
            camara.DesplazamientoX = 0;
            return;
        }
        Panel.Mostrar(Narrador.Elegir(indice));
    }

    /// <summary>Elige una opción como si el jugador la pulsara (para pruebas).</summary>
    public void ElegirOpcion(int indiceInk) => AlElegirOpcion(indiceInk);

    // ---------------------------------------------------------------- partida

    private void IntentarGuardar()
    {
        if (EnDialogo)
        {
            hud.Avisar("No se puede guardar en mitad de una conversación");
            return;
        }
        Guardar(RutaPartida);
        hud.Avisar("Partida guardada");
    }

    private void IntentarCargar()
    {
        if (!FileAccess.FileExists(RutaPartida))
        {
            hud.Avisar("No hay ninguna partida guardada");
            return;
        }
        Cargar(RutaPartida);
        hud.Avisar("Partida cargada");
    }

    public void Guardar(string ruta)
    {
        EstadoPartida estado = Guardado.Capturar(LugarActual.Id, Jugador.GlobalPosition.X, Jugador.GlobalPosition.Y,
                                                 Ficha, Pesquisa, Narrador.GuardarEstado());
        using var archivo = FileAccess.Open(ruta, FileAccess.ModeFlags.Write)
            ?? throw new InvalidOperationException($"No se pudo escribir {ruta}: {FileAccess.GetOpenError()}");
        archivo.StoreString(Guardado.AJson(estado));
    }

    public void Cargar(string ruta)
    {
        EstadoPartida estado = Guardado.DesdeJson(FileAccess.GetFileAsString(ruta));
        if (Panel.Abierto)
            AlElegirOpcion(-1);
        diario.Visible = false;
        Guardado.Aplicar(estado, Ficha, Pesquisa);
        Narrador.CargarEstado(estado.EstadoInk);
        Jugador.Situar(new Vector2(estado.JugadorX, estado.JugadorY));
        camara.Encuadrar(LugarActual.Limites);
    }

    /// <summary>Si se fija (pruebas), los dados de la siguiente partida usan esta semilla.</summary>
    public static int? SemillaForzada { get; set; }

    private static int? LeerSemilla()
    {
        if (SemillaForzada is int forzada)
            return forzada;
        string? arg = OS.GetCmdlineUserArgs().FirstOrDefault(a => a.StartsWith("--semilla="));
        return arg is null ? null : int.Parse(arg["--semilla=".Length..]);
    }
}
