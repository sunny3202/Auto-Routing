using Autodesk.Revit.UI;
using System;
using Autodesk.Revit.DB;
using Newtonsoft.Json.Linq;
using View = Autodesk.Revit.DB.View;
using System.Linq;
using Autodesk.Revit.DB.Plumbing;
using System.Collections.Generic;

namespace SARAI.Core
{
    public class VImportApp
    {
        private readonly ExternalCommandData revit;
        private readonly double Scaler;

        public VImportApp(ExternalCommandData Revit, double scaler)
        {
            this.revit = Revit;
            this.Scaler = scaler;
        }

        public void Run(string jsonText)
        {
            Document Doc = revit.Application.ActiveUIDocument.Document;
            View activeView = revit.Application.ActiveUIDocument.ActiveView;

            JArray jsonArray = JArray.Parse(jsonText);

            foreach (JObject jsonObj in jsonArray.Cast<JObject>())
            {
                double diameter = jsonObj["diameter"].Value<double>() / (Scaler);
                JObject attr = (JObject)jsonObj["attr"];
                string Eqid_value = (string)attr["equip_id"];
                string Chamber_value = (string)attr["chamber"];
                string Chamber_index_value = (string)attr["chamber_index"];
                JArray startArray = (JArray)jsonObj["start"];
                double start_x = startArray[0].Value<double>();
                double start_y = startArray[1].Value<double>();
                double start_z = startArray[2].Value<double>();
                XYZ start_XYZ = new XYZ(start_x, start_y, start_z) / (Scaler);

                JArray endArray = (JArray)jsonObj["end"];
                double end_x = endArray[0].Value<double>();
                double end_y = endArray[1].Value<double>();
                double end_z = endArray[2].Value<double>();
                XYZ end_XYZ = new XYZ(end_x, end_y, end_z) / (Scaler);

                JArray pathArray = (JArray)jsonObj["path"];
                List<XYZ> pathPoints = new List<XYZ>();

                foreach (JArray point in pathArray)
                {
                    double path_x = point[0].Value<double>();
                    double path_y = point[1].Value<double>();
                    double path_z = point[2].Value<double>();
                    XYZ path_XYZ = new XYZ(path_x, path_y, path_z) / (Scaler);
                    pathPoints.Add(path_XYZ);
                }

                ElementId pipeTypeId = new FilteredElementCollector(Doc)
                    .OfClass(typeof(PipeType))
                    .Cast<PipeType>()
                    .FirstOrDefault(p => p.Name == "Test_pipe")?.Id ?? throw new Exception("PipeType not found");

                ElementId systemTypeId = new FilteredElementCollector(Doc)
                    .OfClass(typeof(PipingSystemType))
                    .Cast<PipingSystemType>()
                    .FirstOrDefault(p => p.Name == "Domestic Cold Water")?.Id ?? throw new Exception("SystemType not found");

                Level level = new FilteredElementCollector(Doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name == "Level 1") ?? throw new Exception("Level not found");

                using (Transaction tx = new Transaction(Doc, "Draw Smart Pipe with Elbows"))
                {
                    tx.Start();

                    List<Pipe> createdPipes = new List<Pipe>();

                    XYZ segmentStart = pathPoints[0];
                    XYZ lastDirection = null;

                    for (int i = 1; i < pathPoints.Count; i++)
                    {
                        Pipe pipe = Pipe.Create(Doc, systemTypeId, pipeTypeId, level.Id, pathPoints[i], pathPoints[i - 1]);
                        pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(diameter);
                        createdPipes.Add(pipe);
                    }

                    foreach (Pipe pipe in createdPipes)
                    {
                        Parameter Eqid = pipe.LookupParameter("Eqid");
                        Parameter Chamber = pipe.LookupParameter("Chamber");
                        Parameter Chamber_index = pipe.LookupParameter("Chamber_index");

                        Eqid.Set(Eqid_value);
                        Chamber.Set(Chamber_value);
                        Chamber_index.Set(Chamber_index_value);
                    }

                    // 엘보우 연결
                    for (int i = 0; i < createdPipes.Count - 1; i++)
                    {
                        Pipe pipe1 = createdPipes[i];
                        Pipe pipe2 = createdPipes[i + 1];

                        Connector conn1 = GetConnectorClosestTo(pipe1, pipe2);
                        Connector conn2 = GetConnectorClosestTo(pipe2, pipe1);

                        if (conn1 != null && conn2 != null && conn1.Origin.IsAlmostEqualTo(conn2.Origin))
                        {
                            try
                            {
                                Doc.Create.NewElbowFitting(conn1, conn2);
                            }
                            catch (Autodesk.Revit.Exceptions.InvalidOperationException)
                            {
                                // TaskDialog.Show("Warning", "Elbow 생성 실패: " + ex.Message);
                            }
                        }
                    }

                    tx.Commit();
                }
            }
        }

        private Connector GetConnectorClosestTo(Pipe pipe, Pipe targetPipe)
        {
            ConnectorSet connectors = pipe.ConnectorManager.Connectors;
            XYZ targetPoint = ((LocationCurve)targetPipe.Location).Curve.GetEndPoint(0);

            Connector closest = null;
            double minDist = double.MaxValue;

            foreach (Connector conn in connectors)
            {
                double dist = conn.Origin.DistanceTo(targetPoint);
                if (dist < minDist)
                {
                    minDist = dist;
                    closest = conn;
                }
            }
            return closest;
        }
    }
}
