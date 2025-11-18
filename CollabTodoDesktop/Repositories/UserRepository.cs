using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using MySqlConnector;
using CollabTodoDesktop.Models;
using CollabTodoDesktop.Configuration;
using CollabTodoDesktop.Utils;

namespace CollabTodoDesktop.Repositories;

/// <summary>
/// 사용자 데이터 접근 구현
/// Python 버전의 get_user_by_id, list_active_users와 동일한 기능
/// </summary>
public class UserRepository : IUserRepository
{
    private readonly DatabaseConfig _config;

    public UserRepository(DatabaseConfig config)
    {
        _config = config ?? throw new ArgumentNullException(nameof(config));
    }

    public async Task<User?> GetUserByIdAsync(int userId)
    {
        if (userId <= 0)
            return null;

        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        command.CommandText = @"
            SELECT id, username, display_name, email, role, is_active, created_at, updated_at
              FROM users
             WHERE id = @userId
        ";
        command.Parameters.AddWithValue("@userId", userId);

        using var reader = await command.ExecuteReaderAsync();
        if (!await reader.ReadAsync())
            return null;

        return RowToUser(reader);
    }

    public async Task<List<User>> ListActiveUsersAsync()
    {
        using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(_config);
        
        using var command = conn.CreateCommand();
        command.CommandText = @"
            SELECT id, username, display_name, email, role, is_active, created_at, updated_at
              FROM users
             WHERE is_active = 1
             ORDER BY display_name ASC
        ";

        var users = new List<User>();
        using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            users.Add(RowToUser(reader));
        }

        return users;
    }

    private static User RowToUser(MySqlDataReader reader)
    {
        // role 문자열을 UserRole enum으로 변환
        var roleStr = reader.GetString("role").ToLowerInvariant();
        var role = roleStr switch
        {
            "user" => UserRole.User,
            "admin" => UserRole.Admin,
            "supervisor" => UserRole.Supervisor,
            _ => UserRole.User
        };

        return new User
        {
            Id = reader.GetInt32("id"),
            Username = reader.GetString("username"),
            DisplayName = reader.GetString("display_name"),
            Email = reader.GetString("email"),
            Role = role,
            IsActive = reader.GetBoolean("is_active"),
            CreatedAt = reader.GetDateTime("created_at"),
            UpdatedAt = reader.GetDateTime("updated_at")
        };
    }
}

