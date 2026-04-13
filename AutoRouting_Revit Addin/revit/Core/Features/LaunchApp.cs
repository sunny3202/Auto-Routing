using System.Diagnostics;

namespace SARAI.Core
{
    public class LaunchApp
    {
        private readonly string path;

        public LaunchApp(string Path)
        {
            this.path = Path;
        }

        public void Run()
        {
            Process.Start(path);
        }
    }
}