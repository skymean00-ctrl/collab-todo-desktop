using System;

namespace CollabTodoDesktop.Models;

/// <summary>
/// 작업 도메인 모델
/// Python 버전의 Task dataclass와 동일한 구조
/// </summary>
public record Task
{
    public int Id { get; init; }
    public int ProjectId { get; init; }
    public string Title { get; init; } = string.Empty;
    public string? Description { get; init; }
    public int AuthorId { get; init; }
    public int CurrentAssigneeId { get; init; }
    public int? NextAssigneeId { get; init; }
    public TaskStatus Status { get; init; }
    public DateTime? DueDate { get; init; }
    public DateTime? CompletedAt { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; init; }
}

