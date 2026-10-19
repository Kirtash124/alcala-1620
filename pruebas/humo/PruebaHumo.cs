using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Alcala.Juego;
using Godot;

namespace Alcala.Pruebas;

/// <summary>
/// Prueba de humo: arranca el juego de verdad y lo juega solo.
///
///   Sin pantalla:  godot --headless --path . res://pruebas/humo/PruebaHumo.tscn
///   Con capturas:  godot --path . res://pruebas/humo/PruebaHumo.tscn -- --capturas=/ruta/carpeta
///
/// Recorre todas las conversaciones con varias semillas de dados (aciertos y fallos
/// distintos), comprueba que Ink no da errores, que se puede llegar a cada punto,
/// que las pistas se anotan y que guardar y cargar devuelve el mismo estado.
/// Termina con código 0 si todo va bien y 1 si algo falla.
/// </summary>
public partial class PruebaHumo : Node
{
    private readonly List<string> fallos = new();
    private string? carpetaCapturas;
    private ControlJuego juego = null!;

    public override async void _Ready()
    {
        carpetaCapturas = OS.GetCmdlineUserArgs()
            .FirstOrDefault(a => a.StartsWith("--capturas="))?["--capturas=".Length..];
        bool conCapturas = carpetaCapturas is not null;
        Engine.TimeScale = conCapturas ? 3 : 12;

        try
        {
            int[] semillas = conCapturas ? new[] { 7 } : new[] { 1, 2, 3, 5, 8, 13, 21, 34 };
            foreach (int semilla in semillas)
                await Partida(semilla);
        }
        catch (Exception e)
        {
            Fallo($"Excepción: {e}");
        }

        if (fallos.Count == 0)
        {
            GD.Print("PRUEBA DE HUMO: OK");
            GetTree().Quit(0);
        }
        else
        {
            foreach (string f in fallos)
                GD.PrintErr("FALLO: " + f);
            GD.PrintErr($"PRUEBA DE HUMO: {fallos.Count} fallo(s)");
            GetTree().Quit(1);
        }
    }

    private async Task Partida(int semilla)
    {
        ControlJuego.SemillaForzada = semilla;
        juego = GD.Load<PackedScene>("res://escenas/Principal.tscn").Instantiate<ControlJuego>();
        AddChild(juego);
        await Esperar(() => juego.Listo, 5, "el juego no terminó de cargar");

        Lugar lugar = juego.LugarActual;
        Comprobar(lugar.Navegacion.NavigationPolygon.GetPolygonCount() > 0, "la calle no tiene zona transitable");
        Comprobar(juego.Jugador.GlobalPosition.DistanceTo(lugar.Inicio) < 1f, "el pesquisidor no empieza en «Inicio»");

        foreach (PuntoDeInteres p in lugar.Puntos)
        {
            Vector2[] ruta = lugar.Ruta(juego.Jugador.GlobalPosition, p.Llegada);
            Comprobar(ruta.Length > 0 && ruta[^1].DistanceTo(p.Llegada) < 20f,
                      $"no se puede llegar a «{p.Name}» (llegada {p.Llegada})");
        }
        await Capturar("01_inicio");

        // Paseo por detrás de una columna y del carro: sirve para ver en las capturas
        // si los recortes tapan. Los puntos los pone el generador de la escena.
        foreach ((string marca, string captura) in new[] { ("TrasColumna", "02a_tras_columna"), ("TrasCarro", "02b_tras_carro") })
        {
            Marker2D? m = lugar.GetNodeOrNull<Marker2D>($"Pruebas/{marca}");
            Comprobar(m is not null, $"falta el marcador de prueba «{marca}»");
            if (m is null)
                continue;
            Vector2 destino = lugar.MasCercanoTransitable(m.GlobalPosition);
            Comprobar(destino.DistanceTo(m.GlobalPosition) < 25f, $"«{marca}» no está en zona transitable");
            await Andar(destino);
            await Capturar(captura);
        }

        await Conversar("Cadaver", "02_cadaver");
        await Conversar("Hornacina", null);
        await Conversar("Alguacil", "03_alguacil");
        await Conversar("Salida", null);

        Comprobar(juego.Narrador.Errores.Count == 0, "Ink dio errores: " + string.Join(" | ", juego.Narrador.Errores));
        Comprobar(juego.Pesquisa.Tiene("cera"), "no se anotó la pista de la cera");
        Comprobar(juego.Pesquisa.Tiene("nombre"), "no se anotó el nombre del muerto");
        Comprobar(juego.Narrador.Variable("vio_cera").AsBool(), "Ink no registró vio_cera");

        // Diario abierto, para la captura.
        Pulsar(Key.D);
        await Fotogramas(10);
        await Capturar("04_diario");
        Pulsar(Key.D);

        // Guardar, estropear el estado y cargar.
        const string rutaPartida = "user://prueba_humo.json";
        juego.Guardar(rutaPartida);
        Vector2 posicion = juego.Jugador.GlobalPosition;
        int pistas = juego.Pesquisa.Pistas.Count;
        string inkAntes = juego.Narrador.GuardarEstado();

        await Andar(lugar.MasCercanoTransitable(lugar.Inicio));
        juego.Pesquisa.Restaurar(Array.Empty<Alcala.Reglas.Pista>());
        juego.Cargar(rutaPartida);

        Comprobar(juego.Jugador.GlobalPosition.DistanceTo(posicion) < 0.5f, "cargar no devolvió al pesquisidor a su sitio");
        Comprobar(juego.Pesquisa.Pistas.Count == pistas, "cargar no recuperó las pistas");
        Comprobar(juego.Narrador.GuardarEstado() == inkAntes, "cargar no recuperó el estado de Ink");

        // Tras cargar, las opciones ya usadas no deben volver a aparecer.
        juego.Interactuar("Cadaver");
        await Esperar(() => juego.EnDialogo, 30, "no se reabrió la conversación tras cargar");
        Comprobar(juego.Panel.OpcionesVisibles == 1, $"tras cargar quedan {juego.Panel.OpcionesVisibles} opciones en el cadáver; se esperaba solo «Dejarlo estar»");
        juego.ElegirOpcion(-1);

        GD.Print($"Semilla {semilla}: {juego.Pesquisa.Pistas.Count} pistas · " +
                 string.Join(", ", juego.Pesquisa.Pistas.Select(p => p.Id)));
        juego.QueueFree();
        // Que la malla de navegación de esta partida salga del mapa antes de la siguiente.
        for (int i = 0; i < 4; i++)
            await ToSignal(GetTree(), SceneTree.SignalName.PhysicsFrame);
    }

