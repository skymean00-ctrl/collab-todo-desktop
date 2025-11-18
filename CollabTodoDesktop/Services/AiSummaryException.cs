using System;

namespace CollabTodoDesktop.Services;

/// <summary>
/// AI 요약 호출 실패 시 사용하는 예외
/// Python 버전의 AiSummaryError와 동일
/// </summary>
public class AiSummaryException : Exception
{
    public AiSummaryException(string message) : base(message)
    {
    }

    public AiSummaryException(string message, Exception innerException) 
        : base(message, innerException)
    {
    }
}

