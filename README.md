# Automation Auditor

[![CI](https://github.com/nuhaminae/Automation-Auditor/actions/workflows/CI.yml/badge.svg)](https://github.com/nuhaminae/Automation-Auditor/actions/workflows/CI.yml)
![Black Formatting](https://img.shields.io/badge/code%20style-black-000000.svg)
![isort Imports](https://img.shields.io/badge/imports-isort-blue.svg)
![Flake8 Lint](https://img.shields.io/badge/lint-flake8-yellow.svg)

## Project Overview

**Automation Auditor** is an AI "courtroom" designed to evaluate the quality of automation, pass judgement, and provide actionable feedback for improvement. It uses a structured framework to analyse automation scripts, identify strengths and weaknesses, and offer recommendations for enhancement. It has three layers: Detectives (data gathering), Judges (evaluation), and Chief Justice (synthesis).

This interim submission demonstrates the Detective Layer, with RepoInvestigator and DocAnalyst running in parallel (fan‑out) and converging at EvidenceAggregator (fan‑in). Judges and Chief Justice nodes will be added in the final submission.

---

## Table of Contents

- [Key Features](#key-features)  
- [Project Structure](#project-structure)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Project Status](#project-status)  

---

## Key Features

- **Detective Nodes**  
  - **RepoInvestigator**: Clones the repository, extracts commit history, and analyses orchestration in `src/graph.py`.  
  - **DocAnalyst**: Ingests the PDF report, chunks text, searches for rubric concepts (Fan‑In/Fan‑Out, Dialectical Synthesis), and cross‑references file paths.  

- **Evidence Aggregation**  
  - Evidence from both detectives is collected at the **EvidenceAggregator** node.  
  - This demonstrates **fan‑out/fan‑in orchestration**, a core rubric requirement.  

- **Partial StateGraph**  
  - Only Detectives + EvidenceAggregator are wired.  
  - Judges and Chief Justice will be added in the final submission.  

---

## Project Structure

```bash
AUTOMATION-AUDITOR/
├── .github/                         # GitHub metadata
│   └── workflows/                   # CI/CD workflows
│   │   └── CI.yml
│   └── copilot-instructions.md      # MCP instructions for GitHub Copilot
├── .venv/                           # Virtual environment (not committed)
├── .vscode/
│   └── mcp.json
├── reports/
│   └── interim_report.pdf           # Interim report document
├── src/                             # Script
│   ├── nodes/
│   │   └── detectives.py            # Node definitions for detectiive layer
│   ├── tools/
│   │   ├── doc_tools.py             # Tools for document processing
│   │   └── repo_tools.py            # Tools for repository analysis
│   ├── graph.py
│   └── main.py
├── tests/                           # Test suite
│   └── test_dummy.py                # Placeholder test file
├── .env                             # Environment variables (not committed)
├── .env.example                     # Example environment variables
├── .flake8                          # Flake8 configuration
├── .gitignore                       # Git ignore rules 
├── .pre-commit-config.yaml          # Pre-commit hooks configuration  
├── .yamllint.yml                    # YAML linting configuration
├── format.ps1                       # PowerShell script for code formatting
├── pyproject.toml                   # Dependency and tool configuration
├── README.md                        # Project overview
└── uv.lock                          # Dependency lock file
```

---

## Installation

### Prerequisites

- Python 3.9+  
- Git  

### Setup

```bash
# Clone repo
git clone https://github.com/nuhaminae/Automation-Auditor.git
cd Automation-Auditor

# Install dependencies
pip install uv
uv sync

```

---

## Usage

Run the partial audit workflow with:

```bash
python -m src/main.py <repo_url> <pdf_path>
```

- **Input**:  
  - `repo_url`: GitHub repository to audit  
  - `pdf_path`: Path to the PDF report  

- **Output**:  
  - A **partial report** containing evidence collected by Detectives.  
  - Judges and Chief Justice synthesis will be added in the final submission.  

---

## Project Status

The current submission demonstrates Detectives wired in parallel (fan‑out) and converging at EvidenceAggregator (fan‑in).

``` mermaid
graph TD
    A[RepoInvestigator] --> C[EvidenceAggregator]
    B[DocAnalyst] --> C[EvidenceAggregator]
```

The project is still on going. Check the [commit history](https://github.com/nuhaminae/Automation-Auditor/).
