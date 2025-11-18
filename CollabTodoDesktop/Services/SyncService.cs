using System;
using System.Threading.Tasks;
using MySqlConnector;
using CollabTodoDesktop.Configuration;
using CollabTodoDesktop.Repositories;
using CollabTodoDesktop.Utils;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 주기적 동기화(폴링)용 서비스
/// Python 버전의 perform_sync 함수와 동일한 기능
/// </summary>
public class SyncService : ISyncService
{
    private readonly DatabaseConfig _config;
    private readonly ITaskRepository _taskRepository;
    private readonly INotificationRepository _notificationRepository;

    public SyncService(
        DatabaseConfig config,
        ITaskRepository taskRepository,
        INotificationRepository notificationRepository)
    {
        _config = config ?? throw new ArgumentNullException(nameof(config));
        _taskRepository = taskRepository ?? throw new ArgumentNullException(nameof(taskRepository));
        _notificationRepository = notificationRepository ?? throw new ArgumentNullException(nameof(notificationRepository));
    }

    public async Task<(SyncResult Result, SyncState NewState)> PerformSyncAsync(int userId, SyncState state)
    {
        if (userId <= 0)
            throw new ArgumentException("잘못된 사용자 ID 입니다.");

        // 서버 시간 조회
        DateTime serverTime;
        using (var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config))
        {
            using var command = conn.CreateCommand();
            command.CommandText = "SELECT UTC_TIMESTAMP()";
            
            var result = await command.ExecuteScalarAsync();
            if (result == null || !(result is DateTime))
                throw new InvalidOperationException("서버 시간을 가져오지 못했습니다.");

            serverTime = (DateTime)result;
        }

        // 증분 동기화: lastSyncedAt이 있으면 변경된 항목만 조회
        var tasks = await _taskRepository.ListTasksForAssigneeAsync(
            userId,
            includeCompleted: false,
            lastSyncedAt: state.LastSyncedAt
        );

        var notifications = await _notificationRepository.ListUnreadNotificationsAsync(userId);

        var result = new SyncResult
        {
            Tasks = tasks,
            Notifications = notifications,
            ServerTime = serverTime
        };

        var newState = new SyncState(lastSyncedAt: serverTime);
        return (result, newState);
    }
}

