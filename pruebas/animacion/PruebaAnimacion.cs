using System;
using System.Linq;
using System.Threading.Tasks;
using Alcala.Juego;
using Godot;

namespace Alcala.Pruebas;

/// <summary>La calle habitual con una marcha experimental y comparación con A.</summary>
public partial class PruebaAnimacion : Node
{
    private ControlJuego juego = null!;
    private DibujoArticulado dibujo = null!;
    private Label rotulo = null!;

    public override async void _Ready()
    {
        try
        {
            juego = GD.Load<PackedScene>("res://escenas/Principal.tscn").Instantiate<ControlJuego>();
            AddChild(juego);
            await Esperar(() => juego.Listo, 10);
            dibujo = new DibujoArticulado { Name = "MarchaExperimental" };
            juego.Jugador.AddChild(dibujo);
            // Cadencia de paseo: el ciclo recorre 64 píxeles de suelo. La velocidad
            // original del prototipo (240) produciría más de tres ciclos por segundo.
            juego.Jugador.Velocidad = 105f;
            var interfaz = new CanvasLayer { Layer = 50 };
            AddChild(interfaz);
            rotulo = new Label { Position = new Vector2(24, 80), MouseFilter = Control.MouseFilterEnum.Ignore };
            rotulo.AddThemeFontSizeOverride("font_size", 19);
            rotulo.AddThemeColorOverride("font_shadow_color", Colors.Black);
            rotulo.AddThemeConstantOverride("shadow_offset_x", 2);
            rotulo.AddThemeConstantOverride("shadow_offset_y", 2);
            interfaz.AddChild(rotulo);
            ActualizarRotulo();
            if (OS.GetCmdlineUserArgs().Contains("--automatico"))
            {
                juego.SetProcessUnhandledInput(false);
                SetProcessUnhandledInput(false);
                await RecorridoAutomatico();
            }
        }
        catch (Exception e)
        {
            GD.PrintErr("PRUEBA DE ANIMACIÓN: " + e);
            GetTree().Quit(1);
        }
    }

    public override void _UnhandledInput(InputEvent evento)
    {
        if (dibujo is null || evento is not InputEventKey { Pressed: true, Echo: false, Keycode: Key.A })
            return;
        dibujo.Activo = !dibujo.Activo;
        ActualizarRotulo();
        GetViewport().SetInputAsHandled();
    }

    private void ActualizarRotulo()
    {
        rotulo.Text = (dibujo.Activo ? "Marcha articulada" : "Balanceo original")
                    + " · Clic para andar · A para comparar";
    }

    private async Task RecorridoAutomatico()
    {
        Vector2 inicio = juego.Jugador.GlobalPosition;
        string? capturas = OS.GetCmdlineUserArgs()
            .FirstOrDefault(a => a.StartsWith("--capturas="))?["--capturas=".Length..];
        int numero = 0;
        foreach (Vector2 desplazamiento in new[] {
            new Vector2(240, 120), new Vector2(480, 0), new Vector2(240, -120), Vector2.Zero })
        {
            bool llego = false;
            juego.IrA(juego.LugarActual.MasCercanoTransitable(inicio + desplazamiento), () => llego = true);
            await Fotogramas(12);
            if (capturas is not null && DisplayServer.GetName() != "headless")
            {
                DirAccess.MakeDirRecursiveAbsolute(capturas);
                for (int f = 0; f < 12; f++)
                {
                    await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
                    GetViewport().GetTexture().GetImage().SavePng($"{capturas}/marcha_{numero++:D3}.png");
                    await ToSignal(GetTree().CreateTimer(1.0 / 12), SceneTreeTimer.SignalName.Timeout);
                }
            }
            await Esperar(() => llego, 30);
            await Esperar(() => dibujo.EnReposo, 2);
        }

        // Cargar una partida o recolocar al jugador debe mantener los pies en el
        // origen y descartar la fase anterior, incluso tras un desplazamiento grande.
        juego.Jugador.Situar(inicio + new Vector2(400, 200));
        await Fotogramas(3);
        if (!dibujo.EnReposo || dibujo.Fase != 0)
            throw new InvalidOperationException("el traslado conserva un paso a medias");
        dibujo.Activo = false;
        await Fotogramas(3);
        if (!juego.Jugador.GetNode<Sprite2D>("Cuerpo").Visible)
            throw new InvalidOperationException("la comparación no recupera el dibujo original");
        GD.Print("PRUEBA DE ANIMACIÓN: OK");
        GetTree().Quit(0);
    }

    private async Task Esperar(Func<bool> condicion, double segundos)
    {
        double transcurrido = 0;
        while (!condicion())
        {
            if (transcurrido > segundos)
                throw new TimeoutException("la animación o el recorrido no terminó");
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            transcurrido += GetProcessDeltaTime();
        }
    }

    private async Task Fotogramas(int cantidad)
    {
        for (int i = 0; i < cantidad; i++)
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    }
}
