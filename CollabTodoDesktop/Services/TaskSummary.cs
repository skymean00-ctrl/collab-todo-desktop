namespace CollabTodoDesktop.Services;

/// <summary>
/// 작업 목록에 대한 간단한 집계 결과
/// Python 버전의 TaskSummary dataclass와 동일한 구조
/// </summary>
public record TaskSummary
{
    public int Total { get; init; }
    public int Pending { get; init; }
    public int InProgress { get; init; }
    public int Review { get; init; }
    public int OnHold { get; init; }
    public int Completed { get; init; }
    public int Cancelled { get; init; }
    public int DueSoon { get; init; }
    public int Overdue { get; init; }
}

