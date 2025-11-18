using System;

namespace CollabTodoDesktop.Models;

/// <summary>
/// 알림 도메인 모델
/// Python 버전의 Notification dataclass와 동일한 구조
/// </summary>
public record Notification
{
    public int Id { get; init; }
    public int RecipientId { get; init; }
    public int? TaskId { get; init; }
    public string NotificationType { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
    public bool IsRead { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime? ReadAt { get; init; }
}

