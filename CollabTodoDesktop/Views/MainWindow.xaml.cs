using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using CollabTodoDesktop.Services;
using CollabTodoDesktop.ViewModels;

namespace CollabTodoDesktop.Views;

public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow()
    {
        InitializeComponent();

        var app = (App)Application.Current;
        var api = app.ServiceProvider.GetRequiredService<ApiClient>();
        var dashboard = app.ServiceProvider.GetRequiredService<IDashboardService>();

        _viewModel = new MainWindowViewModel(api, dashboard);
        DataContext = _viewModel;
    }

    private void OnAiSummaryTest_Click(object sender, RoutedEventArgs e)
    {
        MessageBox.Show("AI 요약 기능은 준비 중입니다.", "안내",
            MessageBoxButton.OK, MessageBoxImage.Information);
    }
}