    /// <summary>Va hasta un punto, abre su conversación y elige opciones hasta agotarla.</summary>
    private async Task Conversar(string punto, string? captura)
    {
        juego.Interactuar(punto);
        await Esperar(() => juego.EnDialogo, 30, $"no se abrió la conversación con «{punto}»");

        for (int vuelta = 0; vuelta < 40 && juego.EnDialogo; vuelta++)
        {
            await Fotogramas(2);
            if (!juego.EnDialogo)
                break;
            if (vuelta == 2 && captura is not null)
                await Capturar(captura);
            // Primera opción disponible: las de un solo uso se agotan y al final
            // queda la de salir, que es la última.
            if (juego.Panel.OpcionesVisibles == 0)
            {
                Fallo($"conversación con «{punto}» sin opciones ni cierre");
                return;
            }
            Pulsar(Key.Key1);
        }
        if (juego.EnDialogo)
            Fallo($"la conversación con «{punto}» no termina");
        Comprobar(juego.Panel.TextoRegistro().Length > 0 || !juego.EnDialogo, $"registro vacío en «{punto}»");
    }

    private async Task Andar(Vector2 destino)
    {
        bool llego = false;
        juego.IrA(destino, () => llego = true);
        await Esperar(() => llego, 30, $"el pesquisidor no llegó a {destino}");
        await Fotogramas(5);
    }

    private void Pulsar(Key tecla)
    {
        var e = new InputEventKey { Keycode = tecla, Pressed = true };
        Input.ParseInputEvent(e);
        Input.ParseInputEvent(new InputEventKey { Keycode = tecla, Pressed = false });
    }

    private async Task Capturar(string nombre)
    {
        if (carpetaCapturas is null)
            return;
        await Fotogramas(30);
        Image img = GetViewport().GetTexture().GetImage();
        DirAccess.MakeDirRecursiveAbsolute(carpetaCapturas);
        img.SavePng($"{carpetaCapturas}/{nombre}.png");
    }

    private async Task Esperar(Func<bool> condicion, double segundosJuego, string error)
    {
        ulong limite = Time.GetTicksMsec() + (ulong)(segundosJuego * 1000 / Engine.TimeScale) + 2000;
        while (!condicion())
        {
            if (Time.GetTicksMsec() > limite)
                throw new TimeoutException(error);
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        }
    }

    private async Task Fotogramas(int n)
    {
        for (int i = 0; i < n; i++)
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    }

    private void Comprobar(bool condicion, string mensaje)
    {
        if (!condicion)
            Fallo(mensaje);
    }

    private void Fallo(string mensaje) => fallos.Add(mensaje);
}
