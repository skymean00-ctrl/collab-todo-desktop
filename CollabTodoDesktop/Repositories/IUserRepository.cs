using System.Collections.Generic;
using System.Threading.Tasks;
using Models = CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Repositories;

/// <summary>
/// 사용자 데이터 접근 인터페이스
/// </summary>
public interface IUserRepository
{
    /// <summary>
    /// ID로 사용자를 조회합니다.
    /// </summary>
    Task<Models.User?> GetUserByIdAsync(int userId);

    /// <summary>
    /// 활성 사용자 목록을 조회합니다.
    /// </summary>
    Task<List<Models.User>> ListActiveUsersAsync();
}

