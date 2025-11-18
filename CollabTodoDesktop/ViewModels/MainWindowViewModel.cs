using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;
using Microsoft.Extensions.DependencyInjection;
using CollabTodoDesktop.Configuration;
using CollabTodoDesktop.Models;
using CollabTodoDesktop.Repositories;
using CollabTodoDesktop.Services;

namespace CollabTodoDesktop.ViewModels;

/// <summary>
/// MainWindow의 ViewModel (MVVM 패턴)
/// Python 버전의 MainWindow 클래스와 동일한 기능
/// </summary>
public class MainWindowViewModel : INotifyPropertyChanged
{
    private readonly IServiceProvider _serviceProvider;
    private readonly DispatcherTimer _syncTimer;
    private SyncState _syncState;
    private int? _currentUserId;
    private bool _isConnected;
    private DateTime? _lastSyncTime;
    private string _windowTitle = "Collab To-Do Desktop";

    public MainWindowViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));
        _syncState = new SyncState();

        // 주기적 동기화 타이머 (5초 간격)
        _syncTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(5)
        };
        _syncTimer.Tick += OnSyncTimer;
        _syncTimer.Start();

        // 초기화
        _ = InitializeAsync();
    }

    public string WindowTitle
    {
        get => _windowTitle;
        set
        {
            _windowTitle = value;
            OnPropertyChanged();
        }
    }

    public bool IsConnected
    {
        get => _isConnected;
        set
        {
            _isConnected = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(ConnectionStatus));
        }
    }

    public string ConnectionStatus => IsConnected ? "DB: 연결됨" : "DB: 끊김";

    public DateTime? LastSyncTime
    {
        get => _lastSyncTime;
        set
        {
            _lastSyncTime = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(LastSyncTimeText));
        }
    }

    public string LastSyncTimeText
    {
        get
        {
            if (LastSyncTime == null)
                return "마지막 동기화: -";
            return $"마지막 동기화: {LastSyncTime.Value:yyyy-MM-dd HH:mm:ss} UTC";
        }
    }

    public ObservableCollection<string> DashboardItems { get; } = new();

    private async Task InitializeAsync()
    {
        try
        {
            await InitializeUserSelectionAsync();
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                $"초기화 중 오류가 발생했습니다: {ex.Message}",
                "오류",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private async Task InitializeUserSelectionAsync()
    {
        var configManager = _serviceProvider.GetRequiredService<ConfigurationManager>();
        var dbConfig = configManager.LoadDatabaseConfig();

        if (dbConfig == null)
        {
            MessageBox.Show(
                "데이터베이스 설정이 완료되지 않았습니다.\n환경 변수를 확인한 후 프로그램을 다시 시작하세요.",
                "설정 필요",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
            return;
        }

        try
        {
            var userRepository = _serviceProvider.GetRequiredService<IUserRepository>();
            var users = await userRepository.ListActiveUsersAsync();

            if (users.Count == 0)
            {
                MessageBox.Show(
                    "활성 사용자가 없습니다.\n데이터베이스를 확인하세요.",
                    "사용자 없음",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
                return;
            }

            // 사용자 선택 다이얼로그 표시
            var dialog = new Views.UserSelectionDialog(users);
            if (dialog.ShowDialog() == true)
            {
                var selectedUser = dialog.SelectedUser;
                if (selectedUser != null)
                {
                    _currentUserId = selectedUser.Id;
                    WindowTitle = $"Collab To-Do Desktop - {selectedUser.DisplayName}";
                }
                else
                {
                    // 사용자가 취소한 경우 첫 번째 사용자를 기본값으로 사용
                    _currentUserId = users[0].Id;
                    WindowTitle = $"Collab To-Do Desktop - {users[0].DisplayName}";
                }
            }
            else
            {
                // 취소한 경우 첫 번째 사용자를 기본값으로 사용
                _currentUserId = users[0].Id;
                WindowTitle = $"Collab To-Do Desktop - {users[0].DisplayName}";
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                $"데이터베이스에 연결할 수 없습니다.\n연결 설정을 확인하세요.\n\n오류: {ex.Message}",
                "연결 실패",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
    }

    private async void OnSyncTimer(object? sender, EventArgs e)
    {
        if (_currentUserId == null)
        {
            IsConnected = false;
            return;
        }

        var configManager = _serviceProvider.GetRequiredService<ConfigurationManager>();
        var dbConfig = configManager.LoadDatabaseConfig();

        if (dbConfig == null)
        {
            IsConnected = false;
            return;
        }

        try
        {
            var syncService = _serviceProvider.GetRequiredService<ISyncService>();
            var (result, newState) = await syncService.PerformSyncAsync(_currentUserId.Value, _syncState);
            
            _syncState = newState;
            IsConnected = true;
            LastSyncTime = result.ServerTime;
            UpdateDashboard(result.ServerTime, result.Tasks);
        }
        catch (Exception ex)
        {
            IsConnected = false;
            MessageBox.Show(
                $"동기화 중 오류가 발생했습니다: {ex.Message}",
                "동기화 오류",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
    }

    private void UpdateDashboard(DateTime now, System.Collections.Generic.List<Task> tasks)
    {
        var dashboardService = _serviceProvider.GetRequiredService<IDashboardService>();
        var summary = dashboardService.SummarizeTasks(tasks, now);

        DashboardItems.Clear();
        DashboardItems.Add($"전체 작업: {summary.Total}");
        DashboardItems.Add($"대기(pending): {summary.Pending}");
        DashboardItems.Add($"진행 중: {summary.InProgress}");
        DashboardItems.Add($"검토(review): {summary.Review}");
        DashboardItems.Add($"보류(on_hold): {summary.OnHold}");
        DashboardItems.Add($"완료(completed): {summary.Completed}");
        DashboardItems.Add($"취소(cancelled): {summary.Cancelled}");
        DashboardItems.Add($"기한 임박(24h): {summary.DueSoon}");
        DashboardItems.Add($"기한 초과: {summary.Overdue}");
    }

    public async void OnAiSummaryTest()
    {
        var configManager = _serviceProvider.GetRequiredService<ConfigurationManager>();
        var aiConfig = configManager.LoadAiServiceConfig();

        if (aiConfig == null)
        {
            MessageBox.Show(
                "AI 요약 서비스를 사용하려면 COLLAB_TODO_AI_BASE_URL 환경 변수를 설정해야 합니다.",
                "AI 설정 필요",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
            return;
        }

        var sampleText = (
            "이 작업은 협업 기반 할 일 관리 시스템의 초기 버전을 구현하는 것입니다. " +
            "Windows 데스크톱 클라이언트를 만들고, NAS에 있는 MySQL 데이터베이스와 연동하며, " +
            "기본적인 작업 생성, 할당, 완료, 알림 기능을 제공합니다."
        );

        try
        {
            var aiClient = _serviceProvider.GetRequiredService<IAiClientService>();
            var summary = await aiClient.SummarizeTextAsync(sampleText, "ko");

            if (string.IsNullOrEmpty(summary))
            {
                summary = "(요약 결과가 비어 있습니다.)";
            }

            MessageBox.Show(
                $"원문:\n{sampleText}\n\n요약:\n{summary}",
                "AI 요약 결과",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }
        catch (AiSummaryException ex)
        {
            MessageBox.Show(
                $"요약 서비스 호출에 실패했습니다.\n\n원문:\n{sampleText}\n\n오류: {ex.Message}",
                "AI 요약 실패",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                $"요약 서비스 호출 중 오류가 발생했습니다.\n\n오류: {ex.Message}",
                "오류",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}

