using System;
using System.Collections.Generic;
using CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 한 번의 동기화 결과
/// Python 버전의 SyncResult dataclass와 동일한 구조
/// </summary>
public record SyncResult
{
    public List<Task> Tasks { get; init; } = new();
    public List<Notification> Notifications { get; init; } = new();
    public DateTime ServerTime { get; init; }
}

