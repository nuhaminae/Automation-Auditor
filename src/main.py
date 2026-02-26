# src/main.py
import sys

from src.graph import build_auditor_graph
from src.state import AgentState


def main():
    repo_url = sys.argv[1]
    pdf_path = sys.argv[2]

    # Build initial state
    state = AgentState(repo_url=repo_url, pdf_path=pdf_path, evidences=[], opinions=[])

    # Load graph
    graph = build_auditor_graph()

    # Run graph
    result = graph.invoke(state)

    print(result)


if __name__ == "__main__":
    main()
