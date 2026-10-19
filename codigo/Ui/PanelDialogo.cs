using System;
using System.Collections.Generic;
using Alcala.Juego;
using Alcala.Reglas;
using Godot;

namespace Alcala.Ui;

/// <summary>
/// Panel de conversación a la derecha de la pantalla, al estilo de Disco Elysium:
/// un registro que crece hacia abajo y las opciones numeradas al pie.
/// Se elige con el ratón o con las teclas 1 a 9.
/// </summary>
public partial class PanelDialogo : PanelContainer
{
    public const float FraccionAncho = 0.36f;

    /// <summary>El jugador ha elegido la opción con este índice de Ink (-1 = cerrar).</summary>
    public event Action<int>? OpcionElegida;

    private VBoxContainer registro = null!;
    private ScrollContainer desplazamiento = null!;
    private VBoxContainer opciones = null!;
    private Label titulo = null!;
    private readonly List<int> indicesVisibles = new();
    private Func<Ficha>? ficha;

    public bool Abierto => Visible;

    public override void _Ready()
    {
        Visible = false;
        AnchorLeft = 1f - FraccionAncho;
        AnchorRight = 1f;
        AnchorTop = 0f;
        AnchorBottom = 1f;
        OffsetLeft = OffsetRight = OffsetTop = OffsetBottom = 0;
        AddThemeStyleboxOverride("panel", Estilo.Caja(Estilo.Fondo, Estilo.Oro * new Color(1, 1, 1, 0.35f), 2));
        MouseFilter = MouseFilterEnum.Stop;

        var margen = new MarginContainer();
        foreach (string lado in new[] { "left", "right" })
            margen.AddThemeConstantOverride($"margin_{lado}", 44);
        margen.AddThemeConstantOverride("margin_top", 40);
        margen.AddThemeConstantOverride("margin_bottom", 36);
        AddChild(margen);

        var columna = new VBoxContainer();
        columna.AddThemeConstantOverride("separation", 18);
        margen.AddChild(columna);

        titulo = new Label { Text = "", Uppercase = true };
        titulo.AddThemeFontOverride("font", Estilo.Fuente("600-normal"));
        titulo.AddThemeFontSizeOverride("font_size", 22);
        titulo.AddThemeColorOverride("font_color", Estilo.Oro);
        columna.AddChild(titulo);

        desplazamiento = new ScrollContainer
        {
            SizeFlagsVertical = SizeFlags.ExpandFill,
            HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled,
        };
        columna.AddChild(desplazamiento);

        registro = new VBoxContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        registro.AddThemeConstantOverride("separation", 16);
        desplazamiento.AddChild(registro);

        columna.AddChild(new HSeparator());

        opciones = new VBoxContainer();
        opciones.AddThemeConstantOverride("separation", 6);
        columna.AddChild(opciones);
    }

    public void Abrir(string encabezado, Func<Ficha> obtenerFicha)
    {
        ficha = obtenerFicha;
        titulo.Text = encabezado;
        foreach (Node n in registro.GetChildren())
            n.QueueFree();
        Visible = true;
        Modulate = new Color(1, 1, 1, 0);
        CreateTween().TweenProperty(this, "modulate:a", 1f, 0.25f);
    }

    public void Cerrar()
    {
        Visible = false;
        LimpiarOpciones();
    }

    public void Mostrar(Paso paso)
    {
        foreach (Entrada e in paso.Entradas)
            Anadir(Formatear(e));

        LimpiarOpciones();
        if (paso.Terminado)
        {
            AnadirOpcion(-1, "[color=#" + Estilo.Hex(Estilo.PapelApagado) + "]Terminar la conversación[/color]", 1);
        }
        else
        {
            int n = 1;
            foreach (OpcionVista o in paso.Opciones)
                AnadirOpcion(o.Indice, FormatearOpcion(o), n++);
        }
        Callable.From(BajarDelTodo).CallDeferred();
    }

    /// <summary>Texto plano de todo el registro (para pruebas y depuración).</summary>
    public string TextoRegistro()
    {
        var partes = new List<string>();
        foreach (Node n in registro.GetChildren())
        {
            if (n is RichTextLabel r && !r.IsQueuedForDeletion())
                partes.Add(r.GetParsedText());
        }
        return string.Join("\n", partes);
    }

    public int OpcionesVisibles => indicesVisibles.Count;

    public override void _UnhandledKeyInput(InputEvent evento)
    {
        if (!Visible || evento is not InputEventKey { Pressed: true, Echo: false } tecla)
            return;
        int numero = tecla.Keycode switch
        {
            >= Key.Key1 and <= Key.Key9 => (int)(tecla.Keycode - Key.Key1),
            >= Key.Kp1 and <= Key.Kp9 => (int)(tecla.Keycode - Key.Kp1),
            Key.Space or Key.Enter or Key.KpEnter when indicesVisibles.Count == 1 => 0,
            _ => -1,
        };
        if (numero >= 0 && numero < indicesVisibles.Count)
        {
            Elegir(indicesVisibles[numero]);
            GetViewport().SetInputAsHandled();
        }
    }

    private void Elegir(int indice)
    {
        LimpiarOpciones();
        OpcionElegida?.Invoke(indice);
    }

