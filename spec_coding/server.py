"""MCP Server for spec-driven coding - FastMCP implementation."""

import json
from typing import Optional, Annotated
from fastmcp import FastMCP

from .storage import SpecStorage
from .compression import encode_compact, estimate_token_savings

# Initialize FastMCP server
mcp = FastMCP("spec-coding-mcp")
storage: Optional[SpecStorage] = None
compression_enabled: bool = True  # Default to compressed output for efficiency


def get_storage() -> SpecStorage:
    """Get or create the storage instance."""
    global storage
    if storage is None:
        storage = SpecStorage()
    return storage


def format_output(data: dict, use_compression: bool = None) -> str:
    """
    Format output data using TOON compression for efficient LLM context usage.
    Reduces token count by 30-60% compared to JSON.

    Args:
        data: Dictionary to output
        use_compression: Override global compression setting

    Returns:
        Formatted string (TOON if compression enabled, JSON otherwise)
    """
    global compression_enabled
    should_compress = use_compression if use_compression is not None else compression_enabled

    if should_compress:
        return encode_compact(data)
    return json.dumps(data, indent=2)


# ============================================================================
# PROJECT TOOLS
# ============================================================================

@mcp.tool
def spec_init(
    project_name: Annotated[str, "Name of the project"] = "",
    description: Annotated[str, "Brief description of the project"] = "",
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Initialize a new spec-driven coding project. Creates the specs directory structure with templates.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.init_structure()

    if project_name:
        project_file = store.base_path / "project.json"
        if project_file.exists():
            data = json.loads(project_file.read_text())
            data["name"] = project_name
            data["description"] = description
            project_file.write_text(json.dumps(data, indent=2))

    use_compression = format != "json"
    return format_output({
        "success": True,
        "message": "Spec-driven coding project initialized",
        "structure": result
    }, use_compression)


@mcp.tool
def spec_list(
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """List all features in the project, showing their status and progress.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    features = store.list_features()
    use_compression = format != "json"
    return format_output({
        "success": True,
        "count": len(features),
        "features": features
    }, use_compression)


@mcp.tool
def spec_current(
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Get the currently active feature (most recently updated).

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    feature = store.get_current_feature()

    use_compression = format != "json"
    if feature is None:
        return format_output({
            "success": False,
            "error": "No active features found"
        }, use_compression)

    return format_output({
        "success": True,
        "feature": feature
    }, use_compression)


# ============================================================================
# FEATURE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool
def spec_create(
    feature_id: Annotated[str, "Unique identifier for the feature (e.g., '001-user-auth', '002-dashboard')"],
    title: Annotated[str, "Clear, concise title for the feature"],
    description: Annotated[str, "Detailed description of what the feature should accomplish"],
    tech_stack: Annotated[list[str], "Technologies to use for this feature"] = None,
    constraints: Annotated[list[str], "Technical or business constraints"] = None,
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Create a new feature specification. This is the starting point for spec-driven development.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.create_feature(
        feature_id=feature_id,
        title=title,
        description=description,
        tech_stack=tech_stack or [],
        constraints=constraints or []
    )
    use_compression = format != "json"
    return format_output({
        "success": True,
        "message": f"Feature '{feature_id}' created",
        "feature": result
    }, use_compression)


@mcp.tool
def spec_get(
    feature_id: Annotated[str, "ID of the feature to retrieve"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Get complete details of a feature including spec, plan, tasks, and review.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    feature = store.get_feature(feature_id)
    use_compression = format != "json"

    if feature is None:
        return format_output({
            "success": False,
            "error": f"Feature '{feature_id}' not found"
        }, use_compression)

    return format_output({
        "success": True,
        "feature": feature
    }, use_compression)


@mcp.tool
def spec_update(
    feature_id: Annotated[str, "ID of the feature to update"],
    updates: Annotated[dict, "Fields to update (title, description, tech_stack, constraints)"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Update fields in a feature specification.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    success = store.update_spec(feature_id, updates)
    use_compression = format != "json"
    return format_output({
        "success": success,
        "message": f"Feature '{feature_id}' updated" if success else "Update failed"
    }, use_compression)


@mcp.tool
def spec_delete(
    feature_id: Annotated[str, "ID of the feature to delete"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Delete a feature (only allowed for draft/planning status).

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.delete_feature(feature_id)
    use_compression = format != "json"
    return format_output(result, use_compression)


# ============================================================================
# REQUIREMENT TOOLS
# ============================================================================

@mcp.tool
def spec_add_requirement(
    feature_id: Annotated[str, "ID of the feature"],
    req_id: Annotated[str, "Requirement ID (e.g., 'REQ-001')"],
    title: Annotated[str, "Title of the requirement"],
    description: Annotated[str, "Detailed requirement description"],
    priority: Annotated[str, "Priority level: 'low', 'medium', 'high', or 'critical'"] = "medium",
    category: Annotated[str, "Requirement category: 'functional' or 'non-functional'"] = "functional",
    acceptance_criteria: Annotated[list[str], "List of acceptance criteria"] = None,
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Add a requirement to a feature specification with acceptance criteria.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.add_requirement(
        feature_id=feature_id,
        req_id=req_id,
        title=title,
        description=description,
        priority=priority,
        category=category,
        acceptance_criteria=acceptance_criteria or []
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


@mcp.tool
def spec_update_requirement(
    feature_id: Annotated[str, "ID of the feature"],
    req_id: Annotated[str, "ID of the requirement to update"],
    updates: Annotated[dict, "Fields to update (title, description, priority, category)"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Update a specific requirement in a feature.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.update_requirement(
        feature_id=feature_id,
        req_id=req_id,
        updates=updates
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


# ============================================================================
# PLANNING TOOLS
# ============================================================================

@mcp.tool
def spec_plan(
    feature_id: Annotated[str, "ID of the feature"],
    overview: Annotated[str, "High-level overview of the implementation approach"],
    architecture: Annotated[str, "Architecture description or diagram"] = "",
    components: Annotated[list[dict], "List of components to implement"] = None,
    dependencies: Annotated[list[str], "External dependencies needed"] = None,
    risks: Annotated[list[dict], "Risks and mitigations"] = None,
    estimated_effort: Annotated[str, "Estimated effort (e.g., '2 days', '1 week')"] = "",
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Create an implementation plan for a feature with architecture and components.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.create_plan(
        feature_id=feature_id,
        overview=overview,
        architecture=architecture,
        components=components or [],
        dependencies=dependencies or [],
        risks=risks or [],
        estimated_effort=estimated_effort
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


@mcp.tool
def spec_get_plan(
    feature_id: Annotated[str, "ID of the feature"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Get the implementation plan for a feature.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    plan = store.get_plan(feature_id)
    use_compression = format != "json"

    if plan is None:
        return format_output({
            "success": False,
            "error": f"No plan found for feature '{feature_id}'"
        }, use_compression)

    return format_output({
        "success": True,
        "plan": plan
    }, use_compression)


# ============================================================================
# TASK TOOLS
# ============================================================================

@mcp.tool
def spec_tasks(
    feature_id: Annotated[str, "ID of the feature"],
    tasks: Annotated[list[dict], "List of tasks to create"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Create a task list for implementing a feature. Breaks down the plan into actionable tasks.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.create_tasks(
        feature_id=feature_id,
        tasks=tasks
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


@mcp.tool
def spec_get_tasks(
    feature_id: Annotated[str, "ID of the feature"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Get all tasks for a feature with their current status.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    tasks = store.get_tasks(feature_id)
    use_compression = format != "json"

    if tasks is None:
        return format_output({
            "success": False,
            "error": f"No tasks found for feature '{feature_id}'"
        }, use_compression)

    return format_output({
        "success": True,
        "tasks": tasks
    }, use_compression)


@mcp.tool
def spec_update_task(
    feature_id: Annotated[str, "ID of the feature"],
    task_id: Annotated[str, "ID of the task to update"],
    status: Annotated[str, "New status: 'pending', 'in_progress', 'completed', or 'blocked'"],
    notes: Annotated[str, "Optional notes to add"] = None,
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Update a task's status (pending, in_progress, completed, blocked).

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.update_task_status(
        feature_id=feature_id,
        task_id=task_id,
        status=status,
        notes=notes
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


@mcp.tool
def spec_add_task(
    feature_id: Annotated[str, "ID of the feature"],
    title: Annotated[str, "Task title"],
    description: Annotated[str, "What needs to be done"] = "",
    dependencies: Annotated[list[str], "IDs of prerequisite tasks"] = None,
    notes: Annotated[str, "Additional notes"] = "",
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Add a new task to a feature.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.add_task(
        feature_id=feature_id,
        title=title,
        description=description,
        dependencies=dependencies or [],
        notes=notes
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


# ============================================================================
# REVIEW TOOLS
# ============================================================================

@mcp.tool
def spec_review(
    feature_id: Annotated[str, "ID of the feature"],
    approved: Annotated[bool, "Whether the implementation is approved"],
    feedback: Annotated[list[str], "General feedback"] = None,
    issues: Annotated[list[str], "Issues found during review"] = None,
    recommendations: Annotated[list[str], "Recommendations for improvement"] = None,
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Create a review for a completed feature with approval status.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.create_review(
        feature_id=feature_id,
        approved=approved,
        feedback=feedback or [],
        issues=issues or [],
        recommendations=recommendations or []
    )
    use_compression = format != "json"
    return format_output(result, use_compression)


@mcp.tool
def spec_get_review(
    feature_id: Annotated[str, "ID of the feature"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Get the review for a feature.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    review = store.get_review(feature_id)
    use_compression = format != "json"

    if review is None:
        return format_output({
            "success": False,
            "error": f"No review found for feature '{feature_id}'"
        }, use_compression)

    return format_output({
        "success": True,
        "review": review
    }, use_compression)


# ============================================================================
# STATUS TOOLS
# ============================================================================

@mcp.tool
def spec_set_status(
    feature_id: Annotated[str, "ID of the feature"],
    status: Annotated[str, "New status: 'draft', 'planning', 'ready', 'in_progress', 'review', or 'completed'"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Set the status of a feature (draft, planning, ready, in_progress, review, completed).

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    success = store.update_spec_status(feature_id, status)
    use_compression = format != "json"
    return format_output({
        "success": success,
        "message": f"Feature status set to '{status}'" if success else "Status update failed"
    }, use_compression)


@mcp.tool
def spec_complete(
    feature_id: Annotated[str, "ID of the feature"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Mark a feature as complete and move it to completed.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.complete_feature(feature_id)
    use_compression = format != "json"
    return format_output(result, use_compression)


# ============================================================================
# IMPORT/EXPORT TOOLS
# ============================================================================

@mcp.tool
def spec_export(
    feature_id: Annotated[str, "ID of the feature to export"]
) -> str:
    """Export a feature as JSON for sharing or backup. Always returns JSON format for portability."""
    store = get_storage()
    exported = store.export_feature(feature_id)

    if exported is None:
        return json.dumps({
            "success": False,
            "error": f"Feature '{feature_id}' not found"
        }, indent=2)

    return exported


@mcp.tool
def spec_import(
    feature_data: Annotated[str, "JSON string of the feature data to import"],
    format: Annotated[str, "Output format: 'toon' for compressed, 'json' for standard JSON"] = "toon"
) -> str:
    """Import a feature from JSON.

    Output uses TOON format by default for 30-60% token reduction.
    """
    store = get_storage()
    result = store.import_feature(feature_data)
    use_compression = format != "json"
    return format_output(result, use_compression)


# ============================================================================
# TOKEN ANALYSIS TOOL
# ============================================================================

@mcp.tool
def spec_analyze(
    feature_id: Annotated[str, "ID of the feature to analyze"]
) -> str:
    """Analyze token savings between TOON and JSON formats for a feature. Shows compression statistics."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return json.dumps({
            "success": False,
            "error": f"Feature '{feature_id}' not found"
        }, indent=2)

    # Compare JSON vs TOON sizes
    json_str = json.dumps(feature, indent=2)
    toon_str = encode_compact(feature)
    savings = estimate_token_savings(json_str, toon_str)

    return json.dumps({
        "success": True,
        "feature_id": feature_id,
        "json_chars": savings["json_chars"],
        "toon_chars": savings["toon_chars"],
        "char_savings": savings["char_savings"],
        "estimated_json_tokens": savings["estimated_json_tokens"],
        "estimated_toon_tokens": savings["estimated_toon_tokens"],
        "token_savings": savings["token_savings"],
        "percent_reduction": savings["percent_reduction"],
        "note": "TOON format reduces token usage by ~50%, improving LLM context efficiency"
    }, indent=2)


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("spec://features/{feature_id}/spec")
def get_feature_spec(feature_id: str) -> str:
    """Get the specification for a feature."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return json.dumps({"error": f"Feature '{feature_id}' not found"}, indent=2)

    return json.dumps(feature.get("spec", {}), indent=2)


@mcp.resource("spec://features/{feature_id}/plan")
def get_feature_plan(feature_id: str) -> str:
    """Get the implementation plan for a feature."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return json.dumps({"error": f"Feature '{feature_id}' not found"}, indent=2)

    return json.dumps(feature.get("plan", {}), indent=2)


