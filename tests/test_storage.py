"""Tests for spec-coding-mcp storage module."""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from spec_coding.storage import SpecStorage


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)


@pytest.fixture
def storage(temp_dir):
    """Create a storage instance with temporary directory."""
    return SpecStorage(base_path=os.path.join(temp_dir, "specs"))


class TestSpecStorage:
    """Tests for SpecStorage class."""

    def test_init_structure(self, storage):
        """Test initializing the directory structure."""
        result = storage.init_structure()

        assert result["status"] == "initialized"
        assert len(result["created"]) == 4  # base, active, completed, templates
        assert storage.base_path.exists()
        assert storage.active_path.exists()
        assert storage.completed_path.exists()
        assert storage.templates_path.exists()

    def test_create_feature(self, storage):
        """Test creating a feature specification."""
        storage.init_structure()

        result = storage.create_feature(
            feature_id="001-test-feature",
            title="Test Feature",
            description="A test feature for unit tests",
            tech_stack=["Python"],
            constraints=["Must be fast"]
        )

        assert result["status"] == "created"
        assert result["id"] == "001-test-feature"

        # Check files exist
        feature_dir = storage.active_path / "001-test-feature"
        assert feature_dir.exists()
        assert (feature_dir / "spec.json").exists()

    def test_get_feature(self, storage):
        """Test retrieving a feature."""
        storage.init_structure()
        storage.create_feature(
            feature_id="001-test",
            title="Test",
            description="Test feature"
        )

        feature = storage.get_feature("001-test")

        assert feature is not None
        assert feature["id"] == "001-test"
        assert feature["spec"]["title"] == "Test"
        assert "plan" in feature
        assert "tasks" in feature

    def test_list_features(self, storage):
        """Test listing features."""
        storage.init_structure()
        storage.create_feature("001-first", "First", "First feature")
        storage.create_feature("002-second", "Second", "Second feature")

        features = storage.list_features()

        assert len(features) == 2
        titles = [f["title"] for f in features]
        assert "First" in titles
        assert "Second" in titles

    def test_add_requirement(self, storage):
        """Test adding a requirement."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")

        result = storage.add_requirement(
            feature_id="001-test",
            req_id="REQ-001",
            title="Login",
            description="User can log in",
            priority="high",
            acceptance_criteria=["Valid credentials accepted", "Invalid credentials rejected"]
        )

        assert result["success"]

        feature = storage.get_feature("001-test")
        assert len(feature["spec"]["requirements"]) == 1
        assert feature["spec"]["requirements"][0]["title"] == "Login"

    def test_create_plan(self, storage):
        """Test creating an implementation plan."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")

        result = storage.create_plan(
            feature_id="001-test",
            overview="Test implementation",
            architecture="Simple architecture",
            components=[
                {"name": "Core", "purpose": "Main logic", "files": ["core.py"]}
            ],
            risks=[
                {"risk": "Complexity", "likelihood": "Low", "impact": "Medium", "mitigation": "Keep it simple"}
            ]
        )

        assert result["success"]

        plan = storage.get_plan("001-test")
        assert plan["overview"] == "Test implementation"
        assert len(plan["components"]) == 1

    def test_create_tasks(self, storage):
        """Test creating tasks."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")

        result = storage.create_tasks(
            feature_id="001-test",
            tasks=[
                {"id": "TASK-001", "title": "Setup", "description": "Initial setup"},
                {"id": "TASK-002", "title": "Implement", "description": "Core implementation", "dependencies": ["TASK-001"]}
            ]
        )

        assert result["success"]
        assert result["task_count"] == 2

        tasks = storage.get_tasks("001-test")
        assert len(tasks["tasks"]) == 2
        assert tasks["summary"]["total"] == 2

    def test_update_task_status(self, storage):
        """Test updating task status."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")
        storage.create_tasks(
            feature_id="001-test",
            tasks=[
                {"id": "TASK-001", "title": "Setup", "description": "Initial setup"}
            ]
        )

        result = storage.update_task_status(
            feature_id="001-test",
            task_id="TASK-001",
            status="in_progress"
        )

        assert result["success"]
        assert result["new_status"] == "in_progress"

        tasks = storage.get_tasks("001-test")
        assert tasks["tasks"][0]["status"] == "in_progress"

    def test_create_review(self, storage):
        """Test creating a review."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")

        result = storage.create_review(
            feature_id="001-test",
            approved=True,
            feedback=["Good work"],
            issues=[],
            recommendations=["Add more tests"]
        )

        assert result["success"]
        assert result["approved"]

        review = storage.get_review("001-test")
        assert review["approved"] == True
        assert "Good work" in review["feedback"]

    def test_complete_feature(self, storage):
        """Test completing and archiving a feature."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")
        storage.update_spec_status("001-test", "review")

        result = storage.complete_feature("001-test")

        assert result["success"]

        # Feature should be in completed
        feature = storage.get_feature("001-test")
        assert feature["type"] == "completed"
        assert feature["spec"]["status"] == "completed"

    def test_export_import(self, storage):
        """Test exporting and importing features."""
        storage.init_structure()
        storage.create_feature("001-test", "Test", "Test feature")
        storage.add_requirement(
            feature_id="001-test",
            req_id="REQ-001",
            title="Req",
            description="A requirement"
        )

        # Export
        exported = storage.export_feature("001-test")
        assert exported is not None
        data = json.loads(exported)

        # Delete and re-import
        storage.delete_feature("001-test")
        assert storage.get_feature("001-test") is None

        # Import
        result = storage.import_feature(exported)
        assert result["success"]

        # Verify
        feature = storage.get_feature("001-test")
        assert feature is not None
        assert feature["spec"]["title"] == "Test"


class TestCompression:
    """Tests for TOON compression."""

    def test_compression_imports(self):
        """Test that compression module imports correctly."""
        from spec_coding.compression import encode, encode_compact, estimate_token_savings
        assert callable(encode)
        assert callable(encode_compact)
        assert callable(estimate_token_savings)

    def test_basic_compression(self):
        """Test basic TOON encoding."""
        from spec_coding.compression import encode, estimate_token_savings
        import json

        data = {
            "id": "001",
            "title": "Test",
            "items": [
                {"id": "1", "name": "First"},
                {"id": "2", "name": "Second"}
            ]
        }

        json_str = json.dumps(data, indent=2)
        toon_str = encode(data)

        # TOON should be shorter
        assert len(toon_str) < len(json_str)

        # Should have token savings
        savings = estimate_token_savings(json_str, toon_str)
        assert savings["percent_reduction"] > 20  # At least 20% reduction

    def test_compact_format(self):
        """Test compact TOON format."""
        from spec_coding.compression import encode_compact

        data = {"name": "Test", "count": 42}
        result = encode_compact(data)

        # Compact format uses tabs
        assert "name:" in result
        assert "Test" in result
        assert "count:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])