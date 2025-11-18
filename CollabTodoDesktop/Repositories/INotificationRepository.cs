using System.Collections.Generic;
using System.Threading.Tasks;
using Models = CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Repositories;

/// <summary>
/// 알림 데이터 접근 인터페이스
/// </summary>
public interface INotificationRepository
{
    /// <summary>
    /// 읽지 않은 알림 목록을 조회합니다.
    /// </summary>
    Task<List<Models.Notification>> ListUnreadNotificationsAsync(int userId);

    /// <summary>
    /// 알림을 읽음 처리합니다.
    /// </summary>
    Task MarkNotificationsAsReadAsync(int userId, List<int> notificationIds);
}

