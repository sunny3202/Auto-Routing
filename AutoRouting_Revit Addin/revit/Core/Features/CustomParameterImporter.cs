using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.DB.Plumbing;

namespace SARAI.Core.Import.Utils
{
    public static class CustomParameterImporter
    {
        public static void StringParameterSetFamily(FamilyInstance instance, string key, string value)
        {
                Parameter param = instance.LookupParameter(key);

            if (param == null)
            {
                TaskDialog.Show("Error", $"'{key}' 파라미터를 찾을 수 없습니다.");
                return;
            }

            if (param.IsReadOnly)
            {
                TaskDialog.Show("Error", $"'{key}' 파라미터는 읽기 전용입니다.");
                return;
            }

            switch (param.StorageType)
            {
                case StorageType.String:
                    param.Set(value);
                    break;

                case StorageType.Double:
                    if (double.TryParse(value, out double dVal))
                        param.Set(dVal);
                    else
                        TaskDialog.Show("Error", $"'{value}'는 유효한 숫자가 아닙니다.");
                    break;

                case StorageType.Integer:
                    if (int.TryParse(value, out int iVal))
                        param.Set(iVal);
                    else
                        TaskDialog.Show("Error", $"'{value}'는 유효한 정수가 아닙니다.");
                    break;

                case StorageType.ElementId:
                    TaskDialog.Show("Warning", "ElementId 타입은 수동 처리해야 합니다.");
                    break;

                case StorageType.None:
                default:
                    TaskDialog.Show("Error", "지원되지 않는 파라미터 타입입니다.");
                    break;
            }
        }

        public static void StringParameterSetPipe(Pipe instance, string key, string value)
        {
            Parameter param = instance.LookupParameter(key);

            if (param == null)
            {
                TaskDialog.Show("Error", $"'{key}' 파라미터를 찾을 수 없습니다.");
                return;
            }

            if (param.IsReadOnly)
            {
                TaskDialog.Show("Error", $"'{key}' 파라미터는 읽기 전용입니다.");
                return;
            }

            switch (param.StorageType)
            {
                case StorageType.String:
                    param.Set(value);
                    break;

                case StorageType.Double:
                    if (double.TryParse(value, out double dVal))
                        param.Set(dVal);
                    else
                        TaskDialog.Show("Error", $"'{value}'는 유효한 숫자가 아닙니다.");
                    break;

                case StorageType.Integer:
                    if (int.TryParse(value, out int iVal))
                        param.Set(iVal);
                    else
                        TaskDialog.Show("Error", $"'{value}'는 유효한 정수가 아닙니다.");
                    break;

                case StorageType.ElementId:
                    TaskDialog.Show("Warning", "ElementId 타입은 수동 처리해야 합니다.");
                    break;

                case StorageType.None:
                default:
                    TaskDialog.Show("Error", "지원되지 않는 파라미터 타입입니다.");
                    break;
            }
        }
    }
}
