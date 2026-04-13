using Autodesk.Revit.UI;
using System;
using Autodesk.Revit.DB;
using Newtonsoft.Json.Linq;
using View = Autodesk.Revit.DB.View;
using System.Linq;
using Autodesk.Revit.DB.Plumbing;
using System.Collections.Generic;
using System.IO;
using Autodesk.Revit.DB.Structure;
using static SARAI.Core.Import.Utils.FamilyInstanceImporter;
using static SARAI.Core.Import.Utils.AttrParser;
using static SARAI.Core.Import.Utils.CustomParameterImporter;
using System.Reflection;

namespace SARAI.Core
{
    public class RImportApp
    {
        private readonly ExternalCommandData Revit;
        private readonly double Foreline_height;
        private readonly double Scaler;
        private readonly Document Doc;

        public RImportApp(ExternalCommandData revit, double foreline_height, double scaler)
        {
            this.Revit = revit;
            this.Foreline_height = foreline_height;
            this.Scaler = scaler;
            this.Doc = revit.Application.ActiveUIDocument.Document;
        }

        public void Run(string jsonText)
        {
            View activeView = Revit.Application.ActiveUIDocument.ActiveView;
            JArray jsonArray = JArray.Parse(jsonText);

            // 메타 데이터 불러오기 & 파싱
            string assemblyPath = Assembly.GetExecutingAssembly().Location;
            string baseDir = Path.GetDirectoryName(assemblyPath);

            // basic stack path
            //string basic_stack_jsonPath = Path.GetFullPath(Path.Combine(baseDir, @"..\..\..\json_file\basic_stack_reducer_custom.json"));
            string basic_stack_jsonPath = Path.Combine(baseDir, "LogicPart/basic_stack_reducer_custom.json");
            string basic_stack_jsonText = File.ReadAllText(basic_stack_jsonPath);
            JArray basic_stack_jsonArray = JArray.Parse(basic_stack_jsonText);
            Dictionary<string, List<string>> areaStackMap = new Dictionary<string, List<string>>();
            foreach (JObject jsonObj in basic_stack_jsonArray.Cast<JObject>())
            {
                string area = jsonObj["area"].Value<string>();
                JArray stackArray = (JArray)jsonObj["stack_list"];
                List<string> stackList = stackArray.ToObject<List<string>>();

                areaStackMap[area] = stackList;
            }

            // family mapping path
            string family_mapping_jsonPath = Path.Combine(baseDir, "LogicPart/family_mapping_reducer_custom.json");
            string family_mapping_jsonText = File.ReadAllText(family_mapping_jsonPath);
            JArray family_mapping_jsonArray = JArray.Parse(family_mapping_jsonText);
            Dictionary<double, Dictionary<string, string>> diameter_mapping = new Dictionary<double, Dictionary<string, string>>();

            foreach (JObject obj in family_mapping_jsonArray)
            {
                double diameter = obj["diameter"].Value<double>();

                Dictionary<string, string> parts = new Dictionary<string, string>();

                foreach (var prop in obj.Properties())
                {
                    if (prop.Name == "diameter") continue;  // diameter는 건너뛰기
                    parts[prop.Name] = prop.Value.ToString();
                }
                diameter_mapping[diameter] = parts;
            }

            // 경로 수 지정 시, 디버그용 JObject jsonObj in jsonArray.Cast<JObject>().Take(1)
            foreach (JObject jsonObj in jsonArray.Cast<JObject>())
            {
                JObject attr = (JObject)jsonObj["attr"];
                double Pump_diameter_mm = attr["pump_size"].Value<double>();
                double Pump_diameter = Pump_diameter_mm / (Scaler);
                double Equipment_diameter_mm = attr["equip_size"].Value<double>();
                double Equipment_diameter = Equipment_diameter_mm / (Scaler);
                string Eqid = StringParser(attr, "equip_id");
                string Chamber = StringParser(attr, "chamber");
                string Chamber_index = StringParser(attr, "chamber_index");

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

                List<ElementId> Routing_elementIds = DirectImport(areaStackMap, diameter_mapping, pathPoints[0] * Scaler, pathPoints[pathPoints.Count - 1] * Scaler, Pump_diameter_mm, Equipment_diameter_mm, attr, Foreline_height);

                ElementId startId = Routing_elementIds[0];
                ElementId endId = Routing_elementIds[1];

                FamilyInstance fiStart = Doc.GetElement(startId) as FamilyInstance;
                FamilyInstance fiEnd = Doc.GetElement(endId) as FamilyInstance;

                Connector startConnector = GetFreeConnector(fiStart);
                Connector endConnector = GetFreeConnector(fiEnd);

                ElementId pipeTypeId = new FilteredElementCollector(Doc)
                    .OfClass(typeof(PipeType))
                    .Cast<PipeType>()
                    .FirstOrDefault(p => p.Name == "Test_pipe")?.Id ?? throw new Exception("PipeType not found");

                PipingSystemType systemType = new FilteredElementCollector(Doc)
                .OfClass(typeof(PipingSystemType))
                .Cast<PipingSystemType>()
                .First();  // 첫 번째 시스템 타입 사용

                Level level = new FilteredElementCollector(Doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name == "Level 1") ?? throw new Exception("Level not found");

                using (Transaction tx = new Transaction(Doc, "Draw Smart Pipe with Elbows"))
                {
                    tx.Start();
                    List<Pipe> createdPipes = new List<Pipe>();
                    if (pathPoints.Count > 2) //2,000mm 이상 시 분할 및 플랜지 삽입
                    {
                        XYZ point_1 = new XYZ(pathPoints[0].X, pathPoints[0].Y, pathPoints[1].Z);
                        MidFlangePipeCreator(diameter_mapping, startConnector.Origin, point_1, Scaler, Pump_diameter_mm, Eqid, Chamber, Chamber_index, createdPipes);

                        for (int i = 1; i < pathPoints.Count - 2; i++)
                        {
                            MidFlangePipeCreator(diameter_mapping, pathPoints[i], pathPoints[i + 1], Scaler, Pump_diameter_mm, Eqid, Chamber, Chamber_index, createdPipes);
                        }

                        XYZ point_2 = new XYZ(pathPoints[pathPoints.Count - 1].X, pathPoints[pathPoints.Count - 1].Y, pathPoints[pathPoints.Count - 2].Z);
                        MidFlangePipeCreator(diameter_mapping, point_2, endConnector.Origin, Scaler, Pump_diameter_mm, Eqid, Chamber, Chamber_index, createdPipes);
                    }
                    else //2,000mm 미만
                    {
                        MidFlangePipeCreator(diameter_mapping, startConnector.Origin, endConnector.Origin, Scaler, Pump_diameter_mm, Eqid, Chamber, Chamber_index, createdPipes);
                    }

                        // 4. 각 파이프의 끝과 다음 파이프의 시작을 ConnectTo()로 연결 (엘보우 생성)
                        for (int i = 0; i < createdPipes.Count - 1; i++)
                        {
                            Connector endConnector1 = GetClosestConnector(createdPipes[i], createdPipes[i + 1].Location as LocationCurve);
                            Connector startConnector2 = GetClosestConnector(createdPipes[i + 1], createdPipes[i].Location as LocationCurve);

                            if (endConnector1 != null && startConnector2 != null)
                            {
                                try
                                {
                                    FamilyInstance elbow = Doc.Create.NewElbowFitting(endConnector1, startConnector2);
                                    StringParameterSetFamily(elbow, "Eqid", Eqid);
                                    StringParameterSetFamily(elbow, "Chamber", Chamber);
                                    StringParameterSetFamily(elbow, "Chamber_index", Chamber_index);
                                }
                                catch (Autodesk.Revit.Exceptions.InvalidOperationException)
                                {
                                    //TaskDialog.Show("Warning", "Elbow 생성 실패: " + ex.Message);
                                }
                            }
                        }
                    tx.Commit();
                }
            }
        }