@mcp.resource("spec://features/{feature_id}/tasks")
def get_feature_tasks(feature_id: str) -> str:
    """Get the task list for a feature."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return json.dumps({"error": f"Feature '{feature_id}' not found"}, indent=2)

    return json.dumps(feature.get("tasks", {}), indent=2)


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt
def spec_workflow_start() -> str:
    """Start a new spec-driven development workflow. Use this to define a new feature with requirements."""
    store = get_storage()

    if not store.base_path.exists():
        return """# Spec-Driven Development Workflow

This MCP server provides tools for structured, specification-driven development.

## Getting Started

1. **Initialize the project**:
   ```
   Use spec_init to create the specs directory structure
   ```

2. **Create a feature specification**:
   ```
   Use spec_create with:
   - feature_id: Unique identifier (e.g., "001-user-auth")
   - title: Clear, concise feature title
   - description: What the feature should accomplish
   ```

3. **Add requirements**:
   ```
   Use spec_add_requirement for each requirement with acceptance criteria
   ```

4. **Create implementation plan**:
   ```
   Use spec_plan to define architecture, components, and risks
   ```

5. **Break into tasks**:
   ```
   Use spec_tasks to create actionable implementation tasks
   ```

6. **Track progress**:
   ```
   Use spec_update_task to mark tasks as in_progress, completed, or blocked
   ```

