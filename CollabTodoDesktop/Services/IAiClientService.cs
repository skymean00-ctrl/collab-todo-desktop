using System.Threading.Tasks;

namespace CollabTodoDesktop.Services;

/// <summary>
/// AI 클라이언트 서비스 인터페이스
/// </summary>
public interface IAiClientService
{
    /// <summary>
    /// 주어진 텍스트를 요약 API에 전달하고 요약 결과를 문자열로 반환합니다.
    /// </summary>
    /// <param name="text">요약할 텍스트</param>
    /// <param name="targetLanguage">대상 언어 (기본값: "ko")</param>
    Task<string> SummarizeTextAsync(string text, string targetLanguage = "ko");
}