        private void MidFlangePipeCreator(Dictionary<double, Dictionary<string, string>> diameter_mapping, XYZ start_point, XYZ end_point, double Scaler, double Pump_diameter_mm, string Eqid, string Chamber, string Chamber_index, List<Pipe> createdPipes)
        {
            double Pump_diameter = Pump_diameter_mm / Scaler;

            ElementId pipeTypeId = new FilteredElementCollector(Doc)
            .OfClass(typeof(PipeType))
            .Cast<PipeType>()
            .FirstOrDefault(p => p.Name == "Test_pipe")?.Id ?? throw new Exception("PipeType not found");

            PipingSystemType systemType = new FilteredElementCollector(Doc)
            .OfClass(typeof(PipingSystemType))
            .Cast<PipingSystemType>()
            .First();  // 첫 번째 시스템 타입 사용

            Level level = new FilteredElementCollector(Doc)
            .OfClass(typeof(Level))
            .Cast<Level>()
            .FirstOrDefault(l => l.Name == "Level 1") ?? throw new Exception("Level not found");

            double length_pipe = end_point.DistanceTo(start_point);
            if (length_pipe * Scaler > 2000)
            {
                XYZ mid_point = (start_point + end_point) / 2;

                string Flange_name = diameter_mapping[Pump_diameter_mm]["MF Flange"];
                string Clamp_name = diameter_mapping[Pump_diameter_mm]["DC Clamp Assembly"];

                FamilyInstance Flange_instance_1 = Family_instance_importer_mid_pipe(Flange_name, mid_point.X * Scaler, mid_point.Y * Scaler, mid_point.Z * Scaler, Doc, Scaler);
                FamilyInstance Clamp_instance = Family_instance_connect_importer_mid_pipe(Flange_instance_1, mid_point.X * Scaler, mid_point.Y * Scaler, Clamp_name, true, Doc, Scaler);
                FamilyInstance Flange_instance_2 = Family_instance_connect_importer_mid_pipe(Clamp_instance, mid_point.X * Scaler, mid_point.Y * Scaler, Flange_name, true, Doc, Scaler);
                StringParameterSetFamily(Flange_instance_1, "Eqid", Eqid);
                StringParameterSetFamily(Flange_instance_1, "Chamber", Chamber);
                StringParameterSetFamily(Flange_instance_1, "Chamber_index", Chamber_index);
                StringParameterSetFamily(Clamp_instance, "Eqid", Eqid);
                StringParameterSetFamily(Clamp_instance, "Chamber", Chamber);
                StringParameterSetFamily(Clamp_instance, "Chamber_index", Chamber_index);
                StringParameterSetFamily(Flange_instance_2, "Eqid", Eqid);
                StringParameterSetFamily(Flange_instance_2, "Chamber", Chamber);
                StringParameterSetFamily(Flange_instance_2, "Chamber_index", Chamber_index);

                RotateConnectedFamilyInstances(Doc, Flange_instance_1, Clamp_instance, Flange_instance_2, start_point, end_point);

                Connector flange1Free = GetUnconnectedConnector(Flange_instance_1);
                Connector flange2Free = GetUnconnectedConnector(Flange_instance_2);

                XYZ flange1Point = flange1Free.Origin;
                XYZ flange2Point = flange2Free.Origin;

                Pipe firstPipe_1 = Pipe.Create(Doc, systemType.Id, pipeTypeId, level.Id, start_point, flange1Point);
                firstPipe_1.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(Pump_diameter);
                StringParameterSetPipe(firstPipe_1, "Eqid", Eqid);
                StringParameterSetPipe(firstPipe_1, "Chamber", Chamber);
                StringParameterSetPipe(firstPipe_1, "Chamber_index", Chamber_index);
                createdPipes.Add(firstPipe_1);

                Pipe firstPipe_2 = Pipe.Create(Doc, systemType.Id, pipeTypeId, level.Id, flange2Point, end_point);
                firstPipe_2.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(Pump_diameter);
                StringParameterSetPipe(firstPipe_2, "Eqid", Eqid);
                StringParameterSetPipe(firstPipe_2, "Chamber", Chamber);
                StringParameterSetPipe(firstPipe_2, "Chamber_index", Chamber_index);
                createdPipes.Add(firstPipe_2);

                Connector pipeStartConn = GetPipeConnectorClosestTo(firstPipe_1, flange1Point);
                Connector pipeEndConn = GetPipeConnectorClosestTo(firstPipe_2, flange2Point);
                pipeStartConn.ConnectTo(flange1Free);
                pipeEndConn.ConnectTo(flange2Free);

                Connector UnconnectedConnector_pipe1 = GetUnconnectedConnector(firstPipe_1);
                Connector UnconnectedConnector_pipe2 = GetUnconnectedConnector(firstPipe_2);
            }
            else
            {
                Pipe firstPipe = Pipe.Create(Doc, systemType.Id, pipeTypeId, level.Id,
                start_point, end_point);
                firstPipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(Pump_diameter);
                StringParameterSetPipe(firstPipe, "Eqid", Eqid);
                StringParameterSetPipe(firstPipe, "Chamber", Chamber);
                StringParameterSetPipe(firstPipe, "Chamber_index", Chamber_index);
                createdPipes.Add(firstPipe);
            }
        }

