using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;
using System;
using System.Collections.Generic;
using System.Linq;

namespace SARAI.Core.Import.Utils
{
    public static class FamilyInstanceImporter
    {
        public static FamilyInstance Family_instance_importer_mid_pipe(string family_name, double placement_point_mm_x, double placement_point_mm_y, double placement_point_mm_z, Document Doc, double Scaler)
        {
            FamilyInstance family_instance = null;
            XYZ placement_point_mm = new XYZ(placement_point_mm_x, placement_point_mm_y, placement_point_mm_z);
            XYZ placement_point = placement_point_mm / Scaler;

            Family targetFamily = new FilteredElementCollector(Doc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(f => f.Name == family_name);

            ElementId symbolId = targetFamily.GetFamilySymbolIds().FirstOrDefault();
            FamilySymbol symbol = Doc.GetElement(symbolId) as FamilySymbol;

            symbol.Activate();

            family_instance = Doc.Create.NewFamilyInstance(
                placement_point,
                symbol,
                StructuralType.NonStructural
            );

            ConnectorSet connectors = family_instance.MEPModel.ConnectorManager.Connectors;
            Connector targetConnector = connectors.Cast<Connector>().FirstOrDefault();

            if (targetConnector != null)
            {
                XYZ basisZ = targetConnector.CoordinateSystem.BasisZ.Normalize();

                XYZ globalZ = XYZ.BasisZ;

                if (!basisZ.IsAlmostEqualTo(globalZ))
                {
                    XYZ axis = basisZ.CrossProduct(globalZ);
                    if (!axis.IsZeroLength())
                    {
                        axis = axis.Normalize();
                        double angle = basisZ.AngleTo(globalZ);

                        Line rotationAxis = Line.CreateUnbound(placement_point, axis);
                        ElementTransformUtils.RotateElement(Doc, family_instance.Id, rotationAxis, angle);
                    }
                }
            }
            return family_instance;
        }

        public static FamilyInstance Family_instance_connect_importer_mid_pipe(FamilyInstance existing_family, double placement_point_mm_x, double placement_point_mm_y, string new_family_name, bool direction, Document Doc, double Scaler)
        {
            FamilyInstance new_family_instance = null;

            ConnectorSet existing_family_connectorset = existing_family.MEPModel.ConnectorManager.Connectors;

            double tolerance = 0.001; // Z 좌표 비교에 사용할 허용 오차
            List<Connector> uniqueConnectors = new List<Connector>();

            foreach (Connector conn in existing_family_connectorset)
            {
                // Z 값이 기존에 등록된 커넥터 중 어느 것과도 충분히 다르면 추가
                if (!uniqueConnectors.Any(c => Math.Abs(c.Origin.Z - conn.Origin.Z) < tolerance))
                {
                    uniqueConnectors.Add(conn);
                }
            }

            // Z 내림차순 정렬
            Connector[] existing_family_connector_sorted = uniqueConnectors
                .OrderByDescending(c => c.Origin.Z)
                .ToArray();

            Connector existing_family_connector = null;

            if (direction == true)
            {
                existing_family_connector = existing_family_connector_sorted[0];
            }
            else
            {
                existing_family_connector = existing_family_connector_sorted[1];
            }

            XYZ existing_family_connector_location = existing_family_connector.Origin;
            XYZ existing_family_connector_direction = existing_family_connector.CoordinateSystem.BasisZ;

            new_family_instance = Family_instance_importer_mid_pipe(new_family_name, placement_point_mm_x, placement_point_mm_y, existing_family_connector_location.Z * Scaler, Doc, Scaler);

            LocationPoint new_family_location = new_family_instance.Location as LocationPoint;
            XYZ new_family_point = new_family_location.Point;

            double new_family_offset = 0;

            ConnectorSet new_family_connectorset = new_family_instance.MEPModel.ConnectorManager.Connectors;

            Connector[] new_family_connector_sorted = new_family_connectorset
            .Cast<Connector>()
            .OrderByDescending(c => c.Origin.Z)
            .ToArray();

            Connector new_family_connector = null;

            if (direction == true)
            {
                new_family_connector = new_family_connector_sorted[1];
                new_family_offset = new_family_point.Z - new_family_connector.Origin.Z;
            }
            else
            {
                new_family_connector = new_family_connector_sorted[0];
                new_family_offset = new_family_point.Z - new_family_connector.Origin.Z;
            }
            XYZ new_family_translation = new XYZ(0, 0, new_family_offset);

            ElementTransformUtils.MoveElement(Doc, new_family_instance.Id, new_family_translation);
            existing_family_connector.ConnectTo(new_family_connector);

            return new_family_instance;
        }
        public static FamilyInstance Family_instance_importer(string family_name, double placement_point_mm_x, double placement_point_mm_y, double placement_point_mm_z, Document Doc, double Scaler)
        {
            FamilyInstance family_instance = null;
            XYZ placemen_point_mm = new XYZ(placement_point_mm_x, placement_point_mm_y, placement_point_mm_z);
            XYZ placement_point = placemen_point_mm / Scaler;

            Family targetFamily = new FilteredElementCollector(Doc)
            .OfClass(typeof(Family))
            .Cast<Family>()
            .FirstOrDefault(f => f.Name == family_name);

            ElementId symbolId = targetFamily.GetFamilySymbolIds().FirstOrDefault();
            FamilySymbol symbol = Doc.GetElement(symbolId) as FamilySymbol;

            if (symbol == null)
            {
                TaskDialog.Show("오류", "해당 이름의 패밀리 심볼을 찾을 수 없습니다.");
            }
            else
            {
                using (Transaction t = new Transaction(Doc, "Activate Symbol"))
                {
                    t.Start();
                    symbol.Activate();
                    t.Commit();
                }
                using (Transaction t = new Transaction(Doc, "Place Family Instance"))
                {
                    t.Start();
                    family_instance = Doc.Create.NewFamilyInstance(
                        placement_point,
                        symbol,
                        StructuralType.NonStructural
                    );

                    ConnectorSet connectors = family_instance.MEPModel.ConnectorManager.Connectors;
                    Connector targetConnector = connectors.Cast<Connector>().FirstOrDefault();

                    if (targetConnector != null)
                    {
                        XYZ basisZ = targetConnector.CoordinateSystem.BasisZ.Normalize();

                        XYZ globalZ = XYZ.BasisZ;

                        if (!basisZ.IsAlmostEqualTo(globalZ))
                        {
                            XYZ axis = basisZ.CrossProduct(globalZ);
                            if (!axis.IsZeroLength())
                            {
                                axis = axis.Normalize();
                                double angle = basisZ.AngleTo(globalZ);

                                Line rotationAxis = Line.CreateUnbound(placement_point, axis);
                                ElementTransformUtils.RotateElement(Doc, family_instance.Id, rotationAxis, angle);
                            }
                        }
                    }
                    t.Commit();
                }
            }
            return family_instance;
        }

        public static FamilyInstance Family_instance_connect_importer(FamilyInstance existing_family, double placement_point_mm_x, double placement_point_mm_y, string new_family_name, bool direction, Document Doc, double Scaler)
        {
            FamilyInstance new_family_instance = null;

            ConnectorSet existing_family_connectorset = existing_family.MEPModel.ConnectorManager.Connectors;

            double tolerance = 0.001; // Z 좌표 비교에 사용할 허용 오차
            List<Connector> uniqueConnectors = new List<Connector>();

            foreach (Connector conn in existing_family_connectorset)
            {
                if (!uniqueConnectors.Any(c => Math.Abs(c.Origin.Z - conn.Origin.Z) < tolerance))
                {
                    uniqueConnectors.Add(conn);
                }
            }

            Connector[] existing_family_connector_sorted = uniqueConnectors
                .OrderByDescending(c => c.Origin.Z)
                .ToArray();

            Connector existing_family_connector = null;

            if (direction == true)
            {
                existing_family_connector = existing_family_connector_sorted[0];
            }
            else
            {
                existing_family_connector = existing_family_connector_sorted[1];
            }

            XYZ existing_family_connector_location = existing_family_connector.Origin;
            XYZ existing_family_connector_direction = existing_family_connector.CoordinateSystem.BasisZ;

            new_family_instance = Family_instance_importer(new_family_name, placement_point_mm_x, placement_point_mm_y, existing_family_connector_location.Z * Scaler, Doc, Scaler);

            LocationPoint new_family_location = new_family_instance.Location as LocationPoint;
            XYZ new_family_point = new_family_location.Point;

            double new_family_offset = 0;

            ConnectorSet new_family_connectorset = new_family_instance.MEPModel.ConnectorManager.Connectors;

            Connector[] new_family_connector_sorted = new_family_connectorset
            .Cast<Connector>()
            .OrderByDescending(c => c.Origin.Z)
            .ToArray();

            Connector new_family_connector = null;

            if (direction == true)
            {
                new_family_connector = new_family_connector_sorted[1];
                new_family_offset = new_family_point.Z - new_family_connector.Origin.Z;
            }
            else
            {
                new_family_connector = new_family_connector_sorted[0];
                new_family_offset = new_family_point.Z - new_family_connector.Origin.Z;
            }
            XYZ new_family_translation = new XYZ(0, 0, new_family_offset);
            using (Transaction t = new Transaction(Doc, "Connect"))
            {
                t.Start();
                ElementTransformUtils.MoveElement(Doc, new_family_instance.Id, new_family_translation);
                existing_family_connector.ConnectTo(new_family_connector);
                t.Commit();
            }
            return new_family_instance;
        }
        public static Pipe CreatePipeFromConnector(FamilyInstance existing_family, double pipeLength_mm, string pipeTypeName, double diameter, bool direction, Document doc, double scaler)
        {         
            ConnectorSet existing_family_connectorset = existing_family.MEPModel.ConnectorManager.Connectors;

            Connector[] existing_family_connector_sorted = existing_family_connectorset
            .Cast<Connector>()
            .OrderByDescending(c => c.Origin.Z)
            .ToArray();

            Connector existing_family_connector = null;

            if (direction == true)
            {
                existing_family_connector = existing_family_connector_sorted[0];
            }
            else
            {
                existing_family_connector = existing_family_connector_sorted[1];
            }

            double pipeLength = pipeLength_mm / scaler;

            XYZ existing_family_connector_location = existing_family_connector.Origin;
            XYZ existing_family_connector_direction = existing_family_connector.CoordinateSystem.BasisZ;

            XYZ endPoint = existing_family_connector_location + (existing_family_connector_direction * pipeLength);

           PipeType pipeType = new FilteredElementCollector(doc)
               .OfClass(typeof(PipeType))
               .Cast<PipeType>()
               .FirstOrDefault(p => p.Name == pipeTypeName)
               ?? throw new InvalidOperationException("파이프 타입을 찾을 수 없습니다.");

            PipingSystemType systemType = new FilteredElementCollector(doc)
            .OfClass(typeof(PipingSystemType))
            .Cast<PipingSystemType>()
            .First();

            XYZ point = (existing_family.Location as LocationPoint).Point;
            Level level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => Math.Abs(l.Elevation - point.Z))
                .FirstOrDefault();

            Pipe newPipe = null;

            using (Transaction t = new Transaction(doc, "Create Pipe"))
            {
                t.Start();

                newPipe = Pipe.Create(doc, systemType.Id, pipeType.Id, level.Id, existing_family_connector_location, endPoint);

                // 필요 시 파이프 지름 설정
                newPipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(diameter/scaler);

                ConnectorSet new_pipe_connectorset = newPipe.ConnectorManager.Connectors;

                Connector[] new_pipe_connector_sorted = new_pipe_connectorset
                .Cast<Connector>()
                .OrderByDescending(c => c.Origin.Z)
                .ToArray();
                Connector new_pipe_connector = null;
                if (direction == true)
                {
                    new_pipe_connector = new_pipe_connector_sorted[1];
                }
                else
                {
                    new_pipe_connector = new_pipe_connector_sorted[0];
                }

                existing_family_connector.ConnectTo(new_pipe_connector);

                t.Commit();
            }

            return newPipe;
        }

