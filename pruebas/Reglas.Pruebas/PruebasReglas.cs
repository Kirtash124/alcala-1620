using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace Alcala.Reglas.Pruebas;

internal sealed class DadosTrucados : IDados
{
    private readonly Queue<int> valores;
    public DadosTrucados(params int[] valores) => this.valores = new Queue<int>(valores);
    public int D6() => valores.Dequeue();
}

public class PruebasTirada
{
    [Fact]
    public void SumaDadosYFacultadContraDificultad()
    {
        var r = Tirada.Resolver(Facultad.Entendimiento, 3, 10, new DadosTrucados(4, 3));
        Assert.Equal(10, r.Total);
        Assert.True(r.Exito);

        var f = Tirada.Resolver(Facultad.Entendimiento, 3, 11, new DadosTrucados(4, 3));
        Assert.False(f.Exito);
    }

    [Fact]
    public void DobleSeisSiempreAcierta()
    {
        var r = Tirada.Resolver(Facultad.Memoria, 1, 30, new DadosTrucados(6, 6));
        Assert.True(r.Exito);
        Assert.True(r.Critico);
    }

    [Fact]
    public void DobleUnoSiempreFalla()
    {
        var r = Tirada.Resolver(Facultad.Memoria, 6, 2, new DadosTrucados(1, 1));
        Assert.False(r.Exito);
        Assert.True(r.Pifia);
    }

    [Theory]
    [InlineData(0, 2, 35.0 / 36)]   // todo acierta salvo el doble uno
    [InlineData(0, 40, 1.0 / 36)]   // solo el doble seis
    [InlineData(3, 10, 21.0 / 36)]  // necesita 7 o más con 2d6
    [InlineData(4, 12, 15.0 / 36)]  // necesita 8 o más
    public void ProbabilidadExacta(int valor, int dificultad, double esperada)
    {
        Assert.Equal(esperada, Tirada.Probabilidad(valor, dificultad), 10);
    }

    [Fact]
    public void LaProbabilidadCoincideConLaSimulacion()
    {
        var dados = new DadosAleatorios(1620);
        int exitos = Enumerable.Range(0, 200_000)
            .Count(_ => Tirada.Resolver(Facultad.Imaginativa, 4, 12, dados).Exito);
        Assert.Equal(Tirada.Probabilidad(4, 12), exitos / 200_000.0, 2);
    }

    [Fact]
    public void RechazaDadosImposibles()
    {
        Assert.Throws<InvalidOperationException>(() =>
            Tirada.Resolver(Facultad.Memoria, 2, 10, new DadosTrucados(7, 1)));
    }
}

public class PruebasFacultades
{
    [Theory]
    [InlineData("entendimiento", Facultad.Entendimiento)]
    [InlineData("MEMORIA", Facultad.Memoria)]
    [InlineData("Imaginación", Facultad.Imaginativa)]
    [InlineData(" imaginativa ", Facultad.Imaginativa)]
    public void AnalizaNombresComoSeEscribenEnInk(string texto, Facultad esperada)
    {
        Assert.Equal(esperada, Facultades.Analizar(texto));
    }

    [Fact]
    public void FacultadDesconocidaFallaConMensajeClaro()
    {
        var ex = Assert.Throws<FormatException>(() => Facultades.Analizar("voluntad"));
        Assert.Contains("voluntad", ex.Message);
    }

    [Fact]
    public void LaFichaLimitaLosValores()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new Ficha(0, 2, 3));
        Assert.Throws<ArgumentOutOfRangeException>(() => new Ficha(2, 7, 3));
    }
}

public class PruebasDialogo
{
    [Fact]
    public void SeparaHablanteYTexto()
    {
        var l = LineaDialogo.Analizar("ALGUACIL: Vuesa merced llega tarde.");
        Assert.Equal("ALGUACIL", l.Hablante);
        Assert.Equal("Vuesa merced llega tarde.", l.Texto);
    }

    [Fact]
    public void AdmiteTildesYEspaciosEnElNombre()
    {
        var l = LineaDialogo.Analizar("MUJER DEL BALCÓN: ¡Ladrones!");
        Assert.Equal("MUJER DEL BALCÓN", l.Hablante);
    }

    [Fact]
    public void SinNombreEnMayusculasEsNarracion()
    {
        Assert.True(LineaDialogo.Analizar("El farol tiembla: algo se mueve.").EsNarracion);
        Assert.True(LineaDialogo.Analizar("Dijo: «no».").EsNarracion);
    }

    [Fact]
    public void LeeLaComprobacionDeUnaOpcion()
    {
        var c = ComprobacionOpcion.DesdeEtiquetas(new[] { "otra", "tirada: entendimiento 10" });
        Assert.NotNull(c);
        Assert.Equal(Facultad.Entendimiento, c!.Value.Facultad);
        Assert.Equal(10, c.Value.Dificultad);
    }

    [Fact]
    public void OpcionSinComprobacion()
    {
        Assert.Null(ComprobacionOpcion.DesdeEtiquetas(new[] { "sin_tirada" }));
    }

    [Fact]
    public void PrefijoConProbabilidad()
    {
        var c = new ComprobacionOpcion(Facultad.Entendimiento, 10);
        Assert.Equal("[Entendimiento · Mediana 10 · 58 %]", c.Prefijo(Ficha.Pesquisidor()));
    }
}

public class PruebasPesquisaYGuardado
{
    [Fact]
    public void NoDuplicaPistas()
    {
        var p = new Pesquisa();
        int avisos = 0;
        p.PistaNueva += _ => avisos++;
        Assert.True(p.Anotar(new Pista("cera", "Cera negra", "Gotas junto a la mano.")));
        Assert.False(p.Anotar(new Pista("cera", "Cera negra", "Otra vez.")));
        Assert.Single(p.Pistas);
        Assert.Equal(1, avisos);
    }

    [Fact]
    public void GuardarYCargarConservaTodo()
    {
        var ficha = Ficha.Pesquisidor();
        var pesquisa = new Pesquisa();
        pesquisa.Anotar(new Pista("cera", "Cera negra", "Gotas junto a la mano, aún blandas."));

        string json = Guardado.AJson(Guardado.Capturar("calle_mayor", 812.5f, 990f, ficha, pesquisa, "{\"ink\":1}"));
        EstadoPartida leido = Guardado.DesdeJson(json);

        var ficha2 = new Ficha(1, 1, 1);
        var pesquisa2 = new Pesquisa();
        Guardado.Aplicar(leido, ficha2, pesquisa2);

        Assert.Equal("calle_mayor", leido.Lugar);
        Assert.Equal(812.5f, leido.JugadorX);
        Assert.Equal("{\"ink\":1}", leido.EstadoInk);
        Assert.Equal(4, ficha2[Facultad.Imaginativa]);
        Assert.Equal("Gotas junto a la mano, aún blandas.", pesquisa2.Pistas.Single().Texto);
    }
}
