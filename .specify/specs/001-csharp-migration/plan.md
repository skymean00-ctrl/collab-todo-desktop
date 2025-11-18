# Implementation Plan: C# / .NET Migration

**Feature**: 001-csharp-migration  
**Created**: 2025-01-XX  
**Status**: Draft  
**Based on**: spec.md

## Overview

This plan outlines the migration of Collab Todo Desktop from Python/PyQt5 to C# / .NET. The goal is to create a simpler deployment process with a single .exe file that doesn't require Python installation.

## Technology Stack Decisions

### Core Stack
- **Language**: C# 12 (.NET 8.0)
- **UI Framework**: WPF (Windows Presentation Foundation)
  - **Rationale**: Mature, well-documented, easier migration from PyQt5
  - **Alternative Considered**: WinUI 3 (more modern but steeper learning curve)
- **Database**: MySqlConnector
  - **Rationale**: Modern, actively maintained, excellent async support
  - **NuGet Package**: `MySqlConnector` (latest version)
- **HTTP Client**: `HttpClient` (built-in) or `RestSharp`
  - **For**: AI service API calls
- **Configuration**: `Microsoft.Extensions.Configuration`
  - **For**: appsettings.json and environment variable support
- **Logging**: `Microsoft.Extensions.Logging`
  - **For**: Application logging

### Project Structure

```
CollabTodoDesktop/
├── CollabTodoDesktop.csproj          # Main WPF application
├── App.xaml / App.xaml.cs            # Application entry point
├── MainWindow.xaml / MainWindow.xaml.cs  # Main window
├── Models/                           # Domain models
│   ├── User.cs
│   ├── Project.cs
│   ├── Task.cs
│   ├── TaskHistory.cs
│   └── Notification.cs
├── Repositories/                     # Data access layer
│   ├── IUserRepository.cs
│   ├── UserRepository.cs
│   ├── ITaskRepository.cs
│   └── TaskRepository.cs
├── Services/                         # Business logic
│   ├── ISyncService.cs
│   ├── SyncService.cs
│   ├── IDashboardService.cs
│   └── DashboardService.cs
├── ViewModels/                       # MVVM ViewModels
│   ├── MainWindowViewModel.cs
│   └── UserSelectionViewModel.cs
├── Views/                            # User controls
│   ├── UserSelectionDialog.xaml
│   └── DashboardWidget.xaml
├── Configuration/                    # Configuration management
│   ├── DatabaseConfig.cs
│   └── AiServiceConfig.cs
├── Utils/                            # Utilities
│   └── DatabaseConnectionHelper.cs
├── appsettings.json                  # Configuration file
└── appsettings.Development.json      # Development overrides
```

## Implementation Phases

### Phase 0: Project Setup and Infrastructure

**Goal**: Create .NET project structure and configure build system

**Tasks**:
1. Create new .NET 8.0 WPF project
2. Configure project for self-contained deployment
3. Add NuGet packages:
   - MySqlConnector
   - Microsoft.Extensions.Configuration
   - Microsoft.Extensions.Configuration.Json
   - Microsoft.Extensions.Configuration.EnvironmentVariables
   - Microsoft.Extensions.Logging
   - System.Net.Http.Json (for AI service)
4. Set up project structure (folders)
5. Configure appsettings.json template

**Deliverables**:
- Working .NET WPF project that compiles
- Project configured for single-file deployment
- appsettings.json template

**Validation**:
- `dotnet build` succeeds
- `dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true` creates single .exe

---

### Phase 1: Domain Models and Configuration

**Goal**: Port domain models and configuration management from Python

**Tasks**:
1. Create C# domain models (User, Project, Task, TaskHistory, Notification)
   - Use C# records for immutability (similar to Python dataclasses)
   - Match Python model structure exactly
2. Implement DatabaseConfig class
3. Implement AiServiceConfig class
4. Create ConfigurationManager to load from appsettings.json and environment variables
5. Implement configuration validation

**Deliverables**:
- All domain models in C#
- Configuration loading working
- Unit tests for configuration

