# Feature Specification: Collab Todo Desktop - Existing System Analysis

**Feature Branch**: `000-existing-system`  
**Created**: 2025-01-XX  
**Status**: Analysis  
**Input**: Existing PyQt5 desktop application for collaborative todo management

## Overview

Collab Todo Desktop is a Windows desktop application (v1.0 Phase 1) built with PyQt5 that provides collaborative task management functionality. The application connects to a NAS-hosted MySQL/PostgreSQL database and provides a desktop interface for viewing and managing tasks, projects, and user assignments.

## User Scenarios & Testing

### User Story 1 - View Personal Task Dashboard (Priority: P1)

Users can view a summary dashboard showing their assigned tasks with status breakdown and due date information.

**Why this priority**: Core functionality - users need to see their work at a glance

**Independent Test**: Can be tested by launching the application, connecting to a database with sample tasks, and verifying the dashboard widget displays correct counts for each status category.

**Acceptance Scenarios**:

1. **Given** a user has tasks assigned, **When** the application starts, **Then** the dashboard displays task counts by status (pending, in_progress, review, on_hold, completed, cancelled)
2. **Given** tasks have due dates, **When** viewing the dashboard, **Then** it shows counts for tasks due soon (within 24h) and overdue tasks
3. **Given** the database connection fails, **When** the application attempts to sync, **Then** the status bar shows "DB: 끊김" and the dashboard remains empty

---

### User Story 2 - Periodic Task Synchronization (Priority: P1)

The application automatically synchronizes task data from the database every 5 seconds, updating the dashboard and connection status.

**Why this priority**: Core functionality - ensures users see up-to-date information

**Independent Test**: Can be tested by modifying task data in the database and observing the dashboard update within 5 seconds.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** 5 seconds pass, **Then** the application queries the database for updated tasks
2. **Given** a successful sync, **When** the sync completes, **Then** the status bar shows "DB: 연결됨" and displays the last sync timestamp
3. **Given** a database connection error, **When** sync attempts fail, **Then** the status bar shows "DB: 끊김" and an error message is displayed

---

### User Story 3 - AI Text Summarization Test (Priority: P3)

Users can test the AI summarization service through a menu option that summarizes sample text.

**Why this priority**: Optional feature - demonstrates AI integration capability but not core to task management

**Independent Test**: Can be tested by configuring AI service environment variables and using the "AI 요약 테스트" menu option.

**Acceptance Scenarios**:

1. **Given** AI service is configured, **When** user selects "AI 요약 테스트", **Then** a dialog shows the original text and its summary
2. **Given** AI service is not configured, **When** user selects "AI 요약 테스트", **Then** an informational message explains that configuration is needed
3. **Given** AI service call fails, **When** the test runs, **Then** an error dialog shows the failure reason with the original text

---

### Edge Cases

- What happens when the database connection is lost during sync? (Handled with try/except, shows error message)
- How does the system handle invalid user IDs? (Repository functions return empty lists for invalid IDs)
- What happens when tasks have NULL due dates? (Dashboard correctly handles NULL values, only counts tasks with due dates for "due soon" and "overdue")
- How does the system handle database transaction failures? (Context manager rolls back on exception)

## Requirements

### Functional Requirements

- **FR-001**: System MUST connect to MySQL/PostgreSQL database using environment variable configuration
- **FR-002**: System MUST display connection status in the status bar (연결됨/끊김)
- **FR-003**: System MUST periodically synchronize task data every 5 seconds
- **FR-004**: System MUST display last synchronization timestamp in UTC format
- **FR-005**: System MUST show task summary dashboard with counts by status (pending, in_progress, review, on_hold, completed, cancelled)
- **FR-006**: System MUST calculate and display tasks due soon (within 24 hours) and overdue tasks
- **FR-007**: System MUST handle database connection failures gracefully with user-friendly error messages
- **FR-008**: System MUST support AI text summarization via external HTTP API (optional feature)
- **FR-009**: System MUST validate all database queries use parameterized statements (SQL injection prevention)
- **FR-010**: System MUST use context managers for database connections to prevent resource leaks

