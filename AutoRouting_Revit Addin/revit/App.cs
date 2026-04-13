using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using static SARAI.Commons.Utils.CreateUiButton;
using System.IO;
using SARAI.Core;
using SARAI.Commons;


namespace SARAI
{
    public class App : IExternalApplication
    {
        public const string TITLE = "SARAI";

        public ExternalEvent externalEvent;

        public Result OnStartup(UIControlledApplication app)
        {
            try
            {
                // SmartRouting AI Panel.
                RibbonPanel panel_SLZ = app.CreateRibbonPanel(Tab.AddIns, "SLZ");
                CreateButton(panel_SLZ, "Crop View", "Command.testCommand", "test", "auto-level-and-grid-crop.ico", 1);
                RibbonPanel panel_SARAI = app.CreateRibbonPanel(Tab.AddIns, "DS AutoRouting");
                CreateButton(panel_SARAI, "Launch", "Launch", "Click to run SARAI", "icon_32X32.ico", 1);
                CreateButton(panel_SARAI, "Draft Import", "VImport", "Draft Pipe Import", "Pipe1.ico", 1);
                CreateButton(panel_SARAI, "Detail Import", "RImport", "Detail Pipe Import (for Foreline)", "Pipq2.ico", 1);

            }
            catch (Exception ex)
            {
                TaskDialog.Show("Addin Error", $"SARAI Addin Error: {ex.Message}");
            }
            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication app)
        {
            return Result.Succeeded;
        }
    }

    [Transaction(TransactionMode.Manual)]
    public class Launch : IExternalCommand
    {
        public Result Execute(ExternalCommandData revit, ref string message, ElementSet elements)
        {
            string appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);

            string clientPath = @"..\Local\Programs\smartrouting-ai\SmartRouting AI.exe";

            string path = Path.GetFullPath(Path.Combine(appDataPath, clientPath));

            LaunchApp launch = new LaunchApp(path);

            launch.Run();

            return Result.Succeeded;
        }
    }

    // SARAI Json File Draft Import
    [Transaction(TransactionMode.Manual)]
    public class VImport : IExternalCommand
    {
        public Result Execute(ExternalCommandData revit, ref string message, ElementSet elements)
        {
            // 현재 작업중인 프로젝트 읽기
            Document doc = revit.Application.ActiveUIDocument.Document;

            // 파읽 읽기
            FileReader file_reader = new FileReader();

            if (file_reader.ReadPath != null)
            {
                string jsonText = File.ReadAllText(file_reader.ReadPath);

                //Routing 생성
                VImportApp Pipe_create = new VImportApp(revit, 304.8);
                Pipe_create.Run(jsonText);
            }
            return Result.Succeeded;
        }
    }

    // SARAI Json File Detail Import
    [Transaction(TransactionMode.Manual)]
    public class RImport : IExternalCommand
    {
        public Result Execute(ExternalCommandData revit, ref string message, ElementSet elements)
        {
            // 현재 작업중인 프로젝트 읽기
            Document doc = revit.Application.ActiveUIDocument.Document;

            Window window = new Window();

            if (window.ShowDialog() == true)
            {
                double value = window.SelectedValue;
                if (value == 0) 
                {
                    TaskDialog.Show("페이즈 데이터 삽입 필요", "해당 페이즈에 대한 Middle Foreline의 높이 정보가 없습니다.");
                }
                else
                {
                    FileReader file_reader = new FileReader();

                    if (file_reader.ReadPath != null)
                    {
                        string jsonText = File.ReadAllText(file_reader.ReadPath);

                        //Routing 생성
                        RImportApp Pipe_create = new RImportApp(revit, value, 304.8);
                        Pipe_create.Run(jsonText);
                    }
                }
            }
            return Result.Succeeded;
        }
    }
}