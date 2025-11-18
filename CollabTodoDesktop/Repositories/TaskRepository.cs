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
/// 작업 데이터 접근 구현
/// Python 버전의 Task 관련 함수들과 동일한 기능
/// </summary>
public class TaskRepository : ITaskRepository
{
    private readonly DatabaseConfig _config;

    public TaskRepository(DatabaseConfig config)
    {
        _config = config ?? throw new ArgumentNullException(nameof(config));
    }

    public async Task<List<Models.Task>> ListTasksForAssigneeAsync(int userId, bool includeCompleted = false, DateTime? lastSyncedAt = null)
    {
        if (userId <= 0)
            return new List<Models.Task>();

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        
        // 증분 동기화: lastSyncedAt이 있으면 변경된 항목만 조회
        if (lastSyncedAt.HasValue)
        {
            if (includeCompleted)
            {
                command.CommandText = @"
                    SELECT id, project_id, title, description, author_id, current_assignee_id,
                           next_assignee_id, status, due_date, completed_at, created_at, updated_at
                      FROM tasks
                     WHERE current_assignee_id = @userId
                       AND (updated_at > @lastSyncedAt OR created_at > @lastSyncedAt)
                     ORDER BY
                         CASE status
                             WHEN 'pending' THEN 1
                             WHEN 'in_progress' THEN 2
                             WHEN 'review' THEN 3
                             WHEN 'on_hold' THEN 4
                             WHEN 'completed' THEN 5
                             ELSE 6
                         END,
                         due_date IS NULL,
                         due_date ASC,
                         created_at DESC
                ";
            }
            else
            {
                command.CommandText = @"
                    SELECT id, project_id, title, description, author_id, current_assignee_id,
                           next_assignee_id, status, due_date, completed_at, created_at, updated_at
                      FROM tasks
                     WHERE current_assignee_id = @userId
                       AND status <> 'completed'
                       AND (updated_at > @lastSyncedAt OR created_at > @lastSyncedAt)
                     ORDER BY
                         CASE status
                             WHEN 'pending' THEN 1
                             WHEN 'in_progress' THEN 2
                             WHEN 'review' THEN 3
                             WHEN 'on_hold' THEN 4
                             WHEN 'completed' THEN 5
                             ELSE 6
                         END,
                         due_date IS NULL,
                         due_date ASC,
                         created_at DESC
                ";
            }
            command.Parameters.AddWithValue("@userId", userId);
            command.Parameters.AddWithValue("@lastSyncedAt", lastSyncedAt.Value);
        }
        else if (includeCompleted)
        {
            command.CommandText = @"
                SELECT id, project_id, title, description, author_id, current_assignee_id,
                       next_assignee_id, status, due_date, completed_at, created_at, updated_at
                  FROM tasks
                 WHERE current_assignee_id = @userId
                 ORDER BY
                     CASE status
                         WHEN 'pending' THEN 1
                         WHEN 'in_progress' THEN 2
                         WHEN 'review' THEN 3
                         WHEN 'on_hold' THEN 4
                         WHEN 'completed' THEN 5
                         ELSE 6
                     END,
                     due_date IS NULL,
                     due_date ASC,
                     created_at DESC
            ";
            command.Parameters.AddWithValue("@userId", userId);
        }
        else
        {
            command.CommandText = @"
                SELECT id, project_id, title, description, author_id, current_assignee_id,
                       next_assignee_id, status, due_date, completed_at, created_at, updated_at
                  FROM tasks
                 WHERE current_assignee_id = @userId
                   AND status <> 'completed'
                 ORDER BY
                     CASE status
                         WHEN 'pending' THEN 1
                         WHEN 'in_progress' THEN 2
                         WHEN 'review' THEN 3
                         WHEN 'on_hold' THEN 4
                         WHEN 'completed' THEN 5
                         ELSE 6
                     END,
                     due_date IS NULL,
                     due_date ASC,
                     created_at DESC
            ";
            command.Parameters.AddWithValue("@userId", userId);
        }

        var tasks = new List<Models.Task>();
        using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            tasks.Add(RowToTask(reader));
        }

