using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.Attributes;
using System;
using System.Diagnostics;
using System.IO;

namespace SARAI.Command
{
    [Transaction(TransactionMode.Manual)]
    internal class LaunchCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData revit, ref string message, ElementSet elements)
        {
            try

            {
                // Get the solution directory
                string solutionPath = Directory.GetCurrentDirectory();

                // Path to the batch file
                string batFilePath = Path.Combine(solutionPath, "../../web_client_launcher.bat"); // 파일 경로 지정

                // Verify the batch file exists
                if (!File.Exists(batFilePath))
                {
                    TaskDialog.Show("Error", "Batch file not found: " + batFilePath);
                    return Result.Failed;
                }

                // Process configuration to keep the terminal open
                ProcessStartInfo processStartInfo = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/K \"{batFilePath}\"", // Use /K to keep the terminal open
                    WorkingDirectory = Path.GetDirectoryName(batFilePath),
                    UseShellExecute = true, // Allows cmd execution
                    CreateNoWindow = false // Show the command window
                };

                // Start the process
                Process process = Process.Start(processStartInfo);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", $"An error occurred: {ex.Message}");
                return Result.Failed;
            }
        }
    }
}
