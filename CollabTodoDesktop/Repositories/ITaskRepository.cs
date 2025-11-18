using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Models = CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Repositories;

/// <summary>
/// 작업 데이터 접근 인터페이스
/// </summary>
public interface ITaskRepository
{
    /// <summary>
    /// 담당자 기준으로 작업 목록을 조회합니다.
    /// </summary>
    /// <param name="userId">담당자 사용자 ID</param>
    /// <param name="includeCompleted">완료된 작업 포함 여부</param>
    /// <param name="lastSyncedAt">마지막 동기화 시각 (증분 동기화용, null이면 전체 조회)</param>
    Task<List<Models.Task>> ListTasksForAssigneeAsync(int userId, bool includeCompleted = false, DateTime? lastSyncedAt = null);

    /// <summary>
    /// 사용자가 작성자로 되어 있는 작업 목록을 조회합니다.
    /// </summary>
    Task<List<Models.Task>> ListTasksCreatedByUserAsync(int userId);

    /// <summary>
    /// 새 작업을 생성합니다.
    /// </summary>
    Task<int> CreateTaskAsync(int projectId, string title, string? description, int authorId, int currentAssigneeId, int? nextAssigneeId, DateTime? dueDate);

    /// <summary>
    /// 작업 상태를 변경합니다.
    /// </summary>
    Task UpdateTaskStatusAsync(int taskId, int actorId, string newStatus);

    /// <summary>
    /// 작업을 완료 처리하고, 다음 담당자가 있으면 그 사람에게 업무를 넘깁니다.
    /// </summary>
    Task CompleteTaskAndMoveToNextAsync(int taskId, int actorId);
}