        return tasks;
    }

    public async Task<List<Models.Task>> ListTasksCreatedByUserAsync(int userId)
    {
        if (userId <= 0)
            return new List<Models.Task>();

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        command.CommandText = @"
            SELECT id, project_id, title, description, author_id, current_assignee_id,
                   next_assignee_id, status, due_date, completed_at, created_at, updated_at
              FROM tasks
             WHERE author_id = @userId
             ORDER BY created_at DESC
        ";
        command.Parameters.AddWithValue("@userId", userId);

        var tasks = new List<Models.Task>();
        using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            tasks.Add(RowToTask(reader));
        }

        return tasks;
    }

    public async Task<int> CreateTaskAsync(int projectId, string title, string? description, int authorId, int currentAssigneeId, int? nextAssigneeId, DateTime? dueDate)
    {
        if (projectId <= 0 || authorId <= 0 || currentAssigneeId <= 0)
            throw new ArgumentException("잘못된 ID 값입니다.");

        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("제목은 비어 있을 수 없습니다.");

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        command.CommandText = @"
            INSERT INTO tasks (
                project_id, title, description, author_id, current_assignee_id,
                next_assignee_id, status, due_date
            )
            VALUES (@projectId, @title, @description, @authorId, @currentAssigneeId,
                    @nextAssigneeId, 'pending', @dueDate)
        ";
        command.Parameters.AddWithValue("@projectId", projectId);
        command.Parameters.AddWithValue("@title", title.Trim());
        command.Parameters.AddWithValue("@description", (object?)description ?? DBNull.Value);
        command.Parameters.AddWithValue("@authorId", authorId);
        command.Parameters.AddWithValue("@currentAssigneeId", currentAssigneeId);
        command.Parameters.AddWithValue("@nextAssigneeId", (object?)nextAssigneeId ?? DBNull.Value);
        command.Parameters.AddWithValue("@dueDate", (object?)dueDate ?? DBNull.Value);

        await command.ExecuteNonQueryAsync();
        return (int)command.LastInsertedId;
    }

    public async Task UpdateTaskStatusAsync(int taskId, int actorId, string newStatus)
    {
        if (taskId <= 0 || actorId <= 0)
            throw new ArgumentException("잘못된 ID 값입니다.");

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        // 트랜잭션 시작
        using var transaction = await conn.BeginTransactionAsync();
        try
        {
            // 현재 상태 조회 (FOR UPDATE)
            using var selectCommand = conn.CreateCommand();
            selectCommand.Transaction = transaction;
            selectCommand.CommandText = @"
                SELECT status
                  FROM tasks
                 WHERE id = @taskId
                 FOR UPDATE
            ";
            selectCommand.Parameters.AddWithValue("@taskId", taskId);

            string? oldStatus = null;
            using (var reader = await selectCommand.ExecuteReaderAsync())
            {
                if (!await reader.ReadAsync())
                    throw new ArgumentException("Task를 찾을 수 없습니다.");
                oldStatus = reader.GetString(reader.GetOrdinal("status"));
            }

            if (oldStatus == "completed" || oldStatus == "cancelled")
            {
                // 이미 종료된 Task는 상태 변경하지 않음
                await transaction.CommitAsync();
                return;
            }

            // 상태 업데이트
            using var updateCommand = conn.CreateCommand();
            updateCommand.Transaction = transaction;
            updateCommand.CommandText = @"
                UPDATE tasks
                   SET status = @newStatus
                 WHERE id = @taskId
            ";
            updateCommand.Parameters.AddWithValue("@newStatus", newStatus);
            updateCommand.Parameters.AddWithValue("@taskId", taskId);
            await updateCommand.ExecuteNonQueryAsync();

            // 이력 기록
            using var historyCommand = conn.CreateCommand();
            historyCommand.Transaction = transaction;
            historyCommand.CommandText = @"
                INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status)
                VALUES (@taskId, @actorId, 'status_change', @oldStatus, @newStatus)
            ";
            historyCommand.Parameters.AddWithValue("@taskId", taskId);
            historyCommand.Parameters.AddWithValue("@actorId", actorId);
            historyCommand.Parameters.AddWithValue("@oldStatus", oldStatus);
            historyCommand.Parameters.AddWithValue("@newStatus", newStatus);
            await historyCommand.ExecuteNonQueryAsync();

            await transaction.CommitAsync();
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }

    public async Task CompleteTaskAndMoveToNextAsync(int taskId, int actorId)
    {
        if (taskId <= 0 || actorId <= 0)
            throw new ArgumentException("잘못된 ID 값입니다.");

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        // 트랜잭션 시작
        using var transaction = await conn.BeginTransactionAsync();
        try
        {
            // 현재 상태 및 다음 담당자 조회 (FOR UPDATE)
            using var selectCommand = conn.CreateCommand();
            selectCommand.Transaction = transaction;
            selectCommand.CommandText = @"
                SELECT status, next_assignee_id
                  FROM tasks
                 WHERE id = @taskId
                 FOR UPDATE
            ";
            selectCommand.Parameters.AddWithValue("@taskId", taskId);

            string? currentStatus = null;
            int? nextAssigneeId = null;
            using (var reader = await selectCommand.ExecuteReaderAsync())
            {
                if (!await reader.ReadAsync())
                    throw new ArgumentException("Task를 찾을 수 없습니다.");
                var statusOrdinal = reader.GetOrdinal("status");
                var nextAssigneeIdOrdinal = reader.GetOrdinal("next_assignee_id");
                currentStatus = reader.GetString(statusOrdinal);
                nextAssigneeId = reader.IsDBNull(nextAssigneeIdOrdinal) ? null : reader.GetInt32(nextAssigneeIdOrdinal);
            }

            if (currentStatus == "completed" || currentStatus == "cancelled")
            {
                await transaction.CommitAsync();
                return;
            }

            string newStatus;
            if (nextAssigneeId == null)
            {
                // 최종 완료
                newStatus = "completed";
                using var updateCommand = conn.CreateCommand();
                updateCommand.Transaction = transaction;
                updateCommand.CommandText = @"
                    UPDATE tasks
                       SET status = @newStatus, completed_at = NOW()
                     WHERE id = @taskId
                ";
                updateCommand.Parameters.AddWithValue("@newStatus", newStatus);
                updateCommand.Parameters.AddWithValue("@taskId", taskId);
                await updateCommand.ExecuteNonQueryAsync();
            }
            else
            {
                // 다음 담당자에게 전달, 상태는 review로 설정
                newStatus = "review";
                using var updateCommand = conn.CreateCommand();
                updateCommand.Transaction = transaction;
                updateCommand.CommandText = @"
                    UPDATE tasks
                       SET current_assignee_id = @nextAssigneeId, status = @newStatus
                     WHERE id = @taskId
                ";
                updateCommand.Parameters.AddWithValue("@nextAssigneeId", nextAssigneeId.Value);
                updateCommand.Parameters.AddWithValue("@newStatus", newStatus);
                updateCommand.Parameters.AddWithValue("@taskId", taskId);
                await updateCommand.ExecuteNonQueryAsync();
            }

            // 이력 기록
            using var historyCommand = conn.CreateCommand();
            historyCommand.Transaction = transaction;
            historyCommand.CommandText = @"
                INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status)
                VALUES (@taskId, @actorId, 'complete_or_forward', @oldStatus, @newStatus)
            ";
            historyCommand.Parameters.AddWithValue("@taskId", taskId);
            historyCommand.Parameters.AddWithValue("@actorId", actorId);
            historyCommand.Parameters.AddWithValue("@oldStatus", currentStatus);
            historyCommand.Parameters.AddWithValue("@newStatus", newStatus);
            await historyCommand.ExecuteNonQueryAsync();

            await transaction.CommitAsync();
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }

    private static Models.Task RowToTask(MySqlDataReader reader)
    {
        // status 문자열을 TaskStatus enum으로 변환
        var statusStr = reader.GetString(reader.GetOrdinal("status")).ToLowerInvariant();
        var status = statusStr switch
        {
            "pending" => Models.TaskStatus.Pending,
            "in_progress" => Models.TaskStatus.InProgress,
            "review" => Models.TaskStatus.Review,
            "completed" => Models.TaskStatus.Completed,
            "on_hold" => Models.TaskStatus.OnHold,
            "cancelled" => Models.TaskStatus.Cancelled,
            _ => Models.TaskStatus.Pending
        };

        var descriptionOrdinal = reader.GetOrdinal("description");
        var nextAssigneeIdOrdinal = reader.GetOrdinal("next_assignee_id");
        var dueDateOrdinal = reader.GetOrdinal("due_date");
        var completedAtOrdinal = reader.GetOrdinal("completed_at");

        return new Models.Task
        {
            Id = reader.GetInt32(reader.GetOrdinal("id")),
            ProjectId = reader.GetInt32(reader.GetOrdinal("project_id")),
            Title = reader.GetString(reader.GetOrdinal("title")),
            Description = reader.IsDBNull(descriptionOrdinal) ? null : reader.GetString(descriptionOrdinal),
            AuthorId = reader.GetInt32(reader.GetOrdinal("author_id")),
            CurrentAssigneeId = reader.GetInt32(reader.GetOrdinal("current_assignee_id")),
            NextAssigneeId = reader.IsDBNull(nextAssigneeIdOrdinal) ? null : reader.GetInt32(nextAssigneeIdOrdinal),
            Status = status,
            DueDate = reader.IsDBNull(dueDateOrdinal) ? null : reader.GetDateTime(dueDateOrdinal),
            CompletedAt = reader.IsDBNull(completedAtOrdinal) ? null : reader.GetDateTime(completedAtOrdinal),
            CreatedAt = reader.GetDateTime(reader.GetOrdinal("created_at")),
            UpdatedAt = reader.GetDateTime(reader.GetOrdinal("updated_at"))
        };
    }
}