**Validation**:
- Models match Python version structure
- Configuration loads from appsettings.json
- Environment variables override appsettings.json
- Invalid configuration shows user-friendly error

---

### Phase 2: Data Access Layer (Repositories)

**Goal**: Port repository layer for database operations

**Tasks**:
1. Create repository interfaces (IUserRepository, ITaskRepository, etc.)
2. Implement UserRepository
   - get_user_by_id
   - list_active_users
3. Implement TaskRepository
   - list_tasks_for_assignee (with incremental sync support)
   - list_tasks_created_by_user
   - create_task
   - update_task_status
   - complete_task_and_move_to_next
4. Implement NotificationRepository
   - list_unread_notifications
   - mark_notifications_as_read
5. Implement database connection helper (similar to Python's db_connection context manager)
6. Add error handling (DatabaseConnectionException)

**Deliverables**:
- All repository methods ported
- Database connection management working
- Integration tests for repositories

**Validation**:
- All repository methods work with test database
- Connection errors handled gracefully
- Incremental sync works (last_synced_at parameter)

---

### Phase 3: Business Logic Layer

**Goal**: Port business logic (sync, dashboard calculations)

**Tasks**:
1. Create SyncService
   - Port perform_sync function
   - Implement SyncState and SyncResult classes
   - Support incremental sync
2. Create DashboardService
   - Port summarize_tasks function
   - Implement TaskSummary class
3. Create AiClientService
   - Port summarize_text function
   - Use HttpClient for API calls
   - Handle errors (AiSummaryException)

**Deliverables**:
- All business logic services working
- Unit tests for pure business logic
- Integration tests for sync service

**Validation**:
- Sync service works with real database
- Dashboard calculations match Python version
- AI client handles errors gracefully

---

### Phase 4: User Interface (WPF)

**Goal**: Port UI from PyQt5 to WPF

**Tasks**:
1. Create MainWindow.xaml
   - Port window layout from PyQt5
   - Status bar with connection status and last sync time
   - Menu bar with "도구" menu
2. Create UserSelectionDialog
   - Port user selection dialog
   - ComboBox for user selection
   - OK/Cancel buttons
3. Create DashboardWidget (UserControl)
   - Port dashboard dock widget
   - ListView or ListBox for task summary
   - Display task counts by status
4. Implement MainWindowViewModel (MVVM pattern)
   - Properties for connection status, sync state
   - Commands for sync, AI test
   - Data binding to UI
5. Implement periodic sync timer (DispatcherTimer)
   - 5-second interval (same as Python version)
   - Update dashboard on sync
6. Implement error dialogs
   - Korean error messages
   - User-friendly error display

**Deliverables**:
- Complete WPF UI matching Python version
- MVVM pattern implemented
- All UI interactions working

**Validation**:
- UI looks and behaves like Python version
- User selection dialog works
- Dashboard updates every 5 seconds
- Error messages display correctly

---

### Phase 5: Build and Deployment

**Goal**: Configure self-contained deployment

**Tasks**:
1. Configure .csproj for self-contained deployment
   - Set RuntimeIdentifier to win-x64
   - Enable PublishSingleFile
   - Enable IncludeNativeLibrariesForSelfExtract
2. Create build script (build.bat)
   - Single command: `dotnet publish`
3. Test deployment on clean Windows machine
   - No .NET runtime installed
   - Verify single .exe runs
4. Optional: Create Inno Setup installer (if needed)
   - Much simpler than Python version (just one .exe file)

**Deliverables**:
- Single .exe file (50-80MB)
- Build script
- Deployment tested on clean machine

**Validation**:
- Single .exe runs on Windows 10+ without .NET runtime
- File size is 50-80MB
- All features work in deployed version

---

### Phase 6: Testing and Validation

**Goal**: Ensure feature parity and quality

**Tasks**:
1. Unit tests for all business logic
2. Integration tests for repositories
3. Feature parity testing (compare with Python version)
4. Performance testing (startup time, memory usage)
5. Error handling testing
6. Configuration testing (appsettings.json, environment variables)

**Deliverables**:
- Test suite with good coverage
- Feature parity verified
- Performance metrics documented

**Validation**:
- All tests pass
- Feature parity 100% with Python version
- Startup time under 2 seconds
- Memory usage reasonable

## Technical Implementation Details

### Database Connection Pattern

**Python version**:
```python
with db_connection(config) as conn:
    # use conn
```

**C# version**:
```csharp
using var conn = DatabaseConnectionHelper.CreateConnection(config);
// use conn
// automatically disposed
```

### Configuration Pattern

**Python version**: Environment variables only

**C# version**: appsettings.json + environment variables
```json
{
  "Database": {
    "Host": "192.168.1.100",
    "Port": 3306,
    "User": "username",
    "Password": "password",
    "Database": "collab_todo",
    "UseSsl": false
  },
  "AiService": {
    "BaseUrl": "https://api.example.com",
    "ApiKey": "optional",
    "TimeoutSeconds": 15
  }
}
```

Environment variables override (same naming as Python):
- `COLLAB_TODO_DB_HOST`
- `COLLAB_TODO_DB_PORT`
- etc.

### MVVM Pattern

Use MVVM for WPF:
- **Model**: Domain models (User, Task, etc.)
- **View**: XAML files (MainWindow.xaml, UserSelectionDialog.xaml)
- **ViewModel**: MainWindowViewModel, UserSelectionViewModel

Benefits:
- Separation of concerns
- Testability
- Data binding

### Async/Await Pattern

Use async/await for:
- Database operations
- HTTP requests (AI service)
- Background sync operations

**Example**:
```csharp
public async Task<SyncResult> PerformSyncAsync(int userId, SyncState state)
{
    using var conn = await DatabaseConnectionHelper.CreateConnectionAsync(config);
    // async database operations
}
```

## Migration Mapping

### Python → C# Equivalents

| Python | C# |
|--------|-----|
| `dataclass(frozen=True)` | `record` |
| `Optional[T]` | `T?` (nullable) |
| `List[T]` | `List<T>` or `IList<T>` |
| `Dict[str, T]` | `Dictionary<string, T>` |
| `@contextmanager` | `using` statement |
| `mysql.connector` | `MySqlConnector` |
| `PyQt5.QtWidgets` | `System.Windows` (WPF) |
| `QTimer` | `DispatcherTimer` |
| `QMessageBox` | `MessageBox.Show()` |
| `QDialog` | `Window` with `DialogResult` |

## Risk Mitigation

### Risk 1: UI Behavior Differences
- **Mitigation**: Careful testing, side-by-side comparison with Python version
- **Contingency**: Adjust WPF implementation to match Python behavior exactly

### Risk 2: Database Connection Issues
- **Mitigation**: Use well-tested MySqlConnector library
- **Contingency**: Test with various MySQL versions and configurations

### Risk 3: Performance Issues
- **Mitigation**: Profile application, optimize hot paths
- **Contingency**: Use async operations, optimize database queries

### Risk 4: Configuration Migration
- **Mitigation**: Support both appsettings.json and environment variables
- **Contingency**: Provide migration guide for existing users

## Success Metrics

- ✅ Single .exe file created (50-80MB)
- ✅ Runs on Windows 10+ without .NET runtime (self-contained)
- ✅ 100% feature parity with Python version
- ✅ Startup time < 2 seconds
- ✅ Build process: single `dotnet publish` command
- ✅ All tests passing

## Dependencies

### NuGet Packages
- `MySqlConnector` (latest)
- `Microsoft.Extensions.Configuration` (8.0+)
- `Microsoft.Extensions.Configuration.Json` (8.0+)
- `Microsoft.Extensions.Configuration.EnvironmentVariables` (8.0+)
- `Microsoft.Extensions.Logging` (8.0+)
- `System.Net.Http.Json` (for AI service)

### Development Tools
- .NET 8.0 SDK
- Visual Studio 2022 Community (free) or Visual Studio Code
- MySQL test database (for integration testing)

## Next Steps

1. Review and approve this plan
2. Create task breakdown (`/speckit.tasks`)
3. Begin implementation (`/speckit.implement`)

---

**Plan Status**: Ready for task breakdown

