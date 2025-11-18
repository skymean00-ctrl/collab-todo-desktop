using System.Threading.Tasks;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 동기화 서비스 인터페이스
/// </summary>
public interface ISyncService
{
    /// <summary>
    /// 주어진 사용자에 대해 한 번의 동기화를 수행합니다.
    /// </summary>
    Task<(SyncResult Result, SyncState NewState)> PerformSyncAsync(int userId, SyncState state);
}

