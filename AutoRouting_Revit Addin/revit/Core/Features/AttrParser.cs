using Newtonsoft.Json.Linq;

namespace SARAI.Core.Import.Utils
{
    public static class AttrParser
    {
        public static string StringParser(JObject Attr, string key)
        {
            return Attr[key].Value<string>();
        }
        public static double DoubleParser(JObject Attr, string key)
        {
            return Attr[key].Value<double>();
        }
    }
}
