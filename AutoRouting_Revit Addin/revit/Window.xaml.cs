using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Windows;
using System.IO;

namespace SARAI
{
    public partial class Window
    {
        private Dictionary<string, double> _phaseData;

        public double SelectedValue { get; private set; }

        public Window()
        {
            InitializeComponent();
            LoadJsonData();
        }

        private void LoadJsonData()
        {
            try
            {
                string assemblyPath = System.Reflection.Assembly.GetExecutingAssembly().Location;
                string baseDir = System.IO.Path.GetDirectoryName(assemblyPath);
                string routing_option_jsonPath = Path.Combine(baseDir, "LogicPart/phase_data.json");
                string jsonText = File.ReadAllText(routing_option_jsonPath);

                _phaseData = JsonConvert.DeserializeObject<Dictionary<string, double>>(jsonText);

                PhaseComboBox.ItemsSource = _phaseData.Keys;
            }
            catch (Exception ex)
            {
                MessageBox.Show("JSON 읽기 오류: " + ex.Message);
            }
        }

        private void ConfirmButton_Click(object sender, RoutedEventArgs e)
        {
            if (PhaseComboBox.SelectedItem != null)
            {
                string selectedKey = PhaseComboBox.SelectedItem.ToString();
                if (_phaseData.ContainsKey(selectedKey))
                {
                    SelectedValue = _phaseData[selectedKey];
                    this.DialogResult = true;
                    this.Close();
                }
            }
            else
            {
                MessageBox.Show("Phase를 선택하세요.");
            }
        }
    }
}
