# src/tools/repo_tools.py
# RepoInvestigator (detective) tools for cloning and analysing GitHub repositories.

import ast
import subprocess
import tempfile
from typing import Dict, List


def clone_repository(repo_url: str) -> str:
    """
    Clone a GitHub repository into a sandboxed temporary directory.

    Args:
        repo_url (str): The URL of the repository to clone.

    Returns:
        str: Path to the cloned repository inside a temporary directory.

    Notes:
        - Uses tempfile.TemporaryDirectory for isolation.
        - Raises subprocess.CalledProcessError if git clone fails.
    """
    # Create a temporary directory for cloning
    temp_dir = tempfile.mkdtemp()
    # Run cloned repository using subprocess
    subprocess.run(
        ["git", "clone", repo_url, temp_dir],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return temp_dir


def extract_git_history(repo_path: str) -> List[Dict[str, str]]:
    """
    Extract commit history from a cloned repository.

    Args:
        repo_path (str): Path to the cloned repository.

    Returns:
        List[Dict[str, str]]: A list of commit dictionaries containing
        'hash', 'message', and 'timestamp'.

    Notes:
        - Runs 'git log --pretty=format' to capture commit metadata.
        - Useful for forensic analysis of development progression.
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "--pretty=format:%H|%s|%cI", "--reverse"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    commits = []
    for line in result.stdout.splitlines():
        commit_hash, message, timestamp = line.split("|", 2)
        commits.append(
            {"hash": commit_hash, "message": message, "timestamp": timestamp}
        )
    return commits


def analyse_graph_structure(file_path: str) -> Dict[str, bool]:
    """
    Analyse a Python file for LangGraph orchestration patterns.

    Args:
        file_path (str): Path to the Python file (e.g., src/graph.py).

    Returns:
        Dict[str, bool]: Flags indicating presence of key orchestration features:
            - 'stategraph_found': Whether StateGraph is instantiated.
            - 'parallel_edges': Whether builder.add_edge() creates fan-out branches.
            - 'reducers_used': Whether operator reducers are applied.

    Notes:
        - Uses Python's AST module for robust parsing (not regex).
        - Helps detect orchestration fraud (linear vs parallel execution).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    stategraph_found = False
    parallel_edges = False
    reducers_used = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "StateGraph":
                stategraph_found = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_edge":
                parallel_edges = True
        if isinstance(node, ast.Attribute) and node.attr in ["ior", "add"]:
            reducers_used = True

    return {
        "stategraph_found": stategraph_found,
        "parallel_edges": parallel_edges,
        "reducers_used": reducers_used,
    }
