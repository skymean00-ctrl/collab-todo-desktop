using System;

namespace CollabTodoDesktop.Utils;

/// <summary>
/// 데이터베이스 연결 관련 예외
/// </summary>
public class DatabaseConnectionException : Exception
{
    public DatabaseConnectionException(string message) : base(message)
    {
    }

    public DatabaseConnectionException(string message, Exception innerException) 
        : base(message, innerException)
    {
    }
}

