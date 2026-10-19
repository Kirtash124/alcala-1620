using Alcala.Reglas;
using Godot;

namespace Alcala.Ui;

/// <summary>Diario de la pesquisa: las pistas reunidas. Se abre y cierra con la tecla D.</summary>
public partial class Diario : PanelContainer
{
    private VBoxContainer lista = null!;
    private Label vacio = null!;

    public override void _Ready()
    {
        Visible = false;
        AnchorLeft = 0.2f;
        AnchorRight = 0.64f;
        AnchorTop = 0.1f;
        AnchorBottom = 0.9f;
        OffsetLeft = OffsetRight = OffsetTop = OffsetBottom = 0;
        AddThemeStyleboxOverride("panel", Estilo.Caja(new Color(0.12f, 0.10f, 0.08f, 0.97f), Estilo.Oro, 3));

        var margen = new MarginContainer();
        foreach (string lado in new[] { "left", "right", "top", "bottom" })
            margen.AddThemeConstantOverride($"margin_{lado}", 40);
        AddChild(margen);

        var columna = new VBoxContainer();
        columna.AddThemeConstantOverride("separation", 14);
        margen.AddChild(columna);

        var titulo = new Label { Text = "Diario de la pesquisa" };
        titulo.AddThemeFontOverride("font", Estilo.Fuente("600-normal"));
        titulo.AddThemeFontSizeOverride("font_size", 34);
        titulo.AddThemeColorOverride("font_color", Estilo.Oro);
        columna.AddChild(titulo);
        columna.AddChild(new HSeparator());

        var scroll = new ScrollContainer { SizeFlagsVertical = SizeFlags.ExpandFill, HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled };
        columna.AddChild(scroll);
        lista = new VBoxContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        lista.AddThemeConstantOverride("separation", 18);
        scroll.AddChild(lista);

        vacio = new Label { Text = "Nada anotado todavía.", AutowrapMode = TextServer.AutowrapMode.WordSmart };
        vacio.AddThemeColorOverride("font_color", Estilo.PapelApagado);
        lista.AddChild(vacio);

        var pie = new Label { Text = "D o Esc para cerrar", HorizontalAlignment = HorizontalAlignment.Right };
        pie.AddThemeColorOverride("font_color", Estilo.PapelApagado);
        pie.AddThemeFontSizeOverride("font_size", 20);
        columna.AddChild(pie);
    }

    public void Rellenar(Pesquisa pesquisa)
    {
        foreach (Node n in lista.GetChildren())
        {
            if (n != vacio)
                n.QueueFree();
        }
        vacio.Visible = pesquisa.Pistas.Count == 0;
        foreach (Pista p in pesquisa.Pistas)
        {
            var r = new RichTextLabel
            {
                BbcodeEnabled = true,
                FitContent = true,
                ScrollActive = false,
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
                SizeFlagsHorizontal = SizeFlags.ExpandFill,
                Text = $"[color=#{Estilo.Hex(Estilo.Oro)}][b]{p.Titulo}[/b][/color]\n{p.Texto}",
            };
            r.AddThemeFontOverride("normal_font", Estilo.Fuente("400-normal"));
            r.AddThemeFontOverride("bold_font", Estilo.Fuente("700-normal"));
            r.AddThemeFontSizeOverride("normal_font_size", 25);
            r.AddThemeFontSizeOverride("bold_font_size", 25);
            r.AddThemeColorOverride("default_color", Estilo.Papel);
            lista.AddChild(r);
        }
    }

    public void Alternar(Pesquisa pesquisa)
    {
        if (!Visible)
            Rellenar(pesquisa);
        Visible = !Visible;
    }
}
