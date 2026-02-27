# src/main.py
import os
import sys
import json
from dotenv import load_dotenv

# --- Disable LangSmith tracing explicitly ---
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ.pop("LANGCHAIN_API_KEY", None)
os.environ.pop("LANGSMITH_WORKSPACE_ID", None)

# Load environment variables
load_dotenv()

from src.graph import build_auditor_graph
from src.state import AgentState
from src.nodes.justice import format_audit_report

def main():
    # Expect at least 3 arguments: repo_url, pdf_path, rubric_path
    if len(sys.argv) < 4:
        print("Usage: python -m src.main <repo_url> <pdf_path> <rubric_path> [output_path]")
        sys.exit(1)

    repo_url = sys.argv[1]
    pdf_path = sys.argv[2]
    rubric_path = sys.argv[3]
    output_path = sys.argv[4] if len(sys.argv) > 4 else None

    # Load rubric dimensions if provided
    rubric_dimensions = []
    if rubric_path:
        with open(rubric_path, "r") as f:
            rubric_json = json.load(f)
            # assume rubric_json has a "dimensions" key
            rubric_dimensions = rubric_json.get("dimensions", rubric_json)

    # Build initial state
    state = AgentState(
        repo_url=repo_url,
        pdf_path=pdf_path,
        rubric_dimensions=rubric_dimensions,
        evidences={},
        opinions=[],
        final_report=None,
    )

    # Load graph
    graph = build_auditor_graph()
    app = graph.compile()

    # Run the app
    final_state = app.invoke(state.model_dump())
    report = final_state["final_report"]

    # Print Markdown version to console
    print(format_audit_report(report))

    # Optionally save JSON verdict if output_path is provided
    if output_path:
        with open(output_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2)

if __name__ == "__main__":
    main()
