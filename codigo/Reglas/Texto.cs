using System.Globalization;
using System.Text;

namespace Alcala.Reglas;

public static class Texto
{
    public static string SinTildes(string s)
    {
        var sb = new StringBuilder(s.Length);
        foreach (char c in s.Normalize(NormalizationForm.FormD))
        {
            if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark)
                sb.Append(c);
        }
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }
}
