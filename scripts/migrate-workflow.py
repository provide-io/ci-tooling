#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Migration script to help convert existing CI workflows to use shared actions.

Usage:
    python scripts/migrate-workflow.py <workflow-file>
    python scripts/migrate-workflow.py --analyze /path/to/project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


class WorkflowMigrator:
    """Migrates existing GitHub workflows to use shared actions."""

    def __init__(self) -> None:
        self.shared_actions = {
            "setup-python": "provide-io/ci-tooling/actions/setup-python-env@v0",
            "python-quality": "provide-io/ci-tooling/actions/python-quality@v0",
            "python-test": "provide-io/ci-tooling/actions/python-test@v0",
            "python-security": "provide-io/ci-tooling/actions/python-security@v0",
            "python-build": "provide-io/ci-tooling/actions/python-build@v0",
            "python-release": "provide-io/ci-tooling/actions/python-release@v0",
        }

        self.reusable_workflows = {
            "python-ci": "provide-io/ci-tooling/workflows/python-ci.yml@v0",
            "python-release": "provide-io/ci-tooling/workflows/python-release.yml@v0",
        }

    def analyze_project(self, project_path: str) -> dict[str, Any]:
        """Analyze a project to suggest migration strategy."""
        project_path = Path(project_path)
        analysis = {
            "project_type": "unknown",
            "workflows": [],
            "migration_suggestions": [],
            "complexity": "low",
        }

        # Check project type
        if (project_path / "pyproject.toml").exists():
            analysis["project_type"] = "python"
        elif (project_path / "setup.py").exists():
            analysis["project_type"] = "python-legacy"
        elif (project_path / "main.tf").exists():
            analysis["project_type"] = "terraform"

        # Find existing workflows
        workflows_dir = project_path / ".github" / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                try:
                    with workflow_file.open() as f:
                        workflow_data = yaml.safe_load(f)

                    workflow_analysis = self._analyze_workflow(workflow_data)
                    workflow_analysis["file"] = str(workflow_file)
                    analysis["workflows"].append(workflow_analysis)
                except Exception as e:
                    print(f"Warning: Could not parse {workflow_file}: {e}")

        # Generate suggestions
        analysis["migration_suggestions"] = self._generate_suggestions(analysis)
        analysis["complexity"] = self._assess_complexity(analysis)

        return analysis

    def _analyze_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single workflow file."""
        analysis = {
            "name": workflow_data.get("name", "Unknown"),
            "triggers": list(workflow_data.get("on", {}).keys()),
            "jobs": [],
            "patterns": [],
            "migration_potential": "low",
        }

        jobs = workflow_data.get("jobs", {})
        for job_name, job_data in jobs.items():
            job_analysis = self._analyze_job(job_name, job_data)
            analysis["jobs"].append(job_analysis)

        # Detect patterns
        analysis["patterns"] = self._detect_patterns(analysis["jobs"])
        analysis["migration_potential"] = self._assess_migration_potential(analysis)

        return analysis

    def _analyze_job(self, job_name: str, job_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single job."""
        steps = job_data.get("steps", [])

        job_analysis = {
            "name": job_name,
            "runner": job_data.get("runs-on", "unknown"),
            "step_count": len(steps),
            "patterns": [],
            "tools_used": [],
        }

        # Analyze steps
        for step in steps:
            if isinstance(step, dict):
                self._detect_tools_in_step(step, job_analysis["tools_used"])

        # Detect patterns based on tools
        job_analysis["patterns"] = self._detect_job_patterns(set(job_analysis["tools_used"]))

        return job_analysis

    def _detect_tools_in_step(self, step: dict[str, Any], tools_used: list[str]) -> None:
        """Detect tools used in a workflow step."""
        step_name = step.get("name", "")
        step_uses = step.get("uses", "")
        step_run = step.get("run", "")

        if "python" in step_name.lower() or "setup-python" in step_uses:
            tools_used.append("python")
        if "uv" in step_run or "uv" in step_name.lower():
            tools_used.append("uv")
        if "ruff" in step_run or "ruff" in step_name.lower():
            tools_used.append("ruff")
        if "mypy" in step_run or "mypy" in step_name.lower():
            tools_used.append("mypy")
        if "pytest" in step_run or "test" in step_name.lower():
            tools_used.append("pytest")
        if "bandit" in step_run or "safety" in step_run or "security" in step_name.lower():
            tools_used.append("security")

    def _detect_job_patterns(self, tools: set[str]) -> list[str]:
        """Detect patterns based on tools used."""
        patterns = []
        if {"python", "uv"} <= tools:
            patterns.append("python-setup")
        if {"ruff"} <= tools or {"mypy"} <= tools:
            patterns.append("python-quality")
        if {"pytest"} <= tools:
            patterns.append("python-test")
        if any(tool in tools for tool in ["bandit", "safety", "security"]):
            patterns.append("python-security")
        return patterns

    def _detect_patterns(self, jobs: list[dict[str, Any]]) -> list[str]:
        """Detect workflow-level patterns."""
        patterns = []
        all_tools = set()
        all_patterns = set()

        for job in jobs:
            all_tools.update(job["tools_used"])
            all_patterns.update(job["patterns"])

        if "python-setup" in all_patterns and "python-test" in all_patterns:
            patterns.append("standard-ci")
        if "python-quality" in all_patterns:
            patterns.append("quality-focused")
        if "python-security" in all_patterns:
            patterns.append("security-focused")

        return patterns

    def _assess_migration_potential(self, workflow_analysis: dict[str, Any]) -> str:
        """Assess how suitable a workflow is for migration."""
        patterns = workflow_analysis["patterns"]
        job_count = len(workflow_analysis["jobs"])

        if "standard-ci" in patterns and job_count <= 3:
            return "high"
        elif any(p in patterns for p in ["quality-focused", "security-focused"]):
            return "medium"
        else:
            return "low"

    def _assess_complexity(self, analysis: dict[str, Any]) -> str:
        """Assess overall project complexity for migration."""
        workflow_count = len(analysis["workflows"])
        high_potential = sum(1 for w in analysis["workflows"] if w["migration_potential"] == "high")

        if workflow_count <= 2 and high_potential >= 1:
            return "low"
        elif workflow_count <= 5 and high_potential >= workflow_count // 2:
            return "medium"
        else:
            return "high"

    def _generate_suggestions(self, analysis: dict[str, Any]) -> list[str]:
        """Generate migration suggestions."""
        suggestions = []

        if analysis["project_type"] == "python":
            suggestions.append("✅ Python project detected - good candidate for ci-tooling")

        complexity = analysis["complexity"]
        if complexity == "low":
            suggestions.append("🚀 Low complexity - recommend using reusable workflows")
            suggestions.append("📝 Suggested approach: Replace with python-ci.yml workflow")
        elif complexity == "medium":
            suggestions.append("🔧 Medium complexity - recommend gradual migration with individual actions")
            suggestions.append("📝 Start with setup-python-env and python-quality actions")
        else:
            suggestions.append("⚠️ High complexity - recommend careful step-by-step migration")
            suggestions.append("📝 Begin with single workflow, then expand")

        # Specific action suggestions
        for workflow in analysis["workflows"]:
            if "standard-ci" in workflow["patterns"]:
                suggestions.append(f"🔄 {workflow['name']}: Replace with python-ci.yml reusable workflow")
            elif "python-setup" in workflow["patterns"]:
                suggestions.append(f"🐍 {workflow['name']}: Use setup-python-env action")

        return suggestions

    def generate_migrated_workflow(self, original_file: str, strategy: str = "reusable") -> str:
        """Generate a migrated workflow file."""
        with Path(original_file).open() as f:
            original_data = yaml.safe_load(f)

        if strategy == "reusable":
            return self._generate_reusable_workflow(original_data)
        else:
            return self._generate_action_based_workflow(original_data)

    def _generate_reusable_workflow(self, original_data: dict[str, Any]) -> str:
        """Generate workflow using reusable workflows."""
        workflow_name = original_data.get("name", "CI")
        triggers = original_data.get("on", {"push": {"branches": ["main"]}, "pull_request": {}})

        migrated = {
            "name": workflow_name,
            "on": triggers,
            "jobs": {
                "ci": {
                    "uses": self.reusable_workflows["python-ci"],
                    "with": {
                        "python-version": "3.11",
                        "matrix-testing": True,
                        "run-security": True,
                    },
                    "secrets": {"CODECOV_TOKEN": "${{ secrets.CODECOV_TOKEN }}"},
                }
            },
        }

        return yaml.dump(migrated, default_flow_style=False, sort_keys=False)

    def _generate_action_based_workflow(self, original_data: dict[str, Any]) -> str:
        """Generate workflow using individual actions."""
        workflow_name = original_data.get("name", "CI")
        triggers = original_data.get("on", {"push": {"branches": ["main"]}, "pull_request": {}})

        migrated = {
            "name": workflow_name,
            "on": triggers,
            "jobs": {
                "quality": {
                    "name": "🔧 Code Quality",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "uses": self.shared_actions["setup-python"],
                            "with": {"python-version": "3.11", "uv-version": "0.7.8"},
                        },
                        {"uses": self.shared_actions["python-quality"]},
                    ],
                },
                "test": {
                    "name": "🧪 Tests",
                    "needs": "quality",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "uses": self.shared_actions["setup-python"],
                            "with": {"python-version": "3.11", "uv-version": "0.7.8"},
                        },
                        {
                            "uses": self.shared_actions["python-test"],
                            "with": {"coverage-threshold": 80},
                        },
                    ],
                },
            },
        }

        return yaml.dump(migrated, default_flow_style=False, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate GitHub workflows to use shared actions")
    parser.add_argument("target", help="Workflow file or project directory to analyze")
    parser.add_argument("--analyze", action="store_true", help="Analyze project and suggest migration")
    parser.add_argument(
        "--strategy",
        choices=["reusable", "actions"],
        default="reusable",
        help="Migration strategy: reusable workflows or individual actions",
    )
    parser.add_argument("--output", help="Output file for migrated workflow")

    args = parser.parse_args()

    migrator = WorkflowMigrator()

    if args.analyze or Path(args.target).is_dir():
        # Analyze project
        analysis = migrator.analyze_project(args.target)

        print(f"📊 Project Analysis: {args.target}")
        print(f"Project Type: {analysis['project_type']}")
        print(f"Complexity: {analysis['complexity']}")
        print(f"Workflows Found: {len(analysis['workflows'])}")
        print()

        print("🔍 Workflows:")
        for workflow in analysis["workflows"]:
            print(f"  • {workflow['name']} - {workflow['migration_potential']} migration potential")
            print(f"    Patterns: {', '.join(workflow['patterns'])}")
        print()

        print("💡 Migration Suggestions:")
        for suggestion in analysis["migration_suggestions"]:
            print(f"  {suggestion}")

    else:
        # Migrate specific workflow
        if not Path(args.target).is_file():
            print(f"Error: {args.target} is not a file")
            sys.exit(1)

        migrated_content = migrator.generate_migrated_workflow(args.target, args.strategy)

        if args.output:
            with Path(args.output).open("w") as f:
                f.write(migrated_content)
            print(f"✅ Migrated workflow written to {args.output}")
        else:
            print("📝 Migrated workflow:")
            print("=" * 50)
            print(migrated_content)


if __name__ == "__main__":
    main()