    private string Formatear(Entrada entrada)
    {
        string papel = Estilo.Hex(Estilo.Papel);
        switch (entrada)
        {
            case EntradaLinea { Linea: var l } when l.EsNarracion:
                return $"[color=#{Estilo.Hex(Estilo.PapelApagado)}][i]{Escapar(l.Texto)}[/i][/color]";
            case EntradaLinea { Linea: var l }:
            {
                string colorNombre = Estilo.Hex(Estilo.Oro);
                try
                {
                    colorNombre = Estilo.Hex(Estilo.ColorFacultad(Facultades.Analizar(l.Hablante!)));
                }
                catch (FormatException)
                {
                    // No es una facultad: es un personaje.
                }
                return $"[color=#{colorNombre}][b]{Escapar(l.Hablante!)}[/b][/color]: [color=#{papel}]{Escapar(l.Texto)}[/color]";
            }
            case EntradaTirada { Resultado: var r }:
            {
                string c = Estilo.Hex(r.Exito ? Estilo.Exito : Estilo.Sangre);
                string veredicto = r.Critico ? "Éxito rotundo" : r.Pifia ? "Fracaso sin remedio" : r.Exito ? "Éxito" : "Fracaso";
                return $"[color=#{c}][{r.Facultad.Nombre()} · {Tirada.NombreDificultad(r.Dificultad)} {r.Dificultad}] {veredicto}[/color]"
                     + $"  [color=#{Estilo.Hex(Estilo.PapelApagado)}]({r.Dado1} + {r.Dado2} + {r.Bonificacion} = {r.Total})[/color]";
            }
            case EntradaPista { Pista: var p }:
                return $"[color=#{Estilo.Hex(Estilo.Oro)}]Anotado en el diario: {Escapar(p.Titulo)}[/color]";
            default:
                return "";
        }
    }

    private string FormatearOpcion(OpcionVista o)
    {
        if (o.Comprobacion is ComprobacionOpcion c && ficha is not null)
        {
            string color = Estilo.Hex(Estilo.ColorFacultad(c.Facultad));
            return $"[color=#{color}]{Escapar(c.Prefijo(ficha()))}[/color] {Escapar(o.Texto)}";
        }
        return Escapar(o.Texto);
    }

    private void Anadir(string bbcode)
    {
        if (bbcode.Length == 0)
            return;
        var etiqueta = NuevaEtiqueta(bbcode, 25);
        registro.AddChild(etiqueta);
        etiqueta.Modulate = new Color(1, 1, 1, 0);
        CreateTween().TweenProperty(etiqueta, "modulate:a", 1f, 0.35f);
    }

    private void AnadirOpcion(int indice, string bbcode, int numero)
    {
        indicesVisibles.Add(indice);
        var boton = new Button
        {
            Flat = true,
            FocusMode = FocusModeEnum.None,
            MouseDefaultCursorShape = CursorShape.PointingHand,
            SizeFlagsHorizontal = SizeFlags.ExpandFill,
            CustomMinimumSize = new Vector2(0, 40),
        };
        var etiqueta = NuevaEtiqueta($"[color=#{Estilo.Hex(Estilo.Sangre)}]{numero}.[/color] {bbcode}", 24);
        etiqueta.MouseFilter = MouseFilterEnum.Ignore;
        etiqueta.SetAnchorsPreset(LayoutPreset.FullRect);
        boton.AddChild(etiqueta);
        boton.Resized += () => boton.CustomMinimumSize = new Vector2(0, etiqueta.GetContentHeight() + 8);
        boton.MouseEntered += () => etiqueta.Modulate = new Color(1.25f, 1.15f, 1f);
        boton.MouseExited += () => etiqueta.Modulate = Colors.White;
        boton.Pressed += () => Elegir(indice);
        opciones.AddChild(boton);
    }

    private static RichTextLabel NuevaEtiqueta(string bbcode, int tamano)
    {
        var r = new RichTextLabel
        {
            BbcodeEnabled = true,
            FitContent = true,
            ScrollActive = false,
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
            SizeFlagsHorizontal = SizeFlags.ExpandFill,
            Text = bbcode,
        };
        r.AddThemeFontOverride("normal_font", Estilo.Fuente("400-normal"));
        r.AddThemeFontOverride("italics_font", Estilo.Fuente("400-italic"));
        r.AddThemeFontOverride("bold_font", Estilo.Fuente("700-normal"));
        r.AddThemeFontSizeOverride("normal_font_size", tamano);
        r.AddThemeFontSizeOverride("italics_font_size", tamano);
        r.AddThemeFontSizeOverride("bold_font_size", tamano);
        r.AddThemeColorOverride("default_color", Estilo.Papel);
        return r;
    }

    private void LimpiarOpciones()
    {
        indicesVisibles.Clear();
        foreach (Node n in opciones.GetChildren())
            n.QueueFree();
    }

    private void BajarDelTodo()
    {
        var barra = desplazamiento.GetVScrollBar();
        CreateTween().TweenProperty(desplazamiento, "scroll_vertical", (int)barra.MaxValue, 0.3f);
    }

    /// <summary>Evita que un corchete escrito en Ink se interprete como BBCode.</summary>
    private static string Escapar(string s) => s.Replace("[", "[lb]");
}
