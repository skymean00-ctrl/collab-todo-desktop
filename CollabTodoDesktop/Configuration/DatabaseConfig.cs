namespace CollabTodoDesktop.Configuration;

/// <summary>
/// 데이터베이스 연결에 필요한 설정 값
/// Python 버전의 DatabaseConfig dataclass와 동일한 구조
/// </summary>
public class DatabaseConfig
{
    public string Host { get; set; } = string.Empty;
    public int Port { get; set; } = 3306;
    public string User { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string Database { get; set; } = string.Empty;
    public bool UseSsl { get; set; } = false;

    /// <summary>
    /// 필수 설정 값이 모두 있는지 확인
    /// </summary>
    public bool IsValid()
    {
        return !string.IsNullOrWhiteSpace(Host) &&
               Port > 0 && Port <= 65535 &&
               !string.IsNullOrWhiteSpace(User) &&
               !string.IsNullOrWhiteSpace(Password) &&
               !string.IsNullOrWhiteSpace(Database);
    }
}

