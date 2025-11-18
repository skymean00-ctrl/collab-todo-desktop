using System;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 클라이언트가 유지하는 최소 동기화 상태
/// Python 버전의 SyncState dataclass와 동일한 구조
/// </summary>
public record SyncState
{
    public DateTime? LastSyncedAt { get; init; }

    public SyncState(DateTime? lastSyncedAt = null)
    {
        LastSyncedAt = lastSyncedAt;
    }
}

