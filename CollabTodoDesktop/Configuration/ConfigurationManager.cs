using System;
using System.Linq;
using Microsoft.Extensions.Configuration;

namespace CollabTodoDesktop.Configuration;

/// <summary>
/// 애플리케이션 설정 관리자
/// appsettings.json과 환경 변수에서 설정을 로드합니다.
/// 환경 변수가 appsettings.json을 덮어씁니다.
/// </summary>
public class ConfigurationManager
{
    private readonly IConfiguration _configuration;

    public ConfigurationManager(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    /// <summary>
    /// 데이터베이스 설정을 로드합니다.
    /// appsettings.json의 Database 섹션과 환경 변수 COLLAB_TODO_DB_*를 읽습니다.
    /// </summary>
    public DatabaseConfig? LoadDatabaseConfig()
    {
        var config = new DatabaseConfig();

        // appsettings.json에서 로드
        var dbSection = _configuration.GetSection("Database");
        config.Host = dbSection["Host"] ?? string.Empty;
        config.Port = int.TryParse(dbSection["Port"], out var port) ? port : 3306;
        config.User = dbSection["User"] ?? string.Empty;
        config.Password = dbSection["Password"] ?? string.Empty;
        config.Database = dbSection["Database"] ?? string.Empty;
        config.UseSsl = bool.TryParse(dbSection["UseSsl"], out var useSsl) && useSsl;

        // 환경 변수로 덮어쓰기 (Python 버전과 동일한 네이밍)
        var envHost = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_HOST");
        if (!string.IsNullOrWhiteSpace(envHost))
            config.Host = envHost.Trim();

        var envPort = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_PORT");
        if (!string.IsNullOrWhiteSpace(envPort) && int.TryParse(envPort.Trim(), out var envPortValue))
            config.Port = envPortValue;

        var envUser = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_USER");
        if (!string.IsNullOrWhiteSpace(envUser))
            config.User = envUser.Trim();

        var envPassword = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_PASSWORD");
        if (!string.IsNullOrWhiteSpace(envPassword))
            config.Password = envPassword.Trim();

        var envDatabase = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_NAME");
        if (!string.IsNullOrWhiteSpace(envDatabase))
            config.Database = envDatabase.Trim();

        var envUseSsl = Environment.GetEnvironmentVariable("COLLAB_TODO_DB_USE_SSL");
        if (!string.IsNullOrWhiteSpace(envUseSsl))
        {
            var sslValue = envUseSsl.Trim().ToLowerInvariant();
            config.UseSsl = sslValue == "1" || sslValue == "true" || sslValue == "yes" || sslValue == "on";
        }

        // 필수 값이 모두 있는지 확인
        if (!config.IsValid())
            return null;

        return config;
    }

    /// <summary>
    /// AI 서비스 설정을 로드합니다.
    /// appsettings.json의 AiService 섹션과 환경 변수 COLLAB_TODO_AI_*를 읽습니다.
    /// </summary>
    public AiServiceConfig? LoadAiServiceConfig()
    {
        var config = new AiServiceConfig();

        // appsettings.json에서 로드
        var aiSection = _configuration.GetSection("AiService");
        config.BaseUrl = aiSection["BaseUrl"] ?? string.Empty;
        config.ApiKey = aiSection["ApiKey"];
        config.TimeoutSeconds = int.TryParse(aiSection["TimeoutSeconds"], out var timeout) && timeout > 0
            ? timeout
            : 15;

        // 환경 변수로 덮어쓰기 (Python 버전과 동일한 네이밍)
        var envBaseUrl = Environment.GetEnvironmentVariable("COLLAB_TODO_AI_BASE_URL");
        if (!string.IsNullOrWhiteSpace(envBaseUrl))
            config.BaseUrl = envBaseUrl.Trim();

        var envApiKey = Environment.GetEnvironmentVariable("COLLAB_TODO_AI_API_KEY");
        if (!string.IsNullOrWhiteSpace(envApiKey))
            config.ApiKey = envApiKey.Trim();

        var envTimeout = Environment.GetEnvironmentVariable("COLLAB_TODO_AI_TIMEOUT_SECONDS");
        if (!string.IsNullOrWhiteSpace(envTimeout) && int.TryParse(envTimeout.Trim(), out var envTimeoutValue) && envTimeoutValue > 0)
            config.TimeoutSeconds = envTimeoutValue;

        // 필수 값이 있는지 확인
        if (!config.IsValid())
            return null;

        return config;
    }
}

