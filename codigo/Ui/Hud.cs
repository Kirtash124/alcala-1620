using Godot;

namespace Alcala.Ui;

/// <summary>Rótulo bajo el cursor, ayuda de teclas y avisos breves.</summary>
public partial class Hud : Control
{
    private Label rotulo = null!;
    private Label aviso = null!;
    private Tween? tweenAviso;

    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;

        rotulo = new Label { Visible = false, MouseFilter = MouseFilterEnum.Ignore };
        rotulo.AddThemeFontOverride("font", Estilo.Fuente("600-normal"));
        rotulo.AddThemeFontSizeOverride("font_size", 26);
        rotulo.AddThemeColorOverride("font_color", Estilo.Papel);
        rotulo.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.9f));
        rotulo.AddThemeConstantOverride("outline_size", 8);
        AddChild(rotulo);

        var ayuda = new Label
        {
            Text = "Clic: andar o examinar   ·   D: diario   ·   F5: guardar   ·   F9: cargar",
            MouseFilter = MouseFilterEnum.Ignore,
        };
        ayuda.AddThemeFontSizeOverride("font_size", 20);
        ayuda.AddThemeColorOverride("font_color", new Color(1, 1, 1, 0.55f));
        ayuda.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.8f));
        ayuda.AddThemeConstantOverride("outline_size", 6);
        ayuda.SetAnchorsPreset(LayoutPreset.BottomLeft);
        ayuda.Position = new Vector2(24, -44);
        ayuda.GrowVertical = GrowDirection.Begin;
        AddChild(ayuda);

        aviso = new Label { Modulate = new Color(1, 1, 1, 0), MouseFilter = MouseFilterEnum.Ignore };
        aviso.AddThemeFontOverride("font", Estilo.Fuente("600-normal"));
        aviso.AddThemeFontSizeOverride("font_size", 28);
        aviso.AddThemeColorOverride("font_color", Estilo.Oro);
        aviso.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.9f));
        aviso.AddThemeConstantOverride("outline_size", 8);
        aviso.SetAnchorsPreset(LayoutPreset.CenterTop);
        aviso.Position = new Vector2(0, 40);
        aviso.GrowHorizontal = GrowDirection.Both;
        aviso.HorizontalAlignment = HorizontalAlignment.Center;
        AddChild(aviso);
    }

    public void MostrarRotulo(string? texto, Vector2 posicionPantalla)
    {
        if (string.IsNullOrEmpty(texto))
        {
            rotulo.Visible = false;
            return;
        }
        rotulo.Text = texto;
        rotulo.Visible = true;
        rotulo.Position = posicionPantalla + new Vector2(22, 18);
    }

    public void Avisar(string texto)
    {
        aviso.Text = texto;
        tweenAviso?.Kill();
        tweenAviso = CreateTween();
        tweenAviso.TweenProperty(aviso, "modulate:a", 1f, 0.2f);
        tweenAviso.TweenInterval(1.8f);
        tweenAviso.TweenProperty(aviso, "modulate:a", 0f, 0.6f);
    }
}
