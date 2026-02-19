using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace CollabTodoDesktop.Services;

/// <summary>
/// collab-todo REST API 클라이언트.
/// MySQL 직접 연결 대신 HTTP로 서버와 통신합니다.
/// </summary>
public class ApiClient
{
    private readonly HttpClient _http;
    private string? _accessToken;
    public int? CurrentUserId { get; private set; }
    public string? CurrentDisplayName { get; private set; }

    private static readonly JsonSerializerOptions _json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public ApiClient(string baseUrl)
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/") };
    }

    // ── 인증 ─────────────────────────────────────────────────

    public async Task<bool> LoginAsync(string username, string password)
    {
        var body = new { username, password };
        var resp = await _http.PostAsJsonAsync("auth/login", body, _json);
        if (!resp.IsSuccessStatusCode)
            return false;

        var result = await resp.Content.ReadFromJsonAsync<LoginResponse>(_json);
        if (result == null) return false;

        _accessToken = result.AccessToken;
        CurrentUserId = result.UserId;
        CurrentDisplayName = result.DisplayName;
        _http.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _accessToken);
        return true;
    }

    public void Logout()
    {
        _accessToken = null;
        CurrentUserId = null;
        CurrentDisplayName = null;
        _http.DefaultRequestHeaders.Authorization = null;
    }

    public bool IsLoggedIn => _accessToken != null;

    // ── 동기화 ────────────────────────────────────────────────

    public async Task<SyncResponse?> SyncAsync(DateTime? lastSyncedAt = null)
    {
        var url = lastSyncedAt.HasValue
            ? $"api/sync?last_synced_at={Uri.EscapeDataString(lastSyncedAt.Value.ToString("O"))}"
            : "api/sync";

        var resp = await _http.GetAsync(url);
        if (resp.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new UnauthorizedAccessException();
        resp.EnsureSuccessStatusCode();

        return await resp.Content.ReadFromJsonAsync<SyncResponse>(_json);
    }

    // ── Task 액션 ─────────────────────────────────────────────

    public async Task UpdateTaskStatusAsync(int taskId, string newStatus)
    {
        var body = new { new_status = newStatus };
        var resp = await _http.PatchAsJsonAsync($"api/tasks/{taskId}/status", body, _json);
        resp.EnsureSuccessStatusCode();
    }

    public async Task CompleteTaskAsync(int taskId)
    {
        var resp = await _http.PostAsync($"api/tasks/{taskId}/complete", null);
        resp.EnsureSuccessStatusCode();
    }

    // ── 사용자 목록 ───────────────────────────────────────────

    public async Task<List<UserOut>?> GetUsersAsync()
    {
        var resp = await _http.GetAsync("api/users/");
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<List<UserOut>>(_json);
    }

    // ── 응답 DTO ─────────────────────────────────────────────

    public record LoginResponse(string AccessToken, int UserId, string DisplayName);

    public record SyncResponse(
        DateTime ServerTime,
        List<TaskOut> Tasks,
        List<NotificationOut> Notifications);

    public record TaskOut(
        int Id, int ProjectId, string Title, string? Description,
        int AuthorId, int CurrentAssigneeId, int? NextAssigneeId,
        string Status, DateTime? DueDate, DateTime? CompletedAt,
        DateTime CreatedAt, DateTime UpdatedAt);

    public record NotificationOut(
        int Id, int? TaskId, string NotificationType,
        string Message, bool IsRead, DateTime CreatedAt);

    public record UserOut(int Id, string Username, string DisplayName, string Email, string Role);
}
