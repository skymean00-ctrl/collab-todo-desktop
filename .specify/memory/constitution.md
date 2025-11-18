# Collab Todo Desktop Constitution

## Core Principles

### I. Desktop-First Architecture
Collab Todo Desktop is a PyQt5-based desktop application that prioritizes:
- Native desktop experience with responsive UI
- Offline-first capability with periodic synchronization
- Single executable deployment target (PyInstaller)
- Direct database connection to NAS-hosted MySQL/PostgreSQL

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
- **Models**: Immutable domain objects (dataclasses)
- **Repositories**: Data access layer (SQL queries)
- **Business Logic**: Sync, dashboard calculations
- **UI**: PyQt5 components (MainWindow, widgets)
- **Config**: Environment variable loading

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
- **UI Framework**: PyQt5 (version 5.15.11)
- **Database**: MySQL (via mysql-connector-python 9.5.0)
- **Packaging**: PyInstaller (6.11.1) for single-file distribution
- **Installer**: Inno Setup for Windows installer package creation
- **Testing**: pytest (8.3.4)
- **Python**: 3.11+ (type hints required)

### Database Schema
- Foreign key constraints enforced
- Timestamps for audit trail (created_at, updated_at)
- Soft deletes via status flags (is_archived, is_active)
- Indexes on frequently queried columns

### Deployment
- Target: Windows desktop (single executable via PyInstaller)
- Installer: Windows installer package (.exe) using Inno Setup
- Database: NAS-hosted MySQL/PostgreSQL (network connection)
- No local database required
- Configuration via environment variables or config file
- Installer MUST include:
  - All application binaries and dependencies
  - Start menu shortcuts
  - Desktop shortcut (optional, user choice)
  - Uninstaller
  - Configuration guide/documentation

## Development Workflow

### Code Quality
- Type hints required for all function signatures
- Docstrings for public functions and classes
- Korean comments for business logic explanation
- English for technical documentation

### Error Handling
- Custom exception types (`DatabaseConnectionError`, `AiSummaryError`)
- User-facing error messages in Korean
- Technical details in logs/console
- Graceful degradation (e.g., AI service unavailable)

### Testing Standards
- Unit tests for pure business logic
- Integration tests for repository functions (with test database)
- UI tests for critical user flows
- Mock external services (AI API) in tests

## Governance

This constitution guides all development decisions. When adding features:
1. Verify alignment with core principles
2. Maintain separation of concerns
3. Follow defensive programming practices
4. Update this document if principles evolve

**Version**: 1.0.0 | **Ratified**: 2025-01-XX | **Last Amended**: 2025-01-XX