7. **Review and complete**:
   ```
   Use spec_review to evaluate implementation
   Use spec_complete to archive completed features
   ```

## Available Tools

| Tool | Purpose |
|------|---------|
| spec_init | Initialize project structure |
| spec_list | List all features |
| spec_current | Get most recently updated feature |
| spec_create | Create new feature spec |
| spec_get | Get feature details |
| spec_update | Update feature fields |
| spec_add_requirement | Add requirement with criteria |
| spec_plan | Create implementation plan |
| spec_tasks | Create task list |
| spec_update_task | Update task status |
| spec_review | Create review |
| spec_complete | Complete and archive |

Start by initializing the project and creating your first feature specification.
"""

    return """# Spec-Driven Development Workflow

Project is initialized. Ready to create specifications.

## Next Steps

1. Create a feature specification using `spec_create`
2. Add requirements using `spec_add_requirement`
3. Plan the implementation using `spec_plan`
4. Break into tasks using `spec_tasks`
5. Track progress and complete

Current features: Use `spec_list` to see all features.
"""


@mcp.prompt
def spec_create_from_idea(idea: str) -> str:
    """Create a complete feature specification from a high-level idea or description."""
    return f"""# Creating Feature Specification from Idea

## Original Idea
{idea}

## Instructions

Based on the idea above, help create a complete feature specification:

