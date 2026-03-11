"""JSON file storage for spec-driven coding - Pure Python implementation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import (
    FeatureSpec, Task, Requirement, AcceptanceCriteria,
    FeatureStatus, TaskStatus, ImplementationPlan, Review
)


class SpecStorage:
    """Manages specification storage in JSON files."""

    def __init__(self, base_path: str = "specs"):
        self.base_path = Path(base_path)
        self.active_path = self.base_path / "active"
        self.completed_path = self.base_path / "completed"
        self.templates_path = self.base_path / "templates"

    def init_structure(self) -> dict:
        """Initialize the specs directory structure."""
        for path in [self.base_path, self.active_path, self.completed_path, self.templates_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Create default templates as JSON
        self._create_templates()

        # Create a project.json for project-level settings
        project_file = self.base_path / "project.json"
        if not project_file.exists():
            project_file.write_text(json.dumps({
                "name": "",
                "description": "",
                "tech_stack": [],
                "conventions": [],
                "created": datetime.now().isoformat(),
                "features": []
            }, indent=2))

        return {
            "created": [str(p) for p in [self.base_path, self.active_path, self.completed_path, self.templates_path]],
            "status": "initialized"
        }

    def _create_templates(self) -> None:
        """Create template JSON files."""
        # Spec template
        spec_template = self.templates_path / "spec_template.json"
        if not spec_template.exists():
            spec_template.write_text(json.dumps({
                "id": "{{FEATURE_ID}}",
                "title": "{{FEATURE_TITLE}}",
                "description": "{{FEATURE_DESCRIPTION}}",
                "status": "draft",
                "requirements": [],
                "tech_stack": [],
                "constraints": [],
                "created_at": "{{CREATED_AT}}",
                "updated_at": "{{UPDATED_AT}}"
            }, indent=2))

        # Plan template
        plan_template = self.templates_path / "plan_template.json"
        if not plan_template.exists():
            plan_template.write_text(json.dumps({
                "feature_id": "{{FEATURE_ID}}",
                "overview": "",
                "architecture": "",
                "components": [],
                "dependencies": [],
                "risks": [],
                "estimated_effort": "",
                "created_at": "{{CREATED_AT}}"
            }, indent=2))

        # Tasks template
        tasks_template = self.templates_path / "tasks_template.json"
        if not tasks_template.exists():
            tasks_template.write_text(json.dumps({
                "feature_id": "{{FEATURE_ID}}",
                "summary": {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "pending": 0
                },
                "tasks": [],
                "created_at": "{{CREATED_AT}}",
                "updated_at": "{{UPDATED_AT}}"
            }, indent=2))

    def list_features(self) -> list[dict]:
        """List all features (active and completed)."""
        features = []

        # Active features
        for feature_dir in self.active_path.iterdir():
            if feature_dir.is_dir():
                spec_file = feature_dir / "spec.json"
                if spec_file.exists():
                    try:
                        data = json.loads(spec_file.read_text())
                        features.append({
                            "id": feature_dir.name,
                            "title": data.get("title", ""),
                            "status": data.get("status", "draft"),
                            "path": str(feature_dir),
                            "type": "active"
                        })
                    except (json.JSONDecodeError, Exception):
                        pass

        # Completed features
        for feature_dir in self.completed_path.iterdir():
            if feature_dir.is_dir():
                spec_file = feature_dir / "spec.json"
                if spec_file.exists():
                    try:
                        data = json.loads(spec_file.read_text())
                        features.append({
                            "id": feature_dir.name,
                            "title": data.get("title", ""),
                            "status": data.get("status", "completed"),
                            "path": str(feature_dir),
                            "type": "completed"
                        })
                    except (json.JSONDecodeError, Exception):
                        pass

        # Sort by updated_at (most recent first)
        features.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return features

    def create_feature(self, feature_id: str, title: str, description: str,
                       tech_stack: list[str] = None, constraints: list[str] = None) -> dict:
        """Create a new feature specification."""
        feature_dir = self.active_path / feature_id
        feature_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now().isoformat()

        spec = {
            "id": feature_id,
            "title": title,
            "description": description,
            "status": "draft",
            "requirements": [],
            "tech_stack": tech_stack or [],
            "constraints": constraints or [],
            "created_at": now,
            "updated_at": now
        }

        spec_file = feature_dir / "spec.json"
        spec_file.write_text(json.dumps(spec, indent=2))

        # Create empty plan.json
        plan_file = feature_dir / "plan.json"
        plan_file.write_text(json.dumps({
            "feature_id": feature_id,
            "overview": "",
            "architecture": "",
            "components": [],
            "dependencies": [],
            "risks": [],
            "estimated_effort": "",
            "created_at": now
        }, indent=2))

        # Create empty tasks.json
        tasks_file = feature_dir / "tasks.json"
        tasks_file.write_text(json.dumps({
            "feature_id": feature_id,
            "summary": {"total": 0, "completed": 0, "in_progress": 0, "blocked": 0, "pending": 0},
            "tasks": [],
            "created_at": now,
            "updated_at": now
        }, indent=2))

        return {
            "id": feature_id,
            "title": title,
            "path": str(feature_dir),
            "spec_file": str(spec_file),
            "status": "created"
        }

    def get_feature(self, feature_id: str) -> Optional[dict]:
        """Get complete feature data including spec, plan, tasks, and review."""
        # Check active first
        feature_dir = self.active_path / feature_id
        feature_type = "active"

        if not feature_dir.exists():
            # Check completed
            feature_dir = self.completed_path / feature_id
            feature_type = "completed"
            if not feature_dir.exists():
                return None

        result = {
            "id": feature_id,
            "type": feature_type,
            "path": str(feature_dir)
        }

        # Load spec.json
        spec_file = feature_dir / "spec.json"
        if spec_file.exists():
            try:
                result["spec"] = json.loads(spec_file.read_text())
            except json.JSONDecodeError:
                result["spec"] = {}

        # Load plan.json
        plan_file = feature_dir / "plan.json"
        if plan_file.exists():
            try:
                result["plan"] = json.loads(plan_file.read_text())
            except json.JSONDecodeError:
                result["plan"] = {}

        # Load tasks.json
        tasks_file = feature_dir / "tasks.json"
        if tasks_file.exists():
            try:
                result["tasks"] = json.loads(tasks_file.read_text())
            except json.JSONDecodeError:
                result["tasks"] = {}

        # Load review.json if exists
        review_file = feature_dir / "review.json"
        if review_file.exists():
            try:
                result["review"] = json.loads(review_file.read_text())
            except json.JSONDecodeError:
                pass

        return result

    def update_spec(self, feature_id: str, updates: dict) -> bool:
        """Update spec fields."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return False

        spec_file = feature_dir / "spec.json"
        if not spec_file.exists():
            return False

        try:
            spec = json.loads(spec_file.read_text())
            spec.update(updates)
            spec["updated_at"] = datetime.now().isoformat()
            spec_file.write_text(json.dumps(spec, indent=2))
            return True
        except (json.JSONDecodeError, Exception):
            return False

    def update_spec_status(self, feature_id: str, status: str) -> bool:
        """Update the status of a feature spec."""
        return self.update_spec(feature_id, {"status": status})

    def add_requirement(self, feature_id: str, req_id: str, title: str, description: str,
                        priority: str = "medium", category: str = "functional",
                        acceptance_criteria: list[str] = None) -> dict:
        """Add a requirement to a feature spec."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        spec_file = feature_dir / "spec.json"
        if not spec_file.exists():
            return {"success": False, "error": "Spec file not found"}

        try:
            spec = json.loads(spec_file.read_text())

            requirement = {
                "id": req_id,
                "title": title,
                "description": description,
                "priority": priority,
                "category": category,
                "acceptance_criteria": [
                    {"id": f"AC-{req_id}-{i+1}", "description": ac, "met": False}
                    for i, ac in enumerate(acceptance_criteria or [])
                ]
            }

            spec["requirements"].append(requirement)
            spec["updated_at"] = datetime.now().isoformat()
            spec_file.write_text(json.dumps(spec, indent=2))

            return {"success": True, "requirement": requirement}
        except (json.JSONDecodeError, Exception) as e:
            return {"success": False, "error": str(e)}

    def update_requirement(self, feature_id: str, req_id: str, updates: dict) -> dict:
        """Update a specific requirement."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        spec_file = feature_dir / "spec.json"
        if not spec_file.exists():
            return {"success": False, "error": "Spec file not found"}

        try:
            spec = json.loads(spec_file.read_text())

            for req in spec["requirements"]:
                if req["id"] == req_id:
                    req.update(updates)
                    break
            else:
                return {"success": False, "error": "Requirement not found"}

            spec["updated_at"] = datetime.now().isoformat()
            spec_file.write_text(json.dumps(spec, indent=2))

            return {"success": True, "requirement_id": req_id}
        except (json.JSONDecodeError, Exception) as e:
            return {"success": False, "error": str(e)}

    def create_plan(self, feature_id: str, overview: str, architecture: str,
                    components: list[dict], dependencies: list[str] = None,
                    risks: list[dict] = None, estimated_effort: str = "") -> dict:
        """Create an implementation plan for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        now = datetime.now().isoformat()

        plan = {
            "feature_id": feature_id,
            "overview": overview,
            "architecture": architecture,
            "components": components,
            "dependencies": dependencies or [],
            "risks": risks or [],
            "estimated_effort": estimated_effort,
            "created_at": now,
            "updated_at": now
        }

        plan_file = feature_dir / "plan.json"
        plan_file.write_text(json.dumps(plan, indent=2))

        # Update spec status
        self.update_spec_status(feature_id, "planning")

        return {
            "success": True,
            "path": str(plan_file),
            "feature_id": feature_id
        }

    def get_plan(self, feature_id: str) -> Optional[dict]:
        """Get the implementation plan for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            feature_dir = self.completed_path / feature_id
            if not feature_dir.exists():
                return None

        plan_file = feature_dir / "plan.json"
        if not plan_file.exists():
            return None

        try:
            return json.loads(plan_file.read_text())
        except json.JSONDecodeError:
            return None

    def create_tasks(self, feature_id: str, tasks: list[dict]) -> dict:
        """Create a task list for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        now = datetime.now().isoformat()

        # Ensure each task has required fields
        processed_tasks = []
        for i, task in enumerate(tasks):
            processed_task = {
                "id": task.get("id", f"TASK-{i+1:03d}"),
                "title": task.get("title", f"Task {i+1}"),
                "description": task.get("description", ""),
                "status": "pending",
                "dependencies": task.get("dependencies", []),
                "assignee": task.get("assignee", ""),
                "notes": task.get("notes", ""),
                "created_at": now,
                "updated_at": now
            }
            processed_tasks.append(processed_task)

        # Calculate summary
        summary = {
            "total": len(processed_tasks),
            "completed": 0,
            "in_progress": 0,
            "blocked": 0,
            "pending": len(processed_tasks)
        }

        tasks_data = {
            "feature_id": feature_id,
            "summary": summary,
            "tasks": processed_tasks,
            "created_at": now,
            "updated_at": now
        }

        tasks_file = feature_dir / "tasks.json"
        tasks_file.write_text(json.dumps(tasks_data, indent=2))

        # Update spec status
        self.update_spec_status(feature_id, "ready")

        return {
            "success": True,
            "path": str(tasks_file),
            "feature_id": feature_id,
            "task_count": len(processed_tasks),
            "summary": summary
        }

    def get_tasks(self, feature_id: str) -> Optional[dict]:
        """Get all tasks for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            feature_dir = self.completed_path / feature_id
            if not feature_dir.exists():
                return None

        tasks_file = feature_dir / "tasks.json"
        if not tasks_file.exists():
            return None

        try:
            return json.loads(tasks_file.read_text())
        except json.JSONDecodeError:
            return None

    def update_task_status(self, feature_id: str, task_id: str, status: str,
                           notes: str = None) -> dict:
        """Update a task's status."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        tasks_file = feature_dir / "tasks.json"
        if not tasks_file.exists():
            return {"success": False, "error": "No tasks file found"}

        try:
            tasks_data = json.loads(tasks_file.read_text())
            now = datetime.now().isoformat()

            # Find and update the task
            task_found = False
            for task in tasks_data["tasks"]:
                if task["id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = now
                    if notes is not None:
                        task["notes"] = notes
                    task_found = True
                    break

            if not task_found:
                return {"success": False, "error": "Task not found"}

            # Recalculate summary
            summary = {"total": 0, "completed": 0, "in_progress": 0, "blocked": 0, "pending": 0}
            for task in tasks_data["tasks"]:
                summary["total"] += 1
                task_status = task.get("status", "pending")
                if task_status in summary:
                    summary[task_status] += 1

            tasks_data["summary"] = summary
            tasks_data["updated_at"] = now

            tasks_file.write_text(json.dumps(tasks_data, indent=2))

            # Update spec status based on task progress
            if summary["completed"] == summary["total"] and summary["total"] > 0:
                self.update_spec_status(feature_id, "review")

            return {
                "success": True,
                "task_id": task_id,
                "new_status": status,
                "summary": summary
            }
        except (json.JSONDecodeError, Exception) as e:
            return {"success": False, "error": str(e)}

    def add_task(self, feature_id: str, title: str, description: str = "",
                 dependencies: list[str] = None, notes: str = "") -> dict:
        """Add a new task to a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        tasks_file = feature_dir / "tasks.json"
        if not tasks_file.exists():
            return {"success": False, "error": "No tasks file found"}

        try:
            tasks_data = json.loads(tasks_file.read_text())
            now = datetime.now().isoformat()

            # Generate task ID
            existing_ids = [t["id"] for t in tasks_data["tasks"]]
            task_num = len(tasks_data["tasks"]) + 1
            task_id = f"TASK-{task_num:03d}"
            while task_id in existing_ids:
                task_num += 1
                task_id = f"TASK-{task_num:03d}"

            new_task = {
                "id": task_id,
                "title": title,
                "description": description,
                "status": "pending",
                "dependencies": dependencies or [],
                "notes": notes,
                "created_at": now,
                "updated_at": now
            }

            tasks_data["tasks"].append(new_task)

            # Update summary
            tasks_data["summary"]["total"] += 1
            tasks_data["summary"]["pending"] += 1
            tasks_data["updated_at"] = now

            tasks_file.write_text(json.dumps(tasks_data, indent=2))

            return {"success": True, "task": new_task}
        except (json.JSONDecodeError, Exception) as e:
            return {"success": False, "error": str(e)}

    def create_review(self, feature_id: str, approved: bool, feedback: list[str] = None,
                      issues: list[str] = None, recommendations: list[str] = None) -> dict:
        """Create a review document for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        now = datetime.now().isoformat()

        review = {
            "feature_id": feature_id,
            "approved": approved,
            "feedback": feedback or [],
            "issues": issues or [],
            "recommendations": recommendations or [],
            "reviewed_at": now
        }

        review_file = feature_dir / "review.json"
        review_file.write_text(json.dumps(review, indent=2))

        # Update spec status
        if approved:
            self.update_spec_status(feature_id, "completed")

        return {
            "success": True,
            "path": str(review_file),
            "approved": approved
        }

    def get_review(self, feature_id: str) -> Optional[dict]:
        """Get the review for a feature."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            feature_dir = self.completed_path / feature_id
            if not feature_dir.exists():
                return None

        review_file = feature_dir / "review.json"
        if not review_file.exists():
            return None

        try:
            return json.loads(review_file.read_text())
        except json.JSONDecodeError:
            return None

    def complete_feature(self, feature_id: str) -> dict:
        """Move a feature to completed status."""
        active_dir = self.active_path / feature_id
        if not active_dir.exists():
            return {"success": False, "error": "Feature not found in active"}

        completed_dir = self.completed_path / feature_id

        # Check if already completed
        if completed_dir.exists():
            return {"success": False, "error": "Feature already completed"}

        # Move the feature directory
        active_dir.rename(completed_dir)

        # Update spec status
        spec_file = completed_dir / "spec.json"
        if spec_file.exists():
            try:
                spec = json.loads(spec_file.read_text())
                spec["status"] = "completed"
                spec["updated_at"] = datetime.now().isoformat()
                spec_file.write_text(json.dumps(spec, indent=2))
            except (json.JSONDecodeError, Exception):
                pass

        return {
            "success": True,
            "new_path": str(completed_dir),
            "feature_id": feature_id
        }

    def get_current_feature(self) -> Optional[dict]:
        """Get the currently active feature (most recently updated)."""
        if not self.active_path.exists():
            return None

        most_recent = None
        most_recent_time = ""

        for feature_dir in self.active_path.iterdir():
            if feature_dir.is_dir():
                spec_file = feature_dir / "spec.json"
                if spec_file.exists():
                    try:
                        spec = json.loads(spec_file.read_text())
                        updated = spec.get("updated_at", "")
                        if updated > most_recent_time:
                            most_recent_time = updated
                            most_recent = feature_dir.name
                    except (json.JSONDecodeError, Exception):
                        pass

        if most_recent:
            return self.get_feature(most_recent)
        return None

    def delete_feature(self, feature_id: str) -> dict:
        """Delete a feature (only if in draft status)."""
        feature_dir = self.active_path / feature_id
        if not feature_dir.exists():
            return {"success": False, "error": "Feature not found"}

        # Check status
        spec_file = feature_dir / "spec.json"
        if spec_file.exists():
            try:
                spec = json.loads(spec_file.read_text())
                if spec.get("status") not in ["draft", "planning"]:
                    return {"success": False, "error": "Cannot delete feature that is not in draft/planning status"}
            except (json.JSONDecodeError, Exception):
                pass

        # Delete all files in the directory
        import shutil
        shutil.rmtree(feature_dir)

        return {"success": True, "deleted": feature_id}

    def export_feature(self, feature_id: str) -> Optional[str]:
        """Export a feature as a JSON string."""
        feature = self.get_feature(feature_id)
        if not feature:
            return None
        return json.dumps(feature, indent=2)

    def import_feature(self, feature_data: str) -> dict:
        """Import a feature from JSON string."""
        try:
            data = json.loads(feature_data)

            # Extract spec
            spec = data.get("spec", {})
            feature_id = spec.get("id")
            if not feature_id:
                return {"success": False, "error": "No feature ID in spec"}

            # Create feature directory
            feature_dir = self.active_path / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)

            # Write spec
            spec["updated_at"] = datetime.now().isoformat()
            (feature_dir / "spec.json").write_text(json.dumps(spec, indent=2))

            # Write plan if present
            if "plan" in data:
                (feature_dir / "plan.json").write_text(json.dumps(data["plan"], indent=2))

            # Write tasks if present
            if "tasks" in data:
                (feature_dir / "tasks.json").write_text(json.dumps(data["tasks"], indent=2))

            # Write review if present
            if "review" in data:
                (feature_dir / "review.json").write_text(json.dumps(data["review"], indent=2))

            return {"success": True, "imported": feature_id}
        except (json.JSONDecodeError, Exception) as e:
            return {"success": False, "error": str(e)}