        public static FamilyInstance Family_instance_connect_importer_from_pipe(Pipe existing_pipe, double placement_point_mm_x, double placement_point_mm_y, string new_family_name, bool direction, Document Doc, double Scaler)
        {
            FamilyInstance new_family_instance = null;

            // 기존 파이프의 Connector 가져오기
            ConnectorSet existing_pipe_connectorset = existing_pipe.ConnectorManager.Connectors;

            Connector[] existing_pipe_connector_sorted = existing_pipe_connectorset
                .Cast<Connector>()
                .OrderByDescending(c => c.Origin.Z)
                .ToArray();

            Connector existing_pipe_connector = direction
                ? existing_pipe_connector_sorted[0]
                : existing_pipe_connector_sorted[1];

            XYZ existing_pipe_connector_location = existing_pipe_connector.Origin;
            XYZ existing_pipe_connector_direction = existing_pipe_connector.CoordinateSystem.BasisZ;

            // 새 패밀리 배치
            new_family_instance = Family_instance_importer(
                new_family_name, placement_point_mm_x, placement_point_mm_y,
                existing_pipe_connector_location.Z * Scaler,
                Doc,
                Scaler
            );

            // 새 패밀리 커넥터 정보
            LocationPoint new_family_location = new_family_instance.Location as LocationPoint;
            XYZ new_family_point = new_family_location.Point;

            ConnectorSet new_family_connectorset = new_family_instance.MEPModel.ConnectorManager.Connectors;

            Connector[] new_family_connector_sorted = new_family_connectorset
                .Cast<Connector>()
                .OrderByDescending(c => c.Origin.Z)
                .ToArray();

            Connector new_family_connector = direction
                ? new_family_connector_sorted[1]
                : new_family_connector_sorted[0];

            double new_family_offset = new_family_point.Z - new_family_connector.Origin.Z;
            XYZ new_family_translation = new XYZ(0, 0, new_family_offset);

            // 이동 + 커넥터 연결
            using (Transaction t = new Transaction(Doc, "Connect from Pipe"))
            {
                t.Start();
                ElementTransformUtils.MoveElement(Doc, new_family_instance.Id, new_family_translation);
                existing_pipe_connector.ConnectTo(new_family_connector);  // 연결
                t.Commit();
            }

            return new_family_instance;
        }
    }
}