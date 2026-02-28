# src/main.py
import json
import os
import sys
import requests  # to support loading rubric/report from HTTPS
import tempfile  # to handle temporary files safely

from dotenv import load_dotenv

# --- Load environment variables from .env ---
load_dotenv()

# --- Disable LangSmith tracing explicitly (otherwise it will use .env)---
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ.pop("LANGCHAIN_API_KEY", None)
os.environ.pop("LANGSMITH_WORKSPACE_ID", None)

from src.graph import build_auditor_graph
from src.nodes.justice import format_audit_report
from src.state import AgentState


def load_json_source(path: str) -> dict:
    """
    Load JSON either from a local file path or from a remote HTTPS URL.
    This allows rubric files to be read directly from GitHub raw links.
    """
    if path.startswith("http"):
        resp = requests.get(path)
        resp.raise_for_status()
        return resp.json()
    else:
        with open(path, "r") as f:
            return json.load(f)


def ensure_local_pdf(path: str) -> str:
    """
    Ensure the PDF is available locally.
    If path is a URL, download it to a temporary file and return that path.
    If path is already local, just return it.
    """
    if path.startswith("http"):
        resp = requests.get(path)
        resp.raise_for_status()
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(resp.content)
        return tmp_path
    return path


def main():
    """
    Entry point for the Automaton Auditor.
    Expects at least 3 arguments:
        repo_url   - GitHub repository URL to evaluate
        pdf_path   - Path to interim report PDF (local or remote)
        rubric_path- Path or URL to rubric JSON
        output_path- Optional path to save final verdict JSON
    """
    if len(sys.argv) < 4:
        print(
            "Usage: python -m src.main <repo_url> \n"
            "<pdf_path> <rubric_path> [output_path]"
        )
        sys.exit(1)

    repo_url = sys.argv[1]
    pdf_arg = sys.argv[2]
    rubric_path = sys.argv[3]
    output_path = sys.argv[4] if len(sys.argv) > 4 else None

    # --- Handle PDF: download if remote, otherwise use local path ---
    pdf_path = ensure_local_pdf(pdf_arg)
    temp_files = []
    if pdf_arg.startswith("http"):
        temp_files.append(pdf_path)

    # --- Load rubric dimensions from local file or HTTPS URL ---
    rubric_dimensions = []
    if rubric_path:
        rubric_json = load_json_source(rubric_path)
        # assume rubric_json has a "dimensions" key
        rubric_dimensions = rubric_json.get("dimensions", rubric_json)

    # --- Build initial agent state ---
    state = AgentState(
        repo_url=repo_url,
        pdf_path=pdf_path,
        rubric_dimensions=rubric_dimensions,
        evidences={},
        opinions=[],
        final_report=None,
    )

    # --- Load and compile the auditor graph ---
    graph = build_auditor_graph()
    app = graph.compile()

    # --- Run the app ---
    final_state = app.invoke(state.model_dump())
    report = final_state["final_report"]

    # --- Print Markdown version to console ---
    print(format_audit_report(report))

    # --- Optionally save JSON verdict if output_path is provided ---
    if output_path:
        verdict = {
            "repo_url": state.repo_url,
            "executive_summary": report.executive_summary,
            "overall_score": report.overall_score,
            "scoring_note": "Judge scores are on a 0 to 10 scale. Final scores are normalised to a 1 to 5 scale.",
            "criteria": [
                {
                    "dimension_id": cr.dimension_id,
                    "dimension_name": cr.dimension_name,
                    "final_score_label": f"{cr.final_score} out of 5",
                    "judge_opinions": [
                        {
                            "judge": op.judge,
                            "criterion_id": op.criterion_id,
                            "score_label": f"{op.score} out of 10",
                            "argument": op.argument,
                            "cited_evidence": op.cited_evidence,
                        }
                        for op in cr.judge_opinions
                    ],
                    # split remediation string into list of lines
                    "remediation": cr.remediation.strip().split("\n"),
                    "dissent_summary": cr.dissent_summary,
                }
                for cr in report.criteria
            ],
            "remediation_plan": report.remediation_plan,
            "evidences": {
                k: [ev.model_dump() for ev in v]
                for k, v in final_state["evidences"].items()
            },
        }
        with open(output_path, "w") as f:
            json.dump(verdict, f, indent=2)

    # --- Cleanup temporary files (PDFs downloaded from URLs) ---
    for tmp in temp_files:
        try:
            os.remove(tmp)
        except OSError:
            pass


if __name__ == "__main__":
    main()
