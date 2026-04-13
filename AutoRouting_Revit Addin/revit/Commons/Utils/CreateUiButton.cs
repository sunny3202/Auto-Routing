using System;
using Autodesk.Revit.UI;
using System.IO;
using System.Reflection;
using System.Windows.Media.Imaging;

namespace SARAI.Commons.Utils
{
    public static class CreateUiButton
    {
        public static void CreateButton(RibbonPanel panel, string button_name, string class_name, string tool_tip, string ico_name, int space)
        {
            string thisAssemblyPath = Assembly.GetExecutingAssembly().Location;
            string parentDirectory = Directory.GetParent(thisAssemblyPath).Parent.FullName;
            //Uri uri = new Uri(Path.Combine(Path.GetDirectoryName(parentDirectory), "icons/" + ico_name));
            Uri uri = new Uri(Path.Combine(Path.GetDirectoryName(thisAssemblyPath), "icons/" + ico_name));

            string space_string = "";

            for (int i = 0; i < space; i++)
            {
                space_string += " ";
            }

            try
            {
                PushButtonData btnData = new PushButtonData(button_name, space_string + button_name + space_string, thisAssemblyPath, "SARAI." + class_name);
                PushButton btn = panel.AddItem(btnData) as PushButton;
                BitmapImage bitmap = new BitmapImage(uri);

                btn.ToolTip = tool_tip;
                btn.LargeImage = bitmap;
            }
            catch
            {
                throw new Exception($"000001: Icon Image path have something worng, Please correct icon image path. \n \n{"Current Path: " + parentDirectory+ "/icons/" + ico_name}");
            }
        }
    }
}
