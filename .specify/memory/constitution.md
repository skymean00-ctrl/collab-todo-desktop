# Collab Todo Desktop Constitution

## Core Principles

### I. Desktop-First Architecture
Collab Todo Desktop is a Windows desktop application that prioritizes:
- Native desktop experience with responsive UI
- Offline-first capability with periodic synchronization
- Single executable deployment target (.NET Self-contained)
- Direct database connection to NAS-hosted MySQL/PostgreSQL
- **Technology**: C# / .NET (migrated from Python/PyQt5 for easier deployment)

### II. Repository Pattern for Data Access
All database operations MUST be abstracted through repository functions:
- SQL queries are centralized in `repositories.py`
- No raw SQL in business logic or UI components
- Type-safe domain models (`models.py`) separate from database schema
- Connection management through context managers (`db_connection`)

### III. Configuration via Environment Variables
Application configuration MUST be externalized:
- Database credentials via `COLLAB_TODO_DB_*` environment variables
- AI service settings via `COLLAB_TODO_AI_*` environment variables
- No hardcoded secrets or connection strings
- Graceful degradation when optional services (AI) are unavailable

### IV. Defensive Programming
Code MUST handle edge cases and failures gracefully:
- Validate all inputs (IDs, user data, configuration)
- Use context managers for resource management (DB connections)
- Wrap external service calls (AI, DB) with custom exceptions
- Provide user-friendly error messages in UI

### V. Separation of Concerns
Clear separation between layers:
- **Models**: Immutable domain objects (C# records or classes)
- **Repositories**: Data access layer (SQL queries, Entity Framework optional)
- **Business Logic**: Sync, dashboard calculations
- **UI**: WPF/WinUI components (MainWindow, UserControls)
- **Config**: Configuration via appsettings.json, environment variables, or config file

### VI. Testability
Code structure MUST support testing:
- Pure functions where possible (e.g., `summarize_tasks`)
- Dependency injection for external services (DB, AI)
- Mockable interfaces for network calls
- Unit tests for business logic, integration tests for repositories

### VII. Incremental Feature Development
Development follows phased approach:
- **Phase 1 (v1.0)**: Basic CRUD, sync, dashboard
- **Future Phases**: Sequential delegation, notifications, history, AI summaries
- Each phase delivers working, deployable software

## Technology Constraints

### Required Stack
- **Language**: C# (.NET 8.0 or later)
- **UI Framework**: WPF (Windows Presentation Foundation) or WinUI 3
- **Database**: MySQL (via MySqlConnector or MySql.Data)
- **Packaging**: .NET Self-contained deployment (single-file)
- **Installer**: Inno Setup for Windows installer package creation (optional)
- **Testing**: xUnit or NUnit
- **IDE**: Visual Studio 2022 Community (free) or Visual Studio Code

### Database Schema
- Foreign key constraints enforced
- Timestamps for audit trail (created_at, updated_at)
- Soft deletes via status flags (is_archived, is_active)
- Indexes on frequently queried columns

### Deployment
- Target: Windows desktop (single executable via .NET Self-contained)
- **Primary Method**: Single .exe file (50-80MB, all dependencies included)
- **Optional**: Windows installer package (.exe) using Inno Setup
- Database: NAS-hosted MySQL/PostgreSQL (network connection)
- No local database required
- Configuration via environment variables, appsettings.json, or config file
- **Key Advantage**: No Python installation required, simpler deployment
- Installer (if used) MUST include:
  - Single executable file (self-contained)
  - Start menu shortcuts
  - Desktop shortcut (optional, user choice)
  - Uninstaller (if using installer)
  - Configuration guide/documentation

## Development Workflow

### Code Quality
- Strong typing (C# is statically typed)
- XML documentation comments for public APIs
- Korean comments for business logic explanation
- English for technical documentation
- Follow C# coding conventions and style guidelines

### Error Handling
- Custom exception types (`DatabaseConnectionException`, `AiSummaryException`)
- User-facing error messages in Korean
- Technical details in logs/console
- Graceful degradation (e.g., AI service unavailable)
- Use try-catch-finally for resource management (using statements for IDisposable)

### Testing Standards
- Unit tests for pure business logic (xUnit or NUnit)
- Integration tests for repository functions (with test database)
- UI tests for critical user flows (optional, using UI automation)
- Mock external services (AI API) in tests using Moq or similar

## Governance

This constitution guides all development decisions. When adding features:
1. Verify alignment with core principles
2. Maintain separation of concerns
3. Follow defensive programming practices
4. Update this document if principles evolve

**Version**: 2.0.0 | **Ratified**: 2025-01-XX | **Last Amended**: 2025-01-XX

## Migration Notes

### From Python/PyQt5 to C# / .NET

This constitution has been updated to reflect the migration from Python/PyQt5 to C# / .NET for the following reasons:
- **Simpler deployment**: Single .exe file without Python runtime
- **Better Windows integration**: Native .NET framework
- **Easier installation**: No Python installation required for end users
- **Smaller footprint**: 50-80MB vs 100-200MB
- **Faster startup**: Native compilation vs interpreted Python

The core principles remain the same, but technology stack has been updated.