### Key Entities

- **User**: Represents a system user with id, username, display_name, email, role (user/admin/supervisor), active status, and timestamps
- **Project**: Represents a work project with id, name, description, owner_id, archive status, and timestamps
- **Task**: Represents a work item with id, project_id, title, description, author_id, current_assignee_id, next_assignee_id, status (pending/in_progress/review/completed/on_hold/cancelled), due_date, completed_at, and timestamps
- **TaskHistory**: Represents audit trail of task changes with id, task_id, actor_id, action_type, old_status, new_status, note, and created_at
- **Notification**: Represents user notifications with id, recipient_id, task_id, notification_type, message, read status, and timestamps

### Non-Functional Requirements

- **NFR-001**: Application MUST be packaged as a single executable using PyInstaller
- **NFR-002**: Application MUST support Windows desktop environment
- **NFR-003**: Database connection MUST support SSL/TLS when configured
- **NFR-004**: AI service calls MUST timeout after 15 seconds (configurable)
- **NFR-005**: Application MUST handle network interruptions gracefully
- **NFR-006**: All user-facing text MUST be in Korean
- **NFR-007**: Application MUST use type hints throughout codebase

## Success Criteria

### Measurable Outcomes

- **SC-001**: Application successfully connects to database and displays connection status within 2 seconds of startup
- **SC-002**: Dashboard updates reflect database changes within 5 seconds (sync interval)
- **SC-003**: Application handles database connection failures without crashing
- **SC-004**: All database operations use parameterized queries (verified by code review)
- **SC-005**: Application can be packaged as a single executable file using PyInstaller

## Current Implementation Status

### Implemented Features (v1.0 Phase 1)

✅ Database connection management with context managers  
✅ Configuration loading from environment variables  
✅ Repository pattern for data access  
✅ Task synchronization (polling every 5 seconds)  
✅ Dashboard widget with task summary statistics  
✅ Connection status display in status bar  
✅ AI summarization service integration (test feature)  
✅ Type-safe domain models (dataclasses)  
✅ Error handling with custom exceptions  

### Not Yet Implemented (Future Phases)

❌ Sequential task delegation workflow  
❌ Notification system UI  
❌ Task history timeline view  
❌ AI-powered task summaries  
❌ User authentication/login UI  
❌ Project management UI  
❌ Task creation/editing UI  

## Architecture Overview

### Layer Structure

1. **UI Layer** (`main.py`, `MainWindow`): PyQt5 components, event handling
2. **Business Logic Layer** (`sync.py`, `dashboard.py`): Task synchronization, statistics calculation
3. **Data Access Layer** (`repositories.py`): SQL queries, data mapping
4. **Domain Models** (`models.py`): Immutable dataclasses representing business entities
5. **Infrastructure** (`db.py`, `config.py`, `ai_client.py`): Database connections, configuration, external services

### Key Design Patterns

- **Repository Pattern**: All database access through repository functions
- **Context Manager Pattern**: Database connections managed via `with` statements
- **Dataclass Pattern**: Immutable domain models
- **Strategy Pattern**: Configurable AI service (can be swapped)

## Technical Debt & Improvement Opportunities

1. **Hardcoded User ID**: Currently uses `user_id = 1` in sync logic - needs proper user authentication
2. **No Incremental Sync**: Full task list fetched every sync - could optimize with timestamp-based filtering
3. **Limited Error Recovery**: No retry logic for transient database failures
4. **No Caching**: Dashboard recalculates from full task list every sync
5. **Synchronous AI Calls**: AI summarization blocks UI thread
6. **No Unit Tests**: Missing test coverage for business logic
7. **SQL String Formatting**: One query uses f-string formatting (line 139 in repositories.py) - should use parameterized query

## Review & Acceptance Checklist

- [x] User stories are prioritized and independently testable
- [x] Functional requirements are specific and measurable
- [x] Edge cases are identified
- [x] Success criteria are defined
- [x] Current implementation status is documented
- [x] Architecture is described
- [x] Technical debt is identified

