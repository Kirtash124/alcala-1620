using System;
using System.Numerics;

namespace Alcala.Juego;

/// <summary>
/// Pesos del dibujo del Pesquisidor: pelvis, hombros, cabeza, brazos y ferreruelo.
/// La cabeza se transforma como una pieza rígida para conservar sus facciones.
/// </summary>
public readonly struct GestoMarcha
{
    private readonly Vector2 tamano;
    private readonly bool espalda;
    private readonly float intensidad;
    private readonly float fase;
    private readonly float separacion;
    private readonly Vector2 cadera;
    private readonly Vector2 hombros;
    private readonly Vector2 cuello;
    private readonly Vector2 cuelloMovido;
    private readonly Vector2 apoyo;
    private readonly Vector2 pieIzquierdo;
    private readonly Vector2 pieDerecho;
    private readonly Vector2 direccion;
    private readonly float giroCadera;
    private readonly float giroHombros;
    private readonly float giroCabeza;

    public GestoMarcha(Vector2 tamano, bool espalda, Vector2 direccion,
                       float fase, float intensidad, float longitud, float altura)
    {
        this = default;
        this.tamano = tamano;
        this.espalda = espalda;
        this.direccion = direccion;
        this.intensidad = intensidad;
        this.fase = (fase - MathF.Floor(fase)) * MathF.Tau;
        separacion = tamano.X * (espalda ? 0.45f : 0.51f);
        cadera = tamano * new Vector2(espalda ? 0.52f : 0.53f, espalda ? 0.67f : 0.62f);
        hombros = tamano * new Vector2(0.52f, 0.34f);
        cuello = tamano * new Vector2(espalda ? 0.55f : 0.57f, 0.255f);

        float alternancia = MathF.Sin(this.fase);
        giroCadera = alternancia * 0.025f * intensidad;
        giroHombros = -alternancia * 0.05f * intensidad;
        giroCabeza = alternancia * 0.004f * intensidad;
        Vector2 lateral = Vector2.Normalize(new Vector2(-direccion.Y * 2f, direccion.X * 0.5f));
        apoyo = lateral * (alternancia * 1.1f * intensidad)
              + new Vector2(0, -(1f - MathF.Cos(this.fase * 2f)) * 0.9f * intensidad);

        var izquierdo = CicloMarcha.Evaluar(fase, longitud, altura);
        var derecho = CicloMarcha.Evaluar(fase + 0.5f, longitud, altura);
        pieIzquierdo = (direccion * izquierdo.Avance - Vector2.UnitY * izquierdo.Elevacion) * intensidad;
        pieDerecho = (direccion * derecho.Avance - Vector2.UnitY * derecho.Elevacion) * intensidad;
        cuelloMovido = TransformarTronco(cuello);
    }

    public Vector2 Transformar(Vector2 p)
    {
        float x = p.X / tamano.X;
        float y = p.Y / tamano.Y;
        bool izquierda = p.X < separacion;
        float suela = tamano.Y * (espalda
            ? (izquierda ? 0.90f : 0.97f)
            : (izquierda ? 0.98f : 0.87f));
        float brazoIzquierdo = PesoBrazo(x, y, true);
        float brazoDerecho = PesoBrazo(x, y, false);
        float pesoPie = Math.Clamp((p.Y - cadera.Y) / (suela - cadera.Y - 9f), 0f, 1f)
                      * (1f - MathF.Max(brazoIzquierdo, brazoDerecho));

        Vector2 tronco = TransformarTronco(p);
        Vector2 cabeza = cuelloMovido + Rotar(p - cuello, giroCabeza);
        float pesoCabeza = 1f - Suave(0.22f, 0.285f, y);
        Vector2 cuerpo = Vector2.Lerp(tronco, cabeza, pesoCabeza);
        Vector2 resultado = Vector2.Lerp(cuerpo, p, pesoPie)
                          + (izquierda ? pieIzquierdo : pieDerecho) * pesoPie;

        // Cada brazo acompaña a la pierna contraria. Los hombros arrastran el
        // brazo desde arriba y el desplazamiento aumenta hacia el guante.
        float pendulo = MathF.Cos(fase - 0.12f) * 8f * intensidad;
        resultado += direccion * pendulo * (brazoDerecho - brazoIzquierdo);

        // El borde libre de la capa responde después que los hombros. La zona
        // central de la ropilla conserva sus botones y su volumen.
        float borde = Suave(0.12f, 0.30f, MathF.Abs(x - 0.51f));
        float capa = Suave(0.28f, 0.47f, y) * (1f - Suave(0.51f, 0.57f, y));
        capa *= espalda ? 0.35f + borde * 0.65f : borde;
        resultado += (direccion * (-MathF.Sin(fase - 0.65f) * 2.2f)
                    + new Vector2(0, MathF.Sin(fase * 2f - 0.5f) * 0.45f))
                    * capa * intensidad;
        return resultado;
    }

    private Vector2 TransformarTronco(Vector2 p)
    {
        float y = p.Y / tamano.Y;
        Vector2 pelvis = cadera + Rotar(p - cadera, giroCadera);
        Vector2 pecho = hombros + Rotar(p - hombros, giroHombros);
        float pesoHombros = 1f - Suave(0.32f, espalda ? 0.67f : 0.62f, y);
        return Vector2.Lerp(pelvis, pecho, pesoHombros) + apoyo;
    }

    private float PesoBrazo(float x, float y, bool izquierdo)
    {
        float recorrido = Suave(0.40f, 0.60f, y);
        float centro = izquierdo
            ? (espalda ? 0.255f + recorrido * 0.015f : 0.235f + recorrido * 0.115f)
            : 0.79f + recorrido * 0.035f;
        float ancho = 1f - Suave(0.02f, 0.16f, MathF.Abs(x - centro));
        float finGuante = espalda ? 0.63f : 0.61f;
        return ancho * Suave(0.39f, 0.55f, y) * (1f - Suave(finGuante, finGuante + 0.06f, y));
    }

    private static Vector2 Rotar(Vector2 p, float angulo)
    {
        float coseno = MathF.Cos(angulo);
        float seno = MathF.Sin(angulo);
        return new Vector2(p.X * coseno - p.Y * seno, p.X * seno + p.Y * coseno);
    }

    private static float Suave(float inicio, float fin, float valor)
    {
        float t = Math.Clamp((valor - inicio) / (fin - inicio), 0f, 1f);
        return t * t * (3f - 2f * t);
    }
}