1. **Generate a feature_id**: Create a unique, descriptive ID (e.g., "001-user-auth", "002-dashboard")

2. **Create the specification**:
   ```
   Use spec_create with:
   - feature_id: [generated ID]
   - title: [concise title extracted from idea]
   - description: [detailed description expanding the idea]
   - tech_stack: [suggested technologies]
   - constraints: [any constraints or limitations]
   ```

3. **Add requirements**:
   For each distinct requirement, use `spec_add_requirement` with:
   - req_id: REQ-001, REQ-002, etc.
   - title: Clear requirement name
   - description: Detailed explanation
   - priority: low/medium/high/critical
   - category: functional/non-functional
   - acceptance_criteria: Testable criteria

4. **Ensure completeness**:
   - All user stories are captured
   - Edge cases are considered
   - Non-functional requirements (performance, security) included
   - Dependencies identified

Proceed to create the specification now.
"""


@mcp.prompt
def spec_plan_feature(feature_id: str) -> str:
    """Generate an implementation plan for a feature based on its requirements."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return f"Feature '{feature_id}' not found. Use spec_create first."

    spec = feature.get("spec", {})
    return f"""# Implementation Planning

## Feature: {spec.get('title', feature_id)}

### Current Requirements
{json.dumps(spec.get('requirements', []), indent=2)}

### Planning Instructions

Create a comprehensive implementation plan using `spec_plan`:

1. **Architecture Overview**:
   - Define the overall approach
   - Identify key patterns and principles
   - Consider scalability and maintainability

2. **Components to Build**:
   For each component specify:
   - name: Component identifier
   - purpose: What it does
   - files: Files to create/modify
   - dependencies: Other components or external libs

3. **Dependencies**:
   - External packages needed
   - Internal dependencies
   - Infrastructure requirements

4. **Risks & Mitigations**:
   Identify potential risks with:
   - risk: Description
   - likelihood: Low/Medium/High
   - impact: Low/Medium/High
   - mitigation: How to address it

5. **Effort Estimation**:
   - Provide realistic time estimate
   - Consider complexity and unknowns

Use `spec_plan` to save the plan, then proceed to task breakdown.
"""


