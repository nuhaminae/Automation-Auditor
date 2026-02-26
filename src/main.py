# src/main.py
import sys

from src.graph import build_auditor_graph
from src.state import AgentState


def main():
    repo_url = sys.argv[1]
    pdf_path = sys.argv[2]

    # Build initial state
    state = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None,
    }

    # Load graph
    graph = build_auditor_graph()

    # Run graph
    final_state = graph.run(state)

    print(final_state["final_report"])


if __name__ == "__main__":
    main()
