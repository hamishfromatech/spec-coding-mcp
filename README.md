# Spec-Coding MCP Server

A FastMCP-based server for spec-driven coding workflows. Provides tools, resources, and prompts to help LLMs perform structured, specification-driven development.

## Features

- **FastMCP Framework**: Modern, Pythonic MCP server built on FastMCP 2.x
- **JSON Storage**: All data stored in simple JSON files
- **Complete Workflow**: Specification → Planning → Tasks → Review → Complete
- **MCP Protocol**: Full support for tools, resources, and prompts
- **TOON Compression**: 30-60% token reduction for efficient context window usage

## Token Compression

By default, all tool outputs use **TOON format** (Token-Oriented Object Notation) which reduces token usage by 30-60% compared to JSON. This helps prevent context window congestion when working with large specifications.

**Example comparison:**

JSON (630 chars, ~157 tokens):
```json
{
  "id": "001-user-auth",
  "title": "User Authentication",
  "requirements": [
    {"id": "REQ-001", "title": "Login", "priority": "high"}
  ]
}
```

TOON (310 chars, ~77 tokens):
```
id: 001-user-auth
title: User Authentication
[1,]{id,title,priority}:
REQ-001,Login,high
```

Use `format: "json"` parameter in any tool to get standard JSON output if needed.

## Installation

```bash
pip install -e .
```

Or install dependencies directly:
```bash
pip install fastmcp
```

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/.claude/config.json` or `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "spec-coding": {
      "command": "uvx",
      "args": ["spec-coding-mcp"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

Or with Python directly:
```json
{
  "mcpServers": {
    "spec-coding": {
      "command": "python",
      "args": ["-m", "spec_coding.server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

## Available Tools

### Project Management

| Tool | Description |
|------|-------------|
| `spec_init` | Initialize a new spec-driven project |
| `spec_list` | List all features in the project |
| `spec_current` | Get the currently active feature |

### Feature Management

| Tool | Description |
|------|-------------|
| `spec_create` | Create a new feature specification |
| `spec_get` | Get complete feature details |
| `spec_update` | Update feature fields |
| `spec_delete` | Delete a feature (draft only) |

### Requirements

| Tool | Description |
|------|-------------|
| `spec_add_requirement` | Add a requirement with acceptance criteria |
| `spec_update_requirement` | Update a specific requirement |

### Planning

| Tool | Description |
|------|-------------|
| `spec_plan` | Create an implementation plan |
| `spec_get_plan` | Get the implementation plan |

### Tasks

| Tool | Description |
|------|-------------|
| `spec_tasks` | Create a task list from a plan |
| `spec_get_tasks` | Get all tasks for a feature |
| `spec_update_task` | Update a task's status |
| `spec_add_task` | Add a new task |

### Review & Complete

| Tool | Description |
|------|-------------|
| `spec_review` | Create a review with approval status |
| `spec_get_review` | Get the review for a feature |
| `spec_set_status` | Set feature status manually |
| `spec_complete` | Mark feature as complete and archive |

### Import/Export

| Tool | Description |
|------|-------------|
| `spec_export` | Export a feature as JSON |
| `spec_import` | Import a feature from JSON |
| `spec_analyze` | Analyze token savings between TOON and JSON formats |

## Output Format

All tools support a `format` parameter:
- `format: "toon"` (default) - Compressed TOON format, 30-60% fewer tokens
- `format: "json"` - Standard JSON format for compatibility

```python
# Get feature in TOON format (default, more efficient)
spec_get(feature_id="001-auth")

# Get feature in JSON format (when needed for parsing)
spec_get(feature_id="001-auth", format="json")
```

## Workflow

### 1. Initialize Project

```
Use spec_init to create the specs directory structure
```

### 2. Create Specification

```
spec_create(
  feature_id="001-user-auth",
  title="User Authentication",
  description="Implement secure user authentication with login, logout, and session management",
  tech_stack=["Python", "FastAPI", "JWT"],
  constraints=["Must be GDPR compliant", "Support 2FA"]
)
```

### 3. Add Requirements

```
spec_add_requirement(
  feature_id="001-user-auth",
  req_id="REQ-001",
  title="User Login",
  description="Users can log in with email and password",
  priority="high",
  acceptance_criteria=[
    "User can enter email and password",
    "Invalid credentials show appropriate error",
    "Successful login creates session",
    "Session persists for 24 hours"
  ]
)
```

### 4. Create Plan

```
spec_plan(
  feature_id="001-user-auth",
  overview="Implement JWT-based authentication with FastAPI",
  architecture="API Gateway -> Auth Service -> User Database",
  components=[
    {"name": "Auth Service", "purpose": "Handle authentication logic", "files": ["auth/service.py"]},
    {"name": "Session Manager", "purpose": "Manage user sessions", "files": ["auth/session.py"]}
  ],
  risks=[
    {"risk": "Token theft", "likelihood": "Medium", "impact": "High", "mitigation": "Use short-lived tokens with refresh"}
  ]
)
```

### 5. Create Tasks

```
spec_tasks(
  feature_id="001-user-auth",
  tasks=[
    {"id": "TASK-001", "title": "Create auth module", "dependencies": []},
    {"id": "TASK-002", "title": "Implement login endpoint", "dependencies": ["TASK-001"]},
    {"id": "TASK-003", "title": "Add session management", "dependencies": ["TASK-001"]}
  ]
)
```

### 6. Track Progress

```
spec_update_task(feature_id="001-user-auth", task_id="TASK-001", status="in_progress")
spec_update_task(feature_id="001-user-auth", task_id="TASK-001", status="completed")
```

### 7. Review & Complete

```
spec_review(
  feature_id="001-user-auth",
  approved=True,
  feedback=["Clean implementation", "Good test coverage"],
  recommendations=["Consider adding rate limiting"]
)

spec_complete(feature_id="001-user-auth")
```

## Directory Structure

```
specs/
├── project.json              # Project metadata
├── templates/                # Template files
│   ├── spec_template.json
│   ├── plan_template.json
│   └── tasks_template.json
├── active/                   # Active features
│   └── <feature-id>/
│       ├── spec.json         # Feature specification
│       ├── plan.json         # Implementation plan
│       ├── tasks.json        # Task list
│       └── review.json       # Review (optional)
└── completed/                # Completed features
    └── <feature-id>/
        └── ...
```

## Prompts

The server provides prompts to guide the spec-driven workflow:

| Prompt | Description |
|--------|-------------|
| `spec_workflow_start` | Start a new spec-driven workflow |
| `spec_create_from_idea` | Create specification from an idea description |
| `spec_plan_feature` | Generate implementation plan for a feature |
| `spec_breakdown_tasks` | Break down a plan into actionable tasks |
| `spec_review_checklist` | Generate a review checklist for a feature |

## Resources

Access feature data via MCP resources:

- `spec://features/{feature_id}/spec` - Feature specification
- `spec://features/{feature_id}/plan` - Implementation plan
- `spec://features/{feature_id}/tasks` - Task list

## Development

Run the server directly:
```bash
python -m spec_coding.server
```

Run tests:
```bash
python -m pytest tests/
```

## Architecture

Built with **FastMCP**, which provides:

- **Declarative decorators**: `@mcp.tool`, `@mcp.resource`, `@mcp.prompt`
- **Type-safe parameters**: Using `Annotated[type, "description"]` for automatic schema generation
- **Clean code**: ~60% less boilerplate than the raw MCP SDK
- **Automatic stdio handling**: Simple `mcp.run()` entry point

## License

MIT