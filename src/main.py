# src/main.py
import sys

from src.graph import build_auditor_graph
from src.state import AgentState


def main():
    repo_url = sys.argv[1]
    pdf_path = sys.argv[2]

    # Build initial state using Pydantic model
    state = AgentState(
        repo_url=repo_url,
        pdf_path=pdf_path,
        rubric_dimensions=[],
        evidences={},
        opinions=[],
        final_report=None,
    )

    # Load graph
    graph = build_auditor_graph()

    # Compile the graph into an app
    app = graph.compile()

    # Run the app
    # final_state = app.invoke(state.dict())  # convert to dict for LangGraph
    final_state = app.invoke(state.model_dump())

    print(final_state["final_report"])


if __name__ == "__main__":
    main()
