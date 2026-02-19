using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Extensions.DependencyInjection;
using CollabTodoDesktop.Services;
using CollabTodoDesktop.Views;

namespace CollabTodoDesktop.ViewModels;

public class MainWindowViewModel : INotifyPropertyChanged
{
    private static readonly TimeSpan[] RetryIntervals =
    {
        TimeSpan.FromMinutes(1),
        TimeSpan.FromMinutes(5),
        TimeSpan.FromMinutes(15),
    };

    private readonly ApiClient _api;
    private readonly IDashboardService _dashboard;
    private readonly DispatcherTimer _syncTimer;

    private DateTime? _lastSyncedAt;
    private int _consecutiveFailures;
    private DateTime? _nextRetryAt;

    // 바인딩 속성 백킹 필드
    private bool _isConnected;
    private DateTime? _lastSyncTime;
    private string _windowTitle = "Collab To-Do Desktop";
    private TaskItemViewModel? _selectedTask;
    private string _statusBarMessage = "준비";
    private int _unreadNotificationCount;

    public MainWindowViewModel(ApiClient api, IDashboardService dashboard)
    {
        _api = api;
        _dashboard = dashboard;

        WindowTitle = $"Collab To-Do Desktop — {_api.CurrentDisplayName}";

        _syncTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(5) };
        _syncTimer.Tick += OnSyncTimer;
        _syncTimer.Start();

