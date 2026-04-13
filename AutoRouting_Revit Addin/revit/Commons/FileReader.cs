using Autodesk.Revit.UI;
using System.Windows.Forms;

namespace SARAI.Commons
{
    public class FileReader
    {
        public readonly string ReadPath;

        public FileReader()
        {
            OpenFileDialog openFileDialog = new OpenFileDialog
            {
                Filter = "모든 파일 (*.*)|*.*"
            };

            if (openFileDialog.ShowDialog() == DialogResult.OK)
            {
                // 사용자가 선택한 파일의 경로 가져오기
                this.ReadPath = openFileDialog.FileName;
            }
            else
            {
                // 사용자가 취소한 경우
                TaskDialog.Show("취소", "파일 선택이 취소되었습니다.");
            }
        }
    }
}

