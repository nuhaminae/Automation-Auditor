# src/tools/repo_tools.py
# RepoInvestigator (detective) tools for cloning and analysing GitHub repositories.

import ast
import os
import subprocess
import tempfile
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file at import time
load_dotenv()


class RepoError(Exception):
    """Custom exception for repository analysis errors."""


def get_github_token() -> Optional[str]:
    """
    Retrieve GitHub token from environment variables.

    Returns:
        str or None: GitHub token if present, else None.
    """
    return os.getenv("GITHUB_TOKEN")


def clone_repository(repo_url: str) -> str:
    """
    Clone a GitHub repository into a sandboxed temporary directory.

    Args:
        repo_url (str): The URL of the repository to clone.

    Returns:
        str: Path to the cloned repository inside a temporary directory.

    Notes:
        - Uses tempfile.mkdtemp for isolation.
        - If GITHUB_TOKEN is set, it is injected into the HTTPS URL for private repos.
        - Raises RepoError if git clone fails.
    """
    temp_dir = tempfile.mkdtemp()
    token = get_github_token()
    try:
        if token and repo_url.startswith("https://"):
            # Insert token into HTTPS URL (avoid logging this!)
            repo_url = repo_url.replace("https://", f"https://{token}@")
            print("Using GitHub token for authentication (not shown in logs).")
        subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RepoError(
            f"Failed to clone repository {repo_url}: {e.stderr.decode()}"
        ) from e
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
        - Raises RepoError if git log fails.
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--pretty=format:%H|%s|%cI", "--reverse"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RepoError(f"Failed to extract git history: {e.stderr}") from e

    commits = []
    for line in result.stdout.splitlines():
        try:
            commit_hash, message, timestamp = line.split("|", 2)
            commits.append(
                {"hash": commit_hash, "message": message, "timestamp": timestamp}
            )
        except ValueError:
            continue
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
        - Raises RepoError if the file cannot be read or parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError) as e:
        raise RepoError(f"Failed to analyse graph structure in {file_path}: {e}") from e

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


def fetch_repo_metadata(repo_full_name: str) -> dict:
    """
    Fetch repository metadata from GitHub API.

    Args:
        repo_full_name (str): e.g., "owner/repo".

    Returns:
        dict: JSON metadata including stars, forks, issues, license, etc.

    Notes:
        - Requires authentication for private repos or higher rate limits.
        - Raises RepoError if API call fails.
    """
    token = get_github_token()
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/repos/{repo_full_name}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RepoError(f"Failed to fetch metadata: {resp.text}")
    return resp.json()


def fetch_commit_details(repo_full_name: str, sha: str) -> dict:
    """
    Fetch detailed commit info from GitHub API.

    Args:
        repo_full_name (str): e.g., "owner/repo".
        sha (str): Commit hash.

    Returns:
        dict: JSON commit details including author, files changed, additions/deletions.

    Notes:
        - Useful for forensic enrichment beyond local git log.
        - Raises RepoError if API call fails.
    """
    token = get_github_token()
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/repos/{repo_full_name}/commits/{sha}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RepoError(f"Failed to fetch commit {sha}: {resp.text}")
    return resp.json()
