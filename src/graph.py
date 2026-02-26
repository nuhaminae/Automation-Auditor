# src/graph.py
# This module defines the complete LangGraph pipeline for the Automaton Auditor.
# It wires together all nodes into a cohesive workflow.

from langgraph.graph import StateGraph

from src.nodes.detectives import doc_analyst_node, repo_investigator_node
from src.nodes.judges import defense_node, prosecutor_node, techlead_node
from src.nodes.justice import chief_justice_node
from src.state import AgentState, AuditReport


def build_auditor_graph() -> StateGraph:
    """
    Build the complete Automaton Auditor StateGraph.

    Workflow:
        1. Detectives (RepoInvestigator, DocAnalyst) run in parallel (fan-out).
        2. EvidenceAggregator collects all evidence (fan-in).
        3. Judges (Prosecutor, Defense, TechLead) run in parallel on the evidence.
        4. ChiefJusticeNode synthesises opinions into a final AuditReport.

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

    # --- Judges ---
    graph.add_node("Prosecutor", prosecutor_node)
    graph.add_node("Defense", defense_node)
    graph.add_node("TechLead", techlead_node)

    def opinions_aggregator(state: AgentState) -> AgentState:
        """
        Aggregates JudicialOpinions from all judges.
        """
        # Opinions are appended via reducers in AgentState
        return state

    graph.add_node("OpinionsAggregator", opinions_aggregator)

    # --- Chief Justice ---
    graph.add_node("ChiefJustice", chief_justice_node)

    # --- Wiring ---
    # Entry point: set both RepoInvestigator and DocAnalyst as starting nodes
    graph.set_entry_point("RepoInvestigator")
    graph.set_entry_point("DocAnalyst")

    # Detectives fan-out -> EvidenceAggregator
    graph.add_edge("RepoInvestigator", "EvidenceAggregator")
    graph.add_edge("DocAnalyst", "EvidenceAggregator")

    # EvidenceAggregator fan-out -> Judges
    graph.add_edge("EvidenceAggregator", "Prosecutor")
    graph.add_edge("EvidenceAggregator", "Defense")
    graph.add_edge("EvidenceAggregator", "TechLead")

    # Judges fan-in -> OpinionsAggregator
    graph.add_edge("Prosecutor", "OpinionsAggregator")
    graph.add_edge("Defense", "OpinionsAggregator")
    graph.add_edge("TechLead", "OpinionsAggregator")

    # OpinionsAggregator -> ChiefJustice
    graph.add_edge("OpinionsAggregator", "ChiefJustice")

    return graph


def run_audit(repo_url: str, pdf_path: str) -> AuditReport:
    """
    Run the full Automaton Auditor workflow.

    Args:
        repo_url (str): GitHub repository URL to audit.
        pdf_path (str): Path to the PDF report.

    Returns:
        AuditReport: Final synthesised audit report.
    """
    graph = build_auditor_graph()
    app = graph.compile()  # compile before running
    initial_state = AgentState(
        repo_url=repo_url,
        pdf_path=pdf_path,
        rubric_dimensions=[],
        evidences={},
        opinions=[],
        final_report=None,
    )
    final_state = app.invoke(initial_state.model_dump())
    return final_state["final_report"]
