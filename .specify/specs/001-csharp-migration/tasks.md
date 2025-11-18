# Tasks: C# / .NET Migration

**Input**: Design documents from `/specs/001-csharp-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included to ensure quality and feature parity with Python version.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 0: Project Setup and Infrastructure

**Purpose**: Create .NET project structure and configure build system

- [ ] T001 Create .NET 8.0 WPF project structure in `CollabTodoDesktop/`
- [ ] T002 [P] Configure CollabTodoDesktop.csproj for self-contained deployment
- [ ] T003 [P] Add NuGet packages to CollabTodoDesktop.csproj:
  - MySqlConnector
  - Microsoft.Extensions.Configuration
  - Microsoft.Extensions.Configuration.Json
  - Microsoft.Extensions.Configuration.EnvironmentVariables
  - Microsoft.Extensions.Logging
  - System.Net.Http.Json
- [ ] T004 [P] Create project folder structure:
  - Models/
  - Repositories/
  - Services/
  - ViewModels/
  - Views/
  - Configuration/
  - Utils/
- [ ] T005 Create appsettings.json template in project root
- [ ] T006 Create appsettings.Development.json template
- [ ] T007 [P] Create build script build.bat for single-file deployment
- [ ] T008 Verify `dotnet publish` creates single .exe file

**Checkpoint**: Project compiles and can be published as single .exe

---

## Phase 1: Domain Models and Configuration

**Purpose**: Port domain models and configuration management from Python

### Tests for Phase 1

- [ ] T009 [P] [US1] Unit test for User model in Tests/Models/UserTests.cs
- [ ] T010 [P] [US1] Unit test for Task model in Tests/Models/TaskTests.cs
- [ ] T011 [P] [US1] Unit test for configuration loading in Tests/Configuration/ConfigurationManagerTests.cs

### Implementation for Phase 1

- [ ] T012 [P] [US1] Create User.cs record in Models/User.cs (match Python User dataclass)
- [ ] T013 [P] [US1] Create Project.cs record in Models/Project.cs
- [ ] T014 [P] [US1] Create Task.cs record in Models/Task.cs
- [ ] T015 [P] [US1] Create TaskHistory.cs record in Models/TaskHistory.cs
- [ ] T016 [P] [US1] Create Notification.cs record in Models/Notification.cs
- [ ] T017 [P] [US1] Create UserRole enum in Models/UserRole.cs
- [ ] T018 [P] [US1] Create TaskStatus enum in Models/TaskStatus.cs
- [ ] T019 [US1] Create DatabaseConfig class in Configuration/DatabaseConfig.cs
- [ ] T020 [US1] Create AiServiceConfig class in Configuration/AiServiceConfig.cs
- [ ] T021 [US1] Create ConfigurationManager class in Configuration/ConfigurationManager.cs
  - Load from appsettings.json
  - Override with environment variables
  - Validate configuration
- [ ] T022 [US1] Implement configuration validation in ConfigurationManager

**Checkpoint**: All models created and configuration loading works

---

## Phase 2: Data Access Layer (Repositories)

**Purpose**: Port repository layer for database operations

### Tests for Phase 2

- [ ] T023 [P] [US2] Integration test for UserRepository in Tests/Repositories/UserRepositoryTests.cs
- [ ] T024 [P] [US2] Integration test for TaskRepository in Tests/Repositories/TaskRepositoryTests.cs
- [ ] T025 [P] [US2] Integration test for NotificationRepository in Tests/Repositories/NotificationRepositoryTests.cs

### Implementation for Phase 2

- [ ] T026 [US2] Create IUserRepository interface in Repositories/IUserRepository.cs
- [ ] T027 [US2] Create UserRepository class in Repositories/UserRepository.cs
  - GetUserByIdAsync method
  - ListActiveUsersAsync method
- [ ] T028 [US2] Create ITaskRepository interface in Repositories/ITaskRepository.cs
- [ ] T029 [US2] Create TaskRepository class in Repositories/TaskRepository.cs
  - ListTasksForAssigneeAsync (with lastSyncedAt parameter for incremental sync)
  - ListTasksCreatedByUserAsync
  - CreateTaskAsync
  - UpdateTaskStatusAsync
  - CompleteTaskAndMoveToNextAsync
- [ ] T030 [US2] Create INotificationRepository interface in Repositories/INotificationRepository.cs
- [ ] T031 [US2] Create NotificationRepository class in Repositories/NotificationRepository.cs
  - ListUnreadNotificationsAsync
  - MarkNotificationsAsReadAsync
- [ ] T032 [US2] Create DatabaseConnectionHelper class in Utils/DatabaseConnectionHelper.cs
  - CreateConnection method (async)
  - CreateConnectionAsync method
  - Dispose pattern (IDisposable)
- [ ] T033 [US2] Create DatabaseConnectionException class in Utils/DatabaseConnectionException.cs
- [ ] T034 [US2] Implement error handling in all repository methods

**Checkpoint**: All repository methods work with test database

---

## Phase 3: Business Logic Layer

**Purpose**: Port business logic (sync, dashboard calculations)

### Tests for Phase 3

- [ ] T035 [P] [US2] Unit test for DashboardService in Tests/Services/DashboardServiceTests.cs
- [ ] T036 [P] [US2] Unit test for SyncService in Tests/Services/SyncServiceTests.cs
- [ ] T037 [P] [US2] Integration test for SyncService in Tests/Services/SyncServiceIntegrationTests.cs

### Implementation for Phase 3

- [ ] T038 [US2] Create SyncState record in Services/SyncState.cs
- [ ] T039 [US2] Create SyncResult record in Services/SyncResult.cs
- [ ] T040 [US2] Create ISyncService interface in Services/ISyncService.cs
- [ ] T041 [US2] Create SyncService class in Services/SyncService.cs
  - PerformSyncAsync method (port from Python perform_sync)
  - Support incremental sync (lastSyncedAt parameter)
- [ ] T042 [US2] Create TaskSummary record in Services/TaskSummary.cs
- [ ] T043 [US2] Create IDashboardService interface in Services/IDashboardService.cs
- [ ] T044 [US2] Create DashboardService class in Services/DashboardService.cs
  - SummarizeTasksAsync method (port from Python summarize_tasks)
- [ ] T045 [US2] Create AiSummaryException class in Services/AiSummaryException.cs
- [ ] T046 [US2] Create IAiClientService interface in Services/IAiClientService.cs
- [ ] T047 [US2] Create AiClientService class in Services/AiClientService.cs
  - SummarizeTextAsync method (port from Python summarize_text)
  - Use HttpClient for API calls
  - Handle errors gracefully

**Checkpoint**: All business logic services working and tested

---

## Phase 4: User Interface (WPF) - User Story 1

**Purpose**: Port UI from PyQt5 to WPF - Simplified Installation

### Tests for Phase 4 (US1)

- [ ] T048 [P] [US1] UI test: Verify single .exe runs without Python in Tests/UI/DeploymentTests.cs

### Implementation for Phase 4 (US1)

- [ ] T049 [US1] Create MainWindow.xaml in Views/MainWindow.xaml
  - Window layout matching Python version
  - Status bar with connection status label
  - Status bar with last sync time label
- [ ] T050 [US1] Create MainWindow.xaml.cs code-behind
- [ ] T051 [US1] Create MainWindowViewModel class in ViewModels/MainWindowViewModel.cs
  - Properties: ConnectionStatus, LastSyncTime, CurrentUserId
  - Commands: SyncCommand, AiTestCommand
  - INotifyPropertyChanged implementation
- [ ] T052 [US1] Implement data binding in MainWindow.xaml
  - Bind status bar labels to ViewModel properties
- [ ] T053 [US1] Configure App.xaml for WPF application
- [ ] T054 [US1] Test single .exe deployment
  - Build self-contained .exe
  - Test on clean Windows machine (no .NET runtime)
  - Verify application starts

**Checkpoint**: Single .exe file runs without any additional installation

---

## Phase 5: User Interface (WPF) - User Story 2

**Purpose**: Port UI - Feature Parity

### Tests for Phase 5 (US2)

- [ ] T055 [P] [US2] UI test: User selection dialog in Tests/UI/UserSelectionDialogTests.cs
- [ ] T056 [P] [US2] UI test: Dashboard updates in Tests/UI/DashboardTests.cs
- [ ] T057 [P] [US2] UI test: Periodic sync in Tests/UI/SyncTests.cs

### Implementation for Phase 5 (US2)

- [ ] T058 [US2] Create UserSelectionDialog.xaml in Views/UserSelectionDialog.xaml
  - ComboBox for user selection
  - OK/Cancel buttons
  - Match Python version layout
- [ ] T059 [US2] Create UserSelectionDialog.xaml.cs code-behind
- [ ] T060 [US2] Create UserSelectionViewModel class in ViewModels/UserSelectionViewModel.cs
  - Users collection
  - SelectedUser property
  - OK/Cancel commands
- [ ] T061 [US2] Implement user selection logic in MainWindowViewModel
  - Load active users on startup
  - Show dialog
  - Store selected user ID
- [ ] T062 [US2] Create DashboardWidget.xaml UserControl in Views/DashboardWidget.xaml
  - ListView or ListBox for task summary
  - Display task counts by status
- [ ] T063 [US2] Create DashboardWidget.xaml.cs code-behind
- [ ] T064 [US2] Create DashboardViewModel class in ViewModels/DashboardViewModel.cs
  - TaskSummary property
  - UpdateDashboard method
- [ ] T065 [US2] Implement periodic sync timer in MainWindowViewModel
  - Use DispatcherTimer (5-second interval)
  - Call SyncService.PerformSyncAsync
  - Update dashboard on sync
  - Update status bar
- [ ] T066 [US2] Implement error dialogs
  - Use MessageBox.Show with Korean messages
  - Handle DatabaseConnectionException
  - Handle AiSummaryException
  - Handle general exceptions
- [ ] T067 [US2] Implement AI summary test feature
  - Menu item "도구" → "AI 요약 테스트"
  - Call AiClientService.SummarizeTextAsync
  - Display result in MessageBox
- [ ] T068 [US2] Implement menu bar in MainWindow.xaml
  - "도구" menu
  - "AI 요약 테스트" menu item

**Checkpoint**: All UI features match Python version functionality

---

## Phase 6: Build and Deployment

**Purpose**: Configure self-contained deployment

- [ ] T069 Configure CollabTodoDesktop.csproj for optimal single-file deployment
  - Set PublishSingleFile to true
  - Set IncludeNativeLibrariesForSelfExtract to true
  - Set RuntimeIdentifier to win-x64
- [ ] T070 Create build.bat script
  - Single command: `dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true`
- [ ] T071 Test deployment on clean Windows machine
  - No .NET runtime installed
  - Verify single .exe runs
  - Verify all features work
- [ ] T072 Measure and document file size
  - Target: 50-80MB
  - Compare with Python version
- [ ] T073 Optional: Create simplified Inno Setup installer
  - Much simpler than Python version (just one .exe file)
  - installer.iss for C# version

**Checkpoint**: Single .exe file works on clean Windows machine

---

## Phase 7: Testing and Validation

**Purpose**: Ensure feature parity and quality

- [ ] T074 [P] Run all unit tests and verify they pass
- [ ] T075 [P] Run all integration tests and verify they pass
- [ ] T076 Feature parity testing
  - Side-by-side comparison with Python version
  - Verify all features work identically
- [ ] T077 Performance testing
  - Measure startup time (target: < 2 seconds)
  - Measure memory usage
  - Compare with Python version
- [ ] T078 Error handling testing
  - Database connection failures
  - Invalid configuration
  - AI service failures
- [ ] T079 Configuration testing
  - appsettings.json loading
  - Environment variable override
  - Invalid configuration handling

**Checkpoint**: All tests pass, feature parity verified

---

## Phase 8: Documentation and Polish

**Purpose**: Final documentation and cleanup

- [ ] T080 [P] Update README.md with C# / .NET build instructions
- [ ] T081 [P] Create C# migration guide in docs/MIGRATION_GUIDE.md
- [ ] T082 [P] Update deployment documentation
- [ ] T083 Code cleanup and refactoring
- [ ] T084 Add XML documentation comments to public APIs
- [ ] T085 Verify Korean comments for business logic
- [ ] T086 Create quick start guide for C# version

**Checkpoint**: Documentation complete, code polished

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately
- **Phase 1 (Models/Config)**: Depends on Phase 0 - BLOCKS all other phases
- **Phase 2 (Repositories)**: Depends on Phase 1
- **Phase 3 (Business Logic)**: Depends on Phase 2
- **Phase 4 (UI - US1)**: Depends on Phase 3
- **Phase 5 (UI - US2)**: Depends on Phase 4
- **Phase 6 (Deployment)**: Depends on Phase 5
- **Phase 7 (Testing)**: Depends on Phase 6
- **Phase 8 (Documentation)**: Depends on Phase 7

### Parallel Opportunities

- **Phase 0**: T002, T003, T004, T007 can run in parallel
- **Phase 1**: T012-T018 (all models) can run in parallel
- **Phase 2**: T023-T025 (all repository tests) can run in parallel
- **Phase 3**: T035-T037 (all service tests) can run in parallel
- **Phase 5**: T055-T057 (all UI tests) can run in parallel

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Models before repositories
- Repositories before services
- Services before UI
- Core implementation before integration

---

## Implementation Strategy

### MVP First (Simplified Installation Only)

1. Complete Phase 0: Setup
2. Complete Phase 1: Models/Config
3. Complete Phase 2: Repositories
4. Complete Phase 3: Business Logic
5. Complete Phase 4: Basic UI (US1 - single .exe deployment)
6. **STOP and VALIDATE**: Test single .exe on clean machine
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Phases 0-3 → Foundation ready
2. Add Phase 4 (US1) → Test single .exe → Deploy/Demo (MVP!)
3. Add Phase 5 (US2) → Test feature parity → Deploy/Demo
4. Add Phase 6 (Deployment) → Test deployment → Deploy
5. Add Phase 7 (Testing) → Validate quality
6. Add Phase 8 (Documentation) → Complete migration

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each phase should be independently completable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently

