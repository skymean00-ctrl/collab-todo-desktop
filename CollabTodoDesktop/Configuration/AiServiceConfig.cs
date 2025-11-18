namespace CollabTodoDesktop.Configuration;

/// <summary>
/// AI 요약 서비스 설정 값
/// Python 버전의 AiServiceConfig dataclass와 동일한 구조
/// </summary>
public class AiServiceConfig
{
    public string BaseUrl { get; set; } = string.Empty;
    public string? ApiKey { get; set; }
    public int TimeoutSeconds { get; set; } = 15;

    /// <summary>
    /// 필수 설정 값이 있는지 확인
    /// </summary>
    public bool IsValid()
    {
        return !string.IsNullOrWhiteSpace(BaseUrl) && TimeoutSeconds > 0;
    }
}

