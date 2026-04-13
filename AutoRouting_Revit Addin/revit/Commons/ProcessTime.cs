using Autodesk.Revit.UI;
using System;
using System.Diagnostics;

namespace SARAI.Commons
{
    public class ProcessTime
    {
        private readonly string Process_Name;
        private readonly Stopwatch _Stopwatch;

        public ProcessTime(string process_name)
        {
            this.Process_Name = process_name;
            this._Stopwatch = new Stopwatch();
        }

        public void Start()
        {
            _Stopwatch.Start();
        }

        public void Stop()
        {
            _Stopwatch.Stop();
            TimeSpan processingTime = _Stopwatch.Elapsed;
            int minutes = processingTime.Minutes;
            double seconds = processingTime.TotalSeconds - (minutes * 60);
            string time_message = Process_Name + " Processing Time";
            TaskDialog.Show(time_message, time_message + $": {minutes} minutes {seconds:F3} seconds");
        }
    }
}

