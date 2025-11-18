using System;

namespace CollabTodoDesktop.Models;

/// <summary>
/// 사용자 도메인 모델
/// Python 버전의 User dataclass와 동일한 구조
/// </summary>
public record User
{
    public int Id { get; init; }
    public string Username { get; init; } = string.Empty;
    public string DisplayName { get; init; } = string.Empty;
    public string Email { get; init; } = string.Empty;
    public UserRole Role { get; init; }
    public bool IsActive { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; init; }
}

