using System.Windows;
using CollabTodoDesktop.ViewModels;

namespace CollabTodoDesktop.Views;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow()
    {
        InitializeComponent();

        // ViewModel을 App의 ServiceProvider로부터 가져오기
        var app = (App)Application.Current;
        _viewModel = new ViewModels.MainWindowViewModel(app.ServiceProvider);
        DataContext = _viewModel;
    }

    private void OnAiSummaryTest_Click(object sender, RoutedEventArgs e)
    {
        _viewModel.OnAiSummaryTest();
    }
}

