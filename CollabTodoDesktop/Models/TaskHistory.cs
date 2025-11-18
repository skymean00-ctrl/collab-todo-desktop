using System;

namespace CollabTodoDesktop.Models;

/// <summary>
/// 작업 이력 도메인 모델
/// Python 버전의 TaskHistory dataclass와 동일한 구조
/// </summary>
public record TaskHistory
{
    public int Id { get; init; }
    public int TaskId { get; init; }
    public int ActorId { get; init; }
    public string ActionType { get; init; } = string.Empty;
    public string? OldStatus { get; init; }
    public string? NewStatus { get; init; }
    public string? Note { get; init; }
    public DateTime CreatedAt { get; init; }
}

