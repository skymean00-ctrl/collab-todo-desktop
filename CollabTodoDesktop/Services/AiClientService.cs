using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using CollabTodoDesktop.Configuration;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 외부 LLM(요약 API) 호출용 클라이언트
/// Python 버전의 summarize_text 함수와 동일한 기능
/// </summary>
public class AiClientService : IAiClientService
{
    private readonly AiServiceConfig _config;
    private readonly HttpClient _httpClient;

    public AiClientService(AiServiceConfig config, HttpClient httpClient)
    {
        _config = config ?? throw new ArgumentNullException(nameof(config));
        _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
    }

    public async Task<string> SummarizeTextAsync(string text, string targetLanguage = "ko")
    {
        var cleaned = text?.Trim() ?? string.Empty;
        if (string.IsNullOrEmpty(cleaned))
            return string.Empty;

        if (!_config.IsValid())
            throw new AiSummaryException("AI 서비스 설정이 유효하지 않습니다.");

        var baseUrl = _config.BaseUrl.TrimEnd('/');
        var url = $"{baseUrl}/summarize";

        var payload = new
        {
            text = cleaned,
            target_language = targetLanguage
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, url);
        request.Content = JsonContent.Create(payload);

        // API 키가 있으면 헤더에 추가
        if (!string.IsNullOrWhiteSpace(_config.ApiKey))
        {
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue(
                "Bearer", _config.ApiKey);
        }

        try
        {
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_config.TimeoutSeconds));
            var response = await _httpClient.SendAsync(request, cts.Token);

            if (!response.IsSuccessStatusCode)
            {
                throw new AiSummaryException(
                    $"요약 서비스 오류 상태 코드: {(int)response.StatusCode}");
            }

            var jsonDocument = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync());
            var root = jsonDocument.RootElement;

            if (!root.TryGetProperty("summary", out var summaryElement))
            {
                throw new AiSummaryException("요약 서비스 응답 형식이 올바르지 않습니다.");
            }

            var summary = summaryElement.GetString();
            if (string.IsNullOrEmpty(summary))
            {
                throw new AiSummaryException("요약 서비스 응답 형식이 올바르지 않습니다.");
            }

            return summary.Trim();
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            throw new AiSummaryException("요약 서비스 요청 시간 초과", ex);
        }
        catch (HttpRequestException ex)
        {
            throw new AiSummaryException($"요약 서비스 요청 실패: {ex.Message}", ex);
        }
        catch (JsonException ex)
        {
            throw new AiSummaryException("요약 서비스 응답을 JSON으로 파싱할 수 없습니다.", ex);
        }
    }
}

