# tests/test_repo_tools.py
# run with: pytest tests/test_repo_tools.py
# Tests for RepoInvestigator tools in src/tools/repo_tools.py

import os
import subprocess

import pytest

from src.tools import repo_tools


def test_clone_repository_success(monkeypatch):
    """Ensure clone_repository calls git clone and returns a temp dir."""
    called = {}

    def fake_run(cmd, check, stdout, stderr):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    repo_url = "https://github.com/example/repo.git"
    temp_dir = repo_tools.clone_repository(repo_url)

    assert os.path.isdir(temp_dir)
    assert "git" in called["cmd"]
    assert repo_url in called["cmd"]


def test_clone_repository_error(monkeypatch):
    """Ensure clone_repository raises RepoError on failure."""

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr=b"fatal: repo not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(repo_tools.RepoError) as excinfo:
        repo_tools.clone_repository("https://github.com/invalid/repo.git")
    assert "Failed to clone repository" in str(excinfo.value)


def test_extract_git_history_success(monkeypatch):
    """Ensure extract_git_history parses git log output correctly."""
    fake_output = (
        "abc123|Initial commit|2024-01-01T00:00:00Z\n"
        "def456|Add feature|2024-01-02T00:00:00Z"
    )

    def fake_run(cmd, check, stdout, stderr, text):
        return subprocess.CompletedProcess(cmd, 0, fake_output, "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    commits = repo_tools.extract_git_history("/fake/path")
    assert len(commits) == 2
    assert commits[0]["hash"] == "abc123"
    assert commits[1]["message"] == "Add feature"


def test_extract_git_history_error(monkeypatch):
    """Ensure extract_git_history raises RepoError on failure."""

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="fatal: not a git repo")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(repo_tools.RepoError) as excinfo:
        repo_tools.extract_git_history("/fake/path")
    assert "Failed to extract git history" in str(excinfo.value)


def test_analyse_graph_structure_success(tmp_path):
    """Ensure analyse_graph_structure detects orchestration patterns."""
    code = """
from langgraph import StateGraph

def build_graph():
    g = StateGraph()
    g.add_edge("A", "B")
    x = g.ior
    return g
"""
    file_path = tmp_path / "graph.py"
    file_path.write_text(code)

    result = repo_tools.analyse_graph_structure(str(file_path))
    assert result["stategraph_found"] is True
    assert result["parallel_edges"] is True
    assert result["reducers_used"] is True


def test_analyse_graph_structure_error(tmp_path):
    """Ensure analyse_graph_structure raises RepoError on bad file."""
    file_path = tmp_path / "bad_graph.py"
    file_path.write_text("this is not valid python")

    with pytest.raises(repo_tools.RepoError) as excinfo:
        repo_tools.analyse_graph_structure(str(file_path))
    assert "Failed to analyse graph structure" in str(excinfo.value)
