# Feature Specification: C# / .NET Migration

**Feature Branch**: `001-csharp-migration`  
**Created**: 2025-01-XX  
**Status**: Draft  
**Input**: Migrate Collab Todo Desktop from Python/PyQt5 to C# / .NET for simpler deployment and installation

## User Scenarios & Testing

### User Story 1 - Simplified Installation Experience (Priority: P1)

End users can install and run the application without installing Python or any additional runtime dependencies.

**Why this priority**: Core value proposition - eliminates Python installation complexity for end users

**Independent Test**: Can be tested by distributing a single .exe file to a Windows machine without Python installed and verifying it runs successfully.

**Acceptance Scenarios**:

1. **Given** a Windows 10+ machine without Python installed, **When** user runs the single .exe file, **Then** the application starts successfully
2. **Given** the application is distributed as a single .exe file, **When** user double-clicks it, **Then** no additional installation steps are required
3. **Given** the application executable, **When** user runs it, **Then** all dependencies are included and no external runtime is needed

---

### User Story 2 - Feature Parity with Python Version (Priority: P1)

All existing features from the Python/PyQt5 version work identically in the C# / .NET version.

**Why this priority**: Critical - users should not lose any functionality during migration

**Independent Test**: Can be tested by running both versions side-by-side and comparing functionality.

**Acceptance Scenarios**:

1. **Given** the C# application, **When** user starts it, **Then** user selection dialog appears (same as Python version)
2. **Given** database connection is configured, **When** application syncs, **Then** tasks are displayed in dashboard (same as Python version)
3. **Given** user selects a user, **When** application runs, **Then** periodic sync works every 5 seconds (same as Python version)
4. **Given** AI service is configured, **When** user tests AI summary, **Then** AI summary feature works (same as Python version)

---

### User Story 3 - Improved Build and Deployment Process (Priority: P2)

Developers can build and deploy the application with a simpler process than the Python version.

**Why this priority**: Developer experience improvement - reduces build complexity

**Independent Test**: Can be tested by running a single build command and verifying a single .exe file is created.

**Acceptance Scenarios**:

1. **Given** .NET SDK is installed, **When** developer runs `dotnet publish`, **Then** a single .exe file is created in one step
2. **Given** the build output, **When** developer checks file size, **Then** it is smaller than Python version (50-80MB vs 100-200MB)
3. **Given** the build process, **When** developer builds, **Then** no PyInstaller or Inno Setup configuration is required for basic deployment

---

### User Story 4 - Configuration Management (Priority: P2)

Application configuration can be managed through appsettings.json, environment variables, or both.

**Why this priority**: Flexibility in configuration management for different deployment scenarios

**Independent Test**: Can be tested by modifying appsettings.json and verifying application reads the configuration.

**Acceptance Scenarios**:

1. **Given** appsettings.json file exists, **When** application starts, **Then** database connection settings are loaded from the file
2. **Given** environment variables are set, **When** application starts, **Then** environment variables override appsettings.json values
3. **Given** no configuration file exists, **When** application starts, **Then** user-friendly error message is displayed

---

### Edge Cases

- What happens when .NET runtime is not installed? (Self-contained deployment eliminates this)
- How does the application handle database connection failures? (Same as Python version - graceful error handling)
- What if MySQL connector library is missing? (Included in self-contained deployment)
- How does the application behave with invalid configuration? (Validation and error messages)

## Requirements

### Functional Requirements

- **FR-001**: Application MUST be built as a single .exe file using .NET self-contained deployment
- **FR-002**: Application MUST include all dependencies (no external runtime required)
- **FR-003**: Application MUST support all features from Python version:
  - User selection dialog
  - Periodic task synchronization (5-second interval)
  - Dashboard with task statistics
  - Database connection status display
  - AI summary test feature
  - Incremental sync support
- **FR-004**: Application MUST support configuration via appsettings.json
- **FR-005**: Application MUST support configuration via environment variables (override appsettings.json)
- **FR-006**: Application MUST connect to MySQL database using MySqlConnector or MySql.Data
- **FR-007**: Application MUST use WPF or WinUI 3 for user interface
- **FR-008**: Application MUST maintain the same UI layout and behavior as Python version
- **FR-009**: Application MUST handle errors gracefully with Korean error messages
- **FR-010**: Application MUST support the same database schema (no schema changes required)

### Key Entities

- **User**: Same as Python version - id, username, display_name, email, role, is_active, timestamps
- **Project**: Same as Python version - id, name, description, owner_id, is_archived, timestamps
- **Task**: Same as Python version - id, project_id, title, description, author_id, current_assignee_id, next_assignee_id, status, due_date, completed_at, timestamps
- **TaskHistory**: Same as Python version - id, task_id, actor_id, action_type, old_status, new_status, note, created_at
- **Notification**: Same as Python version - id, recipient_id, task_id, notification_type, message, is_read, created_at, read_at

### Non-Functional Requirements

- **NFR-001**: Executable file size MUST be 50-80MB (smaller than Python version)
- **NFR-002**: Application startup time MUST be under 2 seconds
- **NFR-003**: Application MUST work on Windows 10 and later
- **NFR-004**: Build process MUST be simpler than Python version (single command)
- **NFR-005**: No Python installation required for end users
- **NFR-006**: All user-facing text MUST be in Korean (same as Python version)
- **NFR-007**: Code MUST follow C# coding conventions and best practices

## Success Criteria

### Measurable Outcomes

- **SC-001**: Single .exe file is created and runs on Windows 10+ without any additional installation
- **SC-002**: All features from Python version work identically
- **SC-003**: Executable file size is 50-80MB (vs 100-200MB for Python version)
- **SC-004**: Build process requires only `dotnet publish` command (vs multiple steps for Python)
- **SC-005**: Application startup time is under 2 seconds
- **SC-006**: 100% feature parity with Python version verified through testing

## Migration Strategy

### Phase 1: Project Setup
- Create .NET project structure
- Set up WPF or WinUI 3 project
- Configure dependencies (MySqlConnector, etc.)

### Phase 2: Core Functionality
- Port domain models (User, Project, Task, etc.)
- Port repository layer (data access)
- Port business logic (sync, dashboard calculations)

### Phase 3: User Interface
- Port MainWindow and UI components
- Port user selection dialog
- Port dashboard widget
- Port status bar

### Phase 4: Configuration and Deployment
- Implement appsettings.json support
- Implement environment variable support
- Configure self-contained deployment
- Test on clean Windows machine

### Phase 5: Testing and Validation
- Unit tests for business logic
- Integration tests for repositories
- UI testing
- Feature parity validation

## Technical Decisions

### UI Framework Choice: WPF vs WinUI 3

**Decision**: WPF (recommended for initial migration)
- **Reason**: More mature, better tooling, easier migration from PyQt5
- **Alternative**: WinUI 3 (more modern, but steeper learning curve)

### Database Connector Choice: MySqlConnector vs MySql.Data

**Decision**: MySqlConnector (recommended)
- **Reason**: Modern, actively maintained, better async support
- **Alternative**: MySql.Data (official but older)

### Configuration Management

**Decision**: appsettings.json with environment variable override
- **Reason**: .NET standard approach, flexible
- **Implementation**: Use IConfiguration and Options pattern

## Review & Acceptance Checklist

- [x] User stories are prioritized and independently testable
- [x] Functional requirements are specific and measurable
- [x] Edge cases are identified
- [x] Success criteria are defined
- [x] Migration strategy is outlined
- [x] Technical decisions are documented

