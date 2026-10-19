using System;
using Alcala.Juego;
using Xunit;

namespace Alcala.Reglas.Pruebas;

public class PruebasMarcha
{
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
