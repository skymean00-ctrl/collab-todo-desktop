using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using MySqlConnector;
using Models = CollabTodoDesktop.Models;
using CollabTodoDesktop.Configuration;
using CollabTodoDesktop.Utils;

namespace CollabTodoDesktop.Repositories;

/// <summary>
/// 알림 데이터 접근 구현
/// Python 버전의 notification 관련 함수들과 동일한 기능
/// </summary>
public class NotificationRepository : INotificationRepository
{
    private readonly DatabaseConfig _config;

    public NotificationRepository(DatabaseConfig config)
    {
        _config = config ?? throw new ArgumentNullException(nameof(config));
    }

    public async Task<List<Models.Notification>> ListUnreadNotificationsAsync(int userId)
    {
        if (userId <= 0)
            return new List<Models.Notification>();

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        command.CommandText = @"
            SELECT id, recipient_id, task_id, notification_type, message,
                   is_read, created_at, read_at
              FROM notifications
             WHERE recipient_id = @userId
               AND is_read = 0
             ORDER BY created_at DESC
        ";
        command.Parameters.AddWithValue("@userId", userId);

        var notifications = new List<Models.Notification>();
        using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            notifications.Add(RowToNotification(reader));
        }

        return notifications;
    }

    public async Task MarkNotificationsAsReadAsync(int userId, List<int> notificationIds)
    {
        if (userId <= 0 || notificationIds == null || notificationIds.Count == 0)
            return;

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        // IN 절을 위한 파라미터 생성
        var placeholders = string.Join(",", notificationIds.Select((_, i) => $"@id{i}"));
        
        using var command = conn.CreateCommand();
        command.CommandText = $@"
            UPDATE notifications
               SET is_read = 1, read_at = NOW()
             WHERE recipient_id = @userId
               AND id IN ({placeholders})
        ";
        command.Parameters.AddWithValue("@userId", userId);
        for (int i = 0; i < notificationIds.Count; i++)
        {
            command.Parameters.AddWithValue($"@id{i}", notificationIds[i]);
        }

        await command.ExecuteNonQueryAsync();
    }

    private static Models.Notification RowToNotification(MySqlDataReader reader)
    {
        var taskIdOrdinal = reader.GetOrdinal("task_id");
        var readAtOrdinal = reader.GetOrdinal("read_at");

        return new Models.Notification
        {
            Id = reader.GetInt32(reader.GetOrdinal("id")),
            RecipientId = reader.GetInt32(reader.GetOrdinal("recipient_id")),
            TaskId = reader.IsDBNull(taskIdOrdinal) ? null : reader.GetInt32(taskIdOrdinal),
            NotificationType = reader.GetString(reader.GetOrdinal("notification_type")),
            Message = reader.GetString(reader.GetOrdinal("message")),
            IsRead = reader.GetBoolean(reader.GetOrdinal("is_read")),
            CreatedAt = reader.GetDateTime(reader.GetOrdinal("created_at")),
            ReadAt = reader.IsDBNull(readAtOrdinal) ? null : reader.GetDateTime(readAtOrdinal)
        };
    }
}

