using System;
using System.Numerics;
using Alcala.Juego;
using Xunit;

namespace Alcala.Reglas.Pruebas;

public class PruebasMarcha
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void LosTriangulosDelTroncoYLasMangasNoSeInvierten(bool espalda)
    {
        for (int fase = 0; fase < 32; fase++)
        {
            var gesto = new GestoMarcha(new Vector2(96, 190), espalda,
                Vector2.Normalize(new Vector2(2, espalda ? -1 : 1)), fase / 32f, 1, 64, 5);
            for (int y = 32; y < 112; y += 4)
            for (int x = 0; x < 96; x += 4)
            {
                Vector2 a = gesto.Transformar(new Vector2(x, y));
                Vector2 b = gesto.Transformar(new Vector2(x + 4, y));
                Vector2 c = gesto.Transformar(new Vector2(x, y + 4));
                Vector2 ab = b - a;
                Vector2 ac = c - a;
                Assert.True(ab.X * ac.Y - ab.Y * ac.X > 0,
                    $"triángulo invertido en {x},{y}, fase {fase}");
            }
        }
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void ElGestoConservaElDibujoExactoAlDetenerse(bool espalda)
    {
        var gesto = new GestoMarcha(new Vector2(96, 190), espalda,
            Vector2.Normalize(new Vector2(2, 1)), 0.37f, 0, 64, 5);
        for (int y = 0; y <= 190; y += 5)
        for (int x = 0; x <= 96; x += 4)
        {
            Vector2 p = new(x, y);
            Assert.InRange(Vector2.Distance(p, gesto.Transformar(p)), 0, 0.0001f);
        }
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void LaCabezaYElSombreroNoSeEstiranAlAndar(bool espalda)
    {
        Vector2 a = new(45, 10);
        Vector2 b = new(61, 39);
        float distancia = Vector2.Distance(a, b);
        for (int i = 0; i < 40; i++)
        {
            var gesto = new GestoMarcha(new Vector2(96, 190), espalda,
                Vector2.Normalize(new Vector2(2, 1)), i / 40f, 1, 64, 5);
            Assert.InRange(MathF.Abs(Vector2.Distance(gesto.Transformar(a), gesto.Transformar(b)) - distancia), 0, 0.0001f);
        }
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void ElTroncoYLosBrazosNoArrastranLasSuelas(bool espalda)
    {
        Vector2 direccion = Vector2.Normalize(new Vector2(2, espalda ? -1 : 1));
        Vector2 p = new(35, 186);
        for (int i = 0; i < 40; i++)
        {
            float fase = i / 40f;
            var gesto = new GestoMarcha(new Vector2(96, 190), espalda, direccion, fase, 1, 64, 5);
            var pie = CicloMarcha.Evaluar(fase, 64, 5);
            Vector2 esperado = p + direccion * pie.Avance - Vector2.UnitY * pie.Elevacion;
            Assert.InRange(Vector2.Distance(esperado, gesto.Transformar(p)), 0, 0.0001f);
        }
    }

    [Fact]
    public void ElPieApoyadoPermaneceFijoMientrasAvanzaElCuerpo()
    {
        const float longitud = 64;
        float antes = CicloMarcha.Evaluar(0.1f, longitud, 5).Avance;
        float despues = CicloMarcha.Evaluar(0.4f, longitud, 5).Avance;
        float recorrido = longitud * (0.4f - 0.1f);
        Assert.InRange(MathF.Abs(recorrido + despues - antes), 0, 0.0001f);
        Assert.Equal(0, CicloMarcha.Evaluar(0.4f, longitud, 5).Elevacion);
    }

    [Fact]
    public void SiempreHayAlMenosUnPieApoyado()
    {
        for (int i = 0; i < 1000; i++)
        {
            float fase = i / 1000f;
            var a = CicloMarcha.Evaluar(fase, 64, 5);
            var b = CicloMarcha.Evaluar(fase + 0.5f, 64, 5);
            Assert.True(a.Elevacion <= 0.0001f || b.Elevacion <= 0.0001f);
        }
    }

    [Theory]
    [InlineData(0f)]
    [InlineData(0.6f)]
    public void NoSaltaAlCambiarEntreApoyoYVuelo(float fase)
    {
        var antes = CicloMarcha.Evaluar(fase - 0.00001f, 64, 5);
        var despues = CicloMarcha.Evaluar(fase + 0.00001f, 64, 5);
        Assert.InRange(MathF.Abs(antes.Avance - despues.Avance), 0, 0.002f);
        Assert.InRange(MathF.Abs(antes.Elevacion - despues.Elevacion), 0, 0.002f);
    }
}