        // 앱 시작 즉시 한 번 동기화
        _ = DoSyncAsync();
    }

    // ── 바인딩 속성 ─────────────────────────────────────────

    public string WindowTitle
    {
        get => _windowTitle;
        set { _windowTitle = value; OnPropertyChanged(); }
    }

    public bool IsConnected
    {
        get => _isConnected;
        set { _isConnected = value; OnPropertyChanged(); OnPropertyChanged(nameof(ConnectionStatus)); }
    }

    public string ConnectionStatus => IsConnected ? "● 연결됨" : "● 연결 끊김";

    public DateTime? LastSyncTime
    {
        get => _lastSyncTime;
        set { _lastSyncTime = value; OnPropertyChanged(); OnPropertyChanged(nameof(LastSyncTimeText)); }
    }

    public string LastSyncTimeText =>
        LastSyncTime == null ? "마지막 동기화: -" : $"마지막 동기화: {LastSyncTime.Value:HH:mm:ss}";

    public string StatusBarMessage
    {
        get => _statusBarMessage;
        set { _statusBarMessage = value; OnPropertyChanged(); }
    }

    public int UnreadNotificationCount
    {
        get => _unreadNotificationCount;
        set
        {
            _unreadNotificationCount = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(NotificationText));
        }
    }

    public string NotificationText =>
        UnreadNotificationCount > 0 ? $"🔔 {UnreadNotificationCount}개" : "";

    public ObservableCollection<TaskItemViewModel> Tasks { get; } = new();
    public string TaskCountText => Tasks.Count == 0 ? "" : $"({Tasks.Count}개)";
    public bool HasNoTasks => Tasks.Count == 0;

    public TaskItemViewModel? SelectedTask
    {
        get => _selectedTask;
        set { _selectedTask = value; OnPropertyChanged(); OnPropertyChanged(nameof(HasSelectedTask)); }
    }

    public bool HasSelectedTask => SelectedTask != null;

    public ObservableCollection<string> DashboardItems { get; } = new();

    // ── 동기화 ──────────────────────────────────────────────

    private async void OnSyncTimer(object? sender, EventArgs e)
    {
        if (_nextRetryAt.HasValue && DateTime.UtcNow < _nextRetryAt.Value)
            return;

        await DoSyncAsync();
    }

    private async System.Threading.Tasks.Task DoSyncAsync()
    {
        try
        {
            var result = await _api.SyncAsync(_lastSyncedAt);
            if (result == null) return;

            _consecutiveFailures = 0;
            _nextRetryAt = null;
            _lastSyncedAt = result.ServerTime;

            IsConnected = true;
            LastSyncTime = result.ServerTime.ToLocalTime();
            StatusBarMessage = "동기화 완료";

            UpdateTaskList(result.Tasks, DateTime.UtcNow);
            UpdateDashboard(result.Tasks, DateTime.UtcNow);
            UnreadNotificationCount = result.Notifications.Count;
        }
        catch (UnauthorizedAccessException)
        {
            // 토큰 만료 → 로그인 창 다시 표시
            _syncTimer.Stop();
            _api.Logout();
            var login = new LoginWindow(_api) { Owner = Application.Current.MainWindow };
            if (login.ShowDialog() == true)
            {
                _lastSyncedAt = null;
                _syncTimer.Start();
            }
            else
            {
                Application.Current.Shutdown();
            }
        }
        catch (Exception ex)
        {
            _consecutiveFailures++;
            IsConnected = false;

            var retryIndex = Math.Min(_consecutiveFailures - 1, RetryIntervals.Length - 1);
            _nextRetryAt = DateTime.UtcNow + RetryIntervals[retryIndex];
            var retryMin = (int)RetryIntervals[retryIndex].TotalMinutes;

            StatusBarMessage = $"연결 실패 ({_consecutiveFailures}회) — {retryMin}분 후 재시도";
            System.Diagnostics.Debug.WriteLine($"[SyncError] {ex.Message}");
        }
    }

    // ── Task 목록 업데이트 ───────────────────────────────────

    private void UpdateTaskList(System.Collections.Generic.List<ApiClient.TaskOut> tasks, DateTime now)
    {
        var previousSelectedId = SelectedTask?.Id;
        Tasks.Clear();

        foreach (var t in tasks)
        {
            var status = ParseStatus(t.Status);
            var model = new Models.Task
            {
                Id = t.Id, ProjectId = t.ProjectId, Title = t.Title,
                Description = t.Description, AuthorId = t.AuthorId,
                CurrentAssigneeId = t.CurrentAssigneeId, NextAssigneeId = t.NextAssigneeId,
                Status = status, DueDate = t.DueDate, CompletedAt = t.CompletedAt,
                CreatedAt = t.CreatedAt, UpdatedAt = t.UpdatedAt,
            };
            Tasks.Add(new TaskItemViewModel(model, now));
        }

        OnPropertyChanged(nameof(TaskCountText));
        OnPropertyChanged(nameof(HasNoTasks));

        if (previousSelectedId.HasValue)
            foreach (var item in Tasks)
                if (item.Id == previousSelectedId.Value) { SelectedTask = item; break; }
    }

    private void UpdateDashboard(System.Collections.Generic.List<ApiClient.TaskOut> tasks, DateTime now)
    {
        // API TaskOut → Models.Task 변환 후 DashboardService에 전달
        var modelTasks = new System.Collections.Generic.List<Models.Task>();
        foreach (var t in tasks)
            modelTasks.Add(new Models.Task
            {
                Id = t.Id, ProjectId = t.ProjectId, Title = t.Title,
                Status = ParseStatus(t.Status), DueDate = t.DueDate,
            });

        var summary = _dashboard.SummarizeTasks(modelTasks, now);
        DashboardItems.Clear();
        DashboardItems.Add($"전체 작업: {summary.Total}");
        DashboardItems.Add($"대기: {summary.Pending}");
        DashboardItems.Add($"진행 중: {summary.InProgress}");
        DashboardItems.Add($"검토: {summary.Review}");
        DashboardItems.Add($"보류: {summary.OnHold}");
        DashboardItems.Add($"완료: {summary.Completed}");
        DashboardItems.Add($"취소: {summary.Cancelled}");
        DashboardItems.Add("──────────────");
        DashboardItems.Add($"기한 임박(24h): {summary.DueSoon}");
        DashboardItems.Add($"기한 초과: {summary.Overdue}");
    }

    private static Models.TaskStatus ParseStatus(string s) => s switch
    {
        "in_progress" => Models.TaskStatus.InProgress,
        "review"      => Models.TaskStatus.Review,
        "completed"   => Models.TaskStatus.Completed,
        "on_hold"     => Models.TaskStatus.OnHold,
        "cancelled"   => Models.TaskStatus.Cancelled,
        _             => Models.TaskStatus.Pending,
    };

    // ── Task 액션 ────────────────────────────────────────────

    public async void OnChangeStatusCommand()
    {
        if (SelectedTask == null) return;

        var dialog = new StatusChangeDialog { Owner = Application.Current.MainWindow };
        if (dialog.ShowDialog() != true || dialog.SelectedStatus == null) return;

        try
        {
            await _api.UpdateTaskStatusAsync(SelectedTask.Id, dialog.SelectedStatus);
            StatusBarMessage = "상태가 변경되었습니다.";
            _lastSyncedAt = null; // 전체 재동기화
        }
        catch (Exception ex)
        {
            MessageBox.Show($"상태 변경 실패: {ex.Message}", "오류",
                MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    public async void OnCompleteTaskCommand()
    {
        if (SelectedTask == null) return;

        var confirm = MessageBox.Show(
            "선택한 작업을 완료 처리하시겠습니까?\n(다음 담당자가 있으면 자동으로 전달됩니다)",
            "완료 확인", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (confirm != MessageBoxResult.Yes) return;

        try
        {
            await _api.CompleteTaskAsync(SelectedTask.Id);
            StatusBarMessage = "작업이 완료 처리되었습니다.";
            _lastSyncedAt = null;
        }
        catch (Exception ex)
        {
            MessageBox.Show($"완료 처리 실패: {ex.Message}", "오류",
                MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    // ── INotifyPropertyChanged ───────────────────────────────

    public event PropertyChangedEventHandler? PropertyChanged;
    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
}