        private Connector GetFreeConnector(FamilyInstance fi)
        {
            MEPModel mepModel = fi.MEPModel;
            if (mepModel == null) return null;

            ConnectorSet connectors = mepModel.ConnectorManager.Connectors;
            foreach (Connector connector in connectors)
            {
                if (!connector.IsConnected)
                    return connector;
            }
            return null;
        }

        private Connector GetClosestConnector(Pipe pipe, LocationCurve otherCurve)
        {
            Connector closest = null;
            double minDistance = double.MaxValue;

            foreach (Connector c in pipe.ConnectorManager.Connectors)
            {
                if (c.ConnectorType != ConnectorType.End)
                    continue;

                XYZ cPos = c.Origin;
                double dist = cPos.DistanceTo(otherCurve.Curve.GetEndPoint(0));
                if (dist < minDistance)
                {
                    minDistance = dist;
                    closest = c;
                }
            }
            return closest;
        }

        Connector GetUnconnectedConnector(FamilyInstance fi)
        {
            ConnectorSet connectors = fi.MEPModel.ConnectorManager.Connectors;

            foreach (Connector conn in connectors)
            {
                if (!conn.IsConnected && conn.Domain == Domain.DomainPiping)
                {
                    return conn;
                }
            }
            return null;
        }

        Connector GetUnconnectedConnector(Pipe pipe)
        {
            ConnectorSet connectors = pipe.ConnectorManager.Connectors;

            foreach (Connector conn in connectors)
            {
                if (!conn.IsConnected && conn.Domain == Domain.DomainPiping)
                {
                    return conn;
                }
            }
            return null;
        }

