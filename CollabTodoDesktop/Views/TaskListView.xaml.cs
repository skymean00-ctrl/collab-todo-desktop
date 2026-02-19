using System.Windows;
using System.Windows.Controls;
using CollabTodoDesktop.ViewModels;

namespace CollabTodoDesktop.Views;

/// <summary>
/// TaskListView.xaml의 코드 비하인드
/// </summary>
public partial class TaskListView : UserControl
{
    public TaskListView()
    {
        InitializeComponent();
    }

    private void OnChangeStatus_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm)
            vm.OnChangeStatusCommand();
    }

    private void OnCompleteTask_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm)
            vm.OnCompleteTaskCommand();
    }

    private void OnTaskDoubleClick(object sender, System.Windows.Input.MouseButtonEventArgs e)
    {
        // 더블클릭 시 상태 변경 다이얼로그 (Phase 1-B에서 구현)
    }
}
