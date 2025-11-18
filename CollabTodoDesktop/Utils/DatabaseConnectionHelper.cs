using System;
using System.Threading.Tasks;
using MySqlConnector;
using CollabTodoDesktop.Configuration;

namespace CollabTodoDesktop.Utils;

/// <summary>
/// 데이터베이스 연결 헬퍼 클래스
/// Python 버전의 db_connection context manager와 유사한 기능 제공
/// </summary>
public static class DatabaseConnectionHelper
{
    /// <summary>
    /// 동기 방식으로 데이터베이스 연결을 생성합니다.
    /// </summary>
    public static MySqlConnection CreateConnection(DatabaseConfig config)
    {
        if (config == null)
            throw new ArgumentNullException(nameof(config));

        if (!config.IsValid())
            throw new DatabaseConnectionException("데이터베이스 설정이 유효하지 않습니다.");

        var connectionString = BuildConnectionString(config);
        var connection = new MySqlConnection(connectionString);
        return connection;
    }

    /// <summary>
    /// 비동기 방식으로 데이터베이스 연결을 생성하고 엽니다.
    /// </summary>
    public static async Task<MySqlConnection> CreateConnectionAsync(DatabaseConfig config)
    {
        if (config == null)
            throw new ArgumentNullException(nameof(config));

        if (!config.IsValid())
            throw new DatabaseConnectionException("데이터베이스 설정이 유효하지 않습니다.");

        var connectionString = BuildConnectionString(config);
        var connection = new MySqlConnection(connectionString);
        
        try
        {
            await connection.OpenAsync();
            return connection;
        }
        catch (Exception ex)
        {
            connection.Dispose();
            throw new DatabaseConnectionException($"데이터베이스 연결 실패: {ex.Message}", ex);
        }
    }

    private static string BuildConnectionString(DatabaseConfig config)
    {
        var builder = new MySqlConnectionStringBuilder
        {
            Server = config.Host,
            Port = (uint)config.Port,
            UserID = config.User,
            Password = config.Password,
            Database = config.Database,
            SslMode = config.UseSsl ? MySqlSslMode.Required : MySqlSslMode.None
        };

        return builder.ConnectionString;
    }
}