        Connector GetPipeConnectorClosestTo(Pipe pipe, XYZ targetPoint)
        {
            ConnectorSet connectors = pipe.ConnectorManager.Connectors;
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

        private void RotateConnectedFamilyInstances(Document doc, FamilyInstance fi1, FamilyInstance fi2, FamilyInstance fi3, XYZ start_point, XYZ end_point)
        {
            XYZ targetDirection = (end_point - start_point).Normalize();
            XYZ currentDirection = XYZ.BasisZ; // 현재 커넥터 방향이 Z축 기준

            if (currentDirection.IsAlmostEqualTo(targetDirection))
                return;

            // 회전축과 회전각
            XYZ rotationAxis = currentDirection.CrossProduct(targetDirection).Normalize();
            double angle = currentDirection.AngleTo(targetDirection);

            // 가운데 패밀리 기준 위치
            LocationPoint midLoc = fi2.Location as LocationPoint;
            if (midLoc == null) return;

            XYZ rotationOrigin = midLoc.Point;
            Line rotationLine = Line.CreateUnbound(rotationOrigin, rotationAxis);

            ICollection<ElementId> elementIds = new List<ElementId>
            {
                fi1.Id,
                fi2.Id,
                fi3.Id
            };
            ElementTransformUtils.RotateElements(doc, elementIds, rotationLine, angle);
        }

        // 삽입기능
        public List<ElementId> DirectImport(Dictionary<string, List<string>> areaStackMap, Dictionary<double, Dictionary<string, string>> diameter_mapping, XYZ start_point, XYZ end_point, double Pump_diameter_mm, double Equipment_diameter_mm, JObject attr, double foreline_height)
        {
            string Eqid_value = attr["equip_id"].Value<string>();
            string Chamber_value = attr["chamber"].Value<string>();
            string Chamber_index_value = attr["chamber_index"].Value<string>();

            // 하드 코딩
            double hard_level_2 = foreline_height;//P4-3 6TH:41200, //P4-1 6TH: 6100
            FamilyInstance FSF_middle_foreline = null;
            List<FamilyInstance> FSF_MF_flange_list = new List<FamilyInstance>();
            FamilyInstance CSF_upper_reducer = null;
            FamilyInstance CSF_under_MF_Flange = null;

            string CSF_reducer_case = "CSF_" + Equipment_diameter_mm.ToString() + "_" + Pump_diameter_mm.ToString();

            foreach (KeyValuePair<string, List<string>> kvp in areaStackMap)
            {
                string area = kvp.Key;
                List<string> stackList = kvp.Value;

                bool direction = true;
                double import_diameter;
                double placement_point_x;
                double placement_point_y;
                double placement_point_z;
                if (area == CSF_reducer_case)
                {
                    direction = false;
                    import_diameter = Equipment_diameter_mm;
                    placement_point_x = end_point.X;
                    placement_point_y = end_point.Y;
                    placement_point_z = end_point.Z;
                }
                else if (area == "FSF")
                {
                    //continue;
                    import_diameter = Pump_diameter_mm;
                    placement_point_x = start_point.X;
                    placement_point_y = start_point.Y;
                    placement_point_z = start_point.Z;
                }
                else
                {
                    continue;
                }

                FamilyInstance exist_family_instance = null;
                Pipe exist_pipe_instance = null;

                for (int i = 0; i < stackList.Count; i++)
                {
                    if (i == 0)
                    {
                        string new_family_name = diameter_mapping[import_diameter][stackList[i]];
                        exist_family_instance = Family_instance_importer(new_family_name, placement_point_x, placement_point_y, placement_point_z, Doc, Scaler);
                        using (Transaction tx = new Transaction(Doc, "Family Custom Parameter Set"))
                        {
                            tx.Start();
                            Parameter Eqid = exist_family_instance.LookupParameter("Eqid");
                            Parameter Chamber = exist_family_instance.LookupParameter("Chamber");
                            Parameter Chamber_index = exist_family_instance.LookupParameter("Chamber_index");

                            Eqid.Set(Eqid_value);
                            Chamber.Set(Chamber_value);
                            Chamber_index.Set(Chamber_index_value);
                            tx.Commit();
                        }
                    }
                    else
                    {
                        if (stackList[i].Contains("pipe"))
                        {
                            string new_family_name = diameter_mapping[import_diameter]["Pipe"];
                            double hard_length = double.Parse(stackList[i].Split('_')[1]);
                            exist_pipe_instance = CreatePipeFromConnector(exist_family_instance, hard_length, new_family_name, import_diameter, direction, Doc, Scaler);
                            using (Transaction tx = new Transaction(Doc, "Pipe Custom Parameter Set"))
                            {
                                tx.Start();
                                Parameter Eqid = exist_pipe_instance.LookupParameter("Eqid");
                                Parameter Chamber = exist_pipe_instance.LookupParameter("Chamber");
                                Parameter Chamber_index = exist_pipe_instance.LookupParameter("Chamber_index");

                                Eqid.Set(Eqid_value);
                                Chamber.Set(Chamber_value);
                                Chamber_index.Set(Chamber_index_value);
                                tx.Commit();
                            }
                            if (stackList[i] == "pipe_200")
                            {
                                ConnectorSet FSF_free_pipe_connectors = exist_pipe_instance.ConnectorManager.Connectors;
                                Connector[] FSF_free_pipe_connector_sorted = FSF_free_pipe_connectors
                                .Cast<Connector>()
                                .OrderByDescending(c => c.Origin.Z)
                                .ToArray();

                                Connector FSF_free_pipe_connector = FSF_free_pipe_connector_sorted[0];

                                XYZ Leak_check_start_location = FSF_free_pipe_connector.Origin + new XYZ(import_diameter / 2, 0, 150) / Scaler;
                                XYZ Leak_check_end_location = Leak_check_start_location + new XYZ(50, 0, 0) / Scaler;

                                ElementId pipeTypeId = new FilteredElementCollector(Doc)
                                .OfClass(typeof(PipeType))
                                .Cast<PipeType>()
                                .FirstOrDefault(p => p.Name == "Test_pipe")?.Id ?? throw new Exception("PipeType not found");

                                // 시스템 타입 찾기
                                PipingSystemType systemType = new FilteredElementCollector(Doc)
                                .OfClass(typeof(PipingSystemType))
                                .Cast<PipingSystemType>()
                                .First();  // 첫 번째 시스템 타입 사용

                                XYZ point = (exist_family_instance.Location as LocationPoint).Point;
                                Level level = new FilteredElementCollector(Doc)
                                .OfClass(typeof(Level))
                                .Cast<Level>()
                                .OrderBy(l => Math.Abs(l.Elevation - point.Z))
                                .FirstOrDefault();

                                using (Transaction t = new Transaction(Doc, "Create Leak Pipe"))
                                {
                                    t.Start();

                                    Pipe Leak_check_port = Pipe.Create(Doc, systemType.Id, pipeTypeId, level.Id, Leak_check_start_location, Leak_check_end_location);

                                    // 필요 시 파이프 지름 설정
                                    Leak_check_port.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(20 / Scaler);
                                    Parameter Eqid_pipe = Leak_check_port.LookupParameter("Eqid");
                                    Parameter Chamber_pipe = Leak_check_port.LookupParameter("Chamber");
                                    Parameter Chamber_index_pipe = Leak_check_port.LookupParameter("Chamber_index");

                                    Eqid_pipe.Set(Eqid_value);
                                    Chamber_pipe.Set(Chamber_value);
                                    Chamber_index_pipe.Set(Chamber_index_value);
                                    ConnectorSet existing_pipe_connectorset = Leak_check_port.ConnectorManager.Connectors;

                                    Connector[] existing_pipe_connector_sorted = existing_pipe_connectorset
                                        .Cast<Connector>()
                                        .OrderByDescending(c => c.Origin.X)
                                        .ToArray();

                                    Connector existing_pipe_connector = direction
                                        ? existing_pipe_connector_sorted[0]
                                        : existing_pipe_connector_sorted[1];

                                    Family targetFamily = new FilteredElementCollector(Doc)
                                    .OfClass(typeof(Family))
                                    .Cast<Family>()
                                    .FirstOrDefault(f => f.Name == "[VAC-030] CLAMP ASSY_NW25_KF POT");

                                    ElementId symbolId = targetFamily.GetFamilySymbolIds().FirstOrDefault();
                                    FamilySymbol symbol = Doc.GetElement(symbolId) as FamilySymbol;

                                    symbol.Activate();

                                    FamilyInstance family_instance = Doc.Create.NewFamilyInstance(Leak_check_end_location, symbol, StructuralType.NonStructural);
                                    Parameter Eqid = family_instance.LookupParameter("Eqid");
                                    Parameter Chamber = family_instance.LookupParameter("Chamber");
                                    Parameter Chamber_index = family_instance.LookupParameter("Chamber_index");

                                    Eqid.Set(Eqid_value);
                                    Chamber.Set(Chamber_value);
                                    Chamber_index.Set(Chamber_index_value);

                                    ConnectorSet connectors = family_instance.MEPModel.ConnectorManager.Connectors;
                                    Connector targetConnector = connectors.Cast<Connector>().FirstOrDefault();

                                    XYZ basis = targetConnector.CoordinateSystem.BasisY.Normalize();
                                    XYZ desired = XYZ.BasisX;

                                    if (!basis.IsAlmostEqualTo(desired))
                                    {
                                        XYZ axis = basis.CrossProduct(desired);
                                        if (!axis.IsZeroLength())
                                        {
                                            axis = axis.Normalize();
                                            double angle = basis.AngleTo(desired) +0.5*Math.PI;

                                            // 커넥터 위치를 중심으로 회전
                                            Line rotationAxis = Line.CreateUnbound(targetConnector.Origin, axis);
                                            ElementTransformUtils.RotateElement(Doc, family_instance.Id, rotationAxis, angle);
                                        }
                                    }

                                    double new_family_offset = Leak_check_end_location.X - targetConnector.Origin.X;
                                    XYZ translation = Leak_check_end_location - targetConnector.Origin;
                                    ElementTransformUtils.MoveElement(Doc, family_instance.Id, translation);
                                    existing_pipe_connector.ConnectTo(targetConnector);  // 연결

                                    t.Commit();
                                }
                            }
                        }
                        else
                        {
                            if (stackList[i - 1].Contains("pipe"))
                            {
                                string new_family_name = diameter_mapping[import_diameter][stackList[i]];
                                exist_family_instance = Family_instance_connect_importer_from_pipe(exist_pipe_instance, placement_point_x, placement_point_y, new_family_name, direction, Doc, Scaler);
                                using (Transaction tx = new Transaction(Doc, "Family Custom Parameter Set"))
                                {
                                    tx.Start();
                                    Parameter Eqid = exist_family_instance.LookupParameter("Eqid");
                                    Parameter Chamber = exist_family_instance.LookupParameter("Chamber");
                                    Parameter Chamber_index = exist_family_instance.LookupParameter("Chamber_index");

                                    Eqid.Set(Eqid_value);
                                    Chamber.Set(Chamber_value);
                                    Chamber_index.Set(Chamber_index_value);
                                    tx.Commit();
                                }
                                if (area == "FSF" && i != 3 && stackList[i] == "MF Flange")
                                {
                                    FSF_MF_flange_list.Add(exist_family_instance);
                                }
                            }
                            else
                            {
                                string new_family_name = diameter_mapping[import_diameter][stackList[i]];
                                exist_family_instance = Family_instance_connect_importer(exist_family_instance, placement_point_x, placement_point_y, new_family_name, direction, Doc, Scaler);
                                using (Transaction tx = new Transaction(Doc, "Family Custom Parameter Set"))
                                {
                                    tx.Start();
                                    Parameter Eqid = exist_family_instance.LookupParameter("Eqid");
                                    Parameter Chamber = exist_family_instance.LookupParameter("Chamber");
                                    Parameter Chamber_index = exist_family_instance.LookupParameter("Chamber_index");

                                    Eqid.Set(Eqid_value);
                                    Chamber.Set(Chamber_value);
                                    Chamber_index.Set(Chamber_index_value);
                                    tx.Commit();
                                }
                                if (area == "FSF" && stackList[i] == "Middle Foreline")
                                {
                                    FSF_middle_foreline = exist_family_instance;
                                }
                                if (area == CSF_reducer_case && stackList[i].Contains("Reducer"))
                                {
                                    CSF_upper_reducer = exist_family_instance;
                                }
                                if (area == "FSF" && stackList[i] == "MF Flange")
                                {
                                    CSF_under_MF_Flange = exist_family_instance;
                                }
                                if (area == "FSF" && i != 3 && stackList[i] == "MF Flange")
                                {
                                    FSF_MF_flange_list.Add(exist_family_instance);
                                }
                            }
                        }
                    }
                }
            }

            LocationPoint FSF_middle_foreline_location = FSF_middle_foreline.Location as LocationPoint;
            XYZ FSF_middle_foreline_point = FSF_middle_foreline_location.Point;
            double FSF_middle_foreline_translation_z = hard_level_2 / Scaler - FSF_middle_foreline_point.Z;

            XYZ translationVector = new XYZ(0, 0, FSF_middle_foreline_translation_z);

            ICollection<ElementId> elementIds = new List<ElementId>
            {
                FSF_middle_foreline.Id,
            };
            List<ElementId> flangeIds = FSF_MF_flange_list.Select(fi => fi.Id).ToList();
            ((List<ElementId>)elementIds).AddRange(flangeIds);

            using (Transaction tx = new Transaction(Doc, "Move Family Instances"))
            {
                tx.Start();

                ElementTransformUtils.MoveElements(Doc, elementIds, translationVector);

                tx.Commit();
            }

            return new List<ElementId> { CSF_under_MF_Flange.Id, CSF_upper_reducer.Id };
        }
    }
}