@mcp.prompt
def spec_breakdown_tasks(feature_id: str) -> str:
    """Break down a feature plan into actionable implementation tasks."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return f"Feature '{feature_id}' not found."

    plan = feature.get("plan", {})
    spec = feature.get("spec", {})

    return f"""# Task Breakdown

## Feature: {spec.get('title', feature_id)}

### Plan Overview
{plan.get('overview', 'No plan yet')}

### Components to Implement
{json.dumps(plan.get('components', []), indent=2)}

### Task Creation Instructions

Break down the implementation into actionable tasks using `spec_tasks`:

1. **Order tasks logically**:
   - Start with foundational work
   - Progress through components
   - End with testing and integration

2. **For each task, specify**:
   - id: TASK-001, TASK-002, etc.
   - title: Clear, action-oriented title
   - description: What needs to be done
   - dependencies: Prerequisite task IDs
   - notes: Implementation hints

3. **Task granularity**:
   - Each task should be completable in one session
   - Clear acceptance criteria
   - Measurable progress

4. **Example task structure**:
   ```json
   {{
     "id": "TASK-001",
     "title": "Set up project structure",
     "description": "Initialize directories and base configuration",
     "dependencies": [],
     "notes": "Follow existing patterns"
   }}
   ```

Create tasks now using `spec_tasks`, then use `spec_update_task` to track progress.
"""


@mcp.prompt
def spec_review_checklist(feature_id: str) -> str:
    """Generate a review checklist for evaluating implementation quality."""
    store = get_storage()
    feature = store.get_feature(feature_id)

    if feature is None:
        return f"Feature '{feature_id}' not found."

    spec = feature.get("spec", {})
    tasks_data = feature.get("tasks", {})
    tasks = tasks_data.get("tasks", [])

    return f"""# Review Checklist

## Feature: {spec.get('title', feature_id)}

### Task Completion Status
{json.dumps(tasks_data.get('summary', {{}}), indent=2)}

### Requirements Check
{json.dumps(spec.get('requirements', []), indent=2)}

### Review Instructions

Perform a thorough review before completing the feature:

1. **Requirements Verification**:
   - All requirements implemented?
   - Acceptance criteria met?
   - Edge cases handled?

2. **Code Quality**:
   - Clean, readable code?
   - Proper error handling?
   - Security considerations addressed?

3. **Testing**:
   - Unit tests written?
   - Integration tests passing?
   - Manual testing completed?

4. **Documentation**:
   - Code comments where needed?
   - API documentation updated?
   - README updated?

5. **Performance**:
   - No obvious bottlenecks?
   - Resources used efficiently?

Use `spec_review` to record the review outcome:
```
spec_review(
  feature_id="{feature_id}",
  approved=true/false,
  feedback=["..."],
  issues=["..."],
  recommendations=["..."]
)
```

If approved, use `spec_complete` to archive the feature.
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Entry point for the server."""
    mcp.run()


if __name__ == "__main__":
    main()