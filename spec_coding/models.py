"""Data models for spec-driven coding - Pure Python, no Pydantic."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class FeatureStatus(Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"


@dataclass
class Task:
    """A single implementation task."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            dependencies=data.get("dependencies", []),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class AcceptanceCriteria:
    """Acceptance criteria for a feature."""
    id: str
    description: str
    met: bool = False
    notes: str = ""


@dataclass
class Requirement:
    """A functional or non-functional requirement."""
    id: str
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    category: str = "functional"  # functional, non-functional
    acceptance_criteria: list[AcceptanceCriteria] = field(default_factory=list)


@dataclass
class FeatureSpec:
    """A complete feature specification."""
    id: str
    title: str
    description: str
    status: FeatureStatus = FeatureStatus.DRAFT
    requirements: list[Requirement] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "requirements": [
                {
                    **r.__dict__,
                    "acceptance_criteria": [ac.__dict__ for ac in r.acceptance_criteria]
                }
                for r in self.requirements
            ],
            "tasks": [t.to_dict() for t in self.tasks],
            "tech_stack": self.tech_stack,
            "constraints": self.constraints,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ImplementationPlan:
    """Technical implementation plan for a feature."""
    feature_id: str
    overview: str
    architecture: str = ""
    components: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    estimated_effort: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Review:
    """Review of an implementation."""
    feature_id: str
    reviewer: str = ""
    approved: bool = False
    feedback: list[dict] = field(default_factory=list)
    issues_found: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# Helper functions for serialization

def feature_to_json(feature: FeatureSpec) -> str:
    """Convert FeatureSpec to JSON string."""
    return json.dumps(feature.to_dict(), indent=2)


def json_to_feature(data: str | dict) -> FeatureSpec:
    """Convert JSON string or dict to FeatureSpec."""
    if isinstance(data, str):
        data = json.loads(data)

    requirements = []
    for r in data.get("requirements", []):
        criteria = [
            AcceptanceCriteria(
                id=ac["id"],
                description=ac["description"],
                met=ac.get("met", False),
                notes=ac.get("notes", "")
            )
            for ac in r.get("acceptance_criteria", [])
        ]
        requirements.append(Requirement(
            id=r["id"],
            title=r["title"],
            description=r["description"],
            priority=r.get("priority", "medium"),
            category=r.get("category", "functional"),
            acceptance_criteria=criteria,
        ))

    tasks = [Task.from_dict(t) for t in data.get("tasks", [])]

    return FeatureSpec(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        status=FeatureStatus(data.get("status", "draft")),
        requirements=requirements,
        tasks=tasks,
        tech_stack=data.get("tech_stack", []),
        constraints=data.get("constraints", []),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )