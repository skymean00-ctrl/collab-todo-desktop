using System.Windows;
using System.Windows.Controls;

namespace CollabTodoDesktop.Views;

/// <summary>
/// Task 상태 변경 다이얼로그
/// </summary>
public partial class StatusChangeDialog : Window
{
    public string? SelectedStatus { get; private set; }

    public StatusChangeDialog()
    {
        InitializeComponent();
    }

    private void OnConfirm_Click(object sender, RoutedEventArgs e)
    {
        if (StatusListBox.SelectedItem is ListBoxItem item)
        {
            SelectedStatus = item.Tag?.ToString();
            DialogResult = true;
        }
        else
        {
            MessageBox.Show("상태를 선택해 주세요.", "선택 필요",
                MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void OnCancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
    }
}
