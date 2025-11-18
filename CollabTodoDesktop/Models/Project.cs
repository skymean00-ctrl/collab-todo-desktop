using System;

namespace CollabTodoDesktop.Models;

/// <summary>
/// 프로젝트 도메인 모델
/// Python 버전의 Project dataclass와 동일한 구조
/// </summary>
public record Project
{
    public int Id { get; init; }
    public string Name { get; init; } = string.Empty;
    public string? Description { get; init; }
    public int OwnerId { get; init; }
    public bool IsArchived { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; init; }
}

