using System;
using Microsoft.Extensions.Configuration;

namespace CollabTodoDesktop.Configuration;

/// <summary>
/// AI 서비스 설정 관리자
/// </summary>
public class ConfigurationManager
{
    private readonly IConfiguration _configuration;

    public ConfigurationManager(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public AiServiceConfig? LoadAiServiceConfig()
    {
        var config = new AiServiceConfig();

        var aiSection = _configuration.GetSection("AiService");
        config.BaseUrl = aiSection["BaseUrl"] ?? string.Empty;
        config.ApiKey = aiSection["ApiKey"];
        config.TimeoutSeconds = int.TryParse(aiSection["TimeoutSeconds"], out var timeout) && timeout > 0
            ? timeout : 15;

        var envBaseUrl = Environment.GetEnvironmentVariable("COLLAB_TODO_AI_BASE_URL");
        if (!string.IsNullOrWhiteSpace(envBaseUrl))
            config.BaseUrl = envBaseUrl.Trim();

        var envApiKey = Environment.GetEnvironmentVariable("COLLAB_TODO_AI_API_KEY");
        if (!string.IsNullOrWhiteSpace(envApiKey))
            config.ApiKey = envApiKey.Trim();

        if (!config.IsValid())
            return null;

        return config;
    }
}
