# src/graph.py
from langgraph.graph import StateGraph

from src.nodes.detectives import doc_analyst_node, repo_investigator_node
from src.state import AgentState, AuditReport


def build_auditor_graph() -> StateGraph:
    """
    Build the complete Automaton Auditor StateGraph.

    Workflow:
        1. Detectives (RepoInvestigator, DocAnalyst) run in parallel (fan-out).
        2. EvidenceAggregator collects all evidence (fan-in).

    Returns:
        StateGraph: Configured LangGraph pipeline for the Automaton Auditor.
    """
    graph = StateGraph(AgentState)

    # --- Detectives ---
    graph.add_node("RepoInvestigator", repo_investigator_node)
    graph.add_node("DocAnalyst", doc_analyst_node)

    def evidence_aggregator(state: AgentState) -> AgentState:
        """
        Aggregates evidence from RepoInvestigator and DocAnalyst.
        """
        # Evidence objects are already appended via reducers in AgentState
        return state

    graph.add_node("EvidenceAggregator", evidence_aggregator)

    # --- Wiring ---
    # Detectives fan-out -> EvidenceAggregator
    graph.add_edge("RepoInvestigator", "EvidenceAggregator")
    graph.add_edge("DocAnalyst", "EvidenceAggregator")

    return graph


def run_audit(repo_url: str, pdf_path: str) -> AuditReport:
    """
    Run the full Automaton Auditor workflow.

    Args:
        repo_url (str): GitHub repository URL to audit.
        pdf_path (str): Path to the PDF report.

    Returns:
        AuditReport: Partially synthesised audit report.
    """
    graph = build_auditor_graph()
    initial_state: AgentState = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "partial_report": None,
    }
    partial_state = graph.run(initial_state)
    return partial_state["partial_report"]
