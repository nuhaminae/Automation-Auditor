# src/nodes/detectives.py
# This module wrapsRepoInvestigator and DocAnalyst tools
# so they can run in parallel and output structured Evidence objects

from langgraph.graph import StateGraph

from src.state import AgentState, Evidence
from src.tools import doc_tools, repo_tools


def repo_investigator_node(state: AgentState) -> Evidence:
    """
    LangGraph node: RepoInvestigator (Code Detective).

    Responsibilities:
        - Clone the target repository in a sandbox.
        - Extract git history for forensic analysis.
        - Analyse graph structure via AST parsing.

    Args:
        state (AgentState): Current agent state containing repo_url.

    Returns:
        Evidence: Structured evidence object with findings.
    """
    repo_url = state.repo_url
    repo_path = repo_tools.clone_repository(repo_url)
    commits = repo_tools.extract_git_history(repo_path)
    graph_flags = repo_tools.analyse_graph_structure(f"{repo_path}/src/graph.py")

    return Evidence(
        goal="Repository Forensics",
        found=True,
        content=str({"commits": commits, "graph_flags": graph_flags}),
        location=repo_path,
        rationale="Repo cloned and analysed successfully.",
        confidence=0.9,
    )


def doc_analyst_node(state: AgentState) -> Evidence:
    """
    LangGraph node: DocAnalyst (Paperwork Detective).

    Responsibilities:
        - Ingest the PDF report using Docling.
        - Chunk the document for manageable querying.
        - Search for key concepts (Dialectical Synthesis, Fan-In/Fan-Out).
        - Cross-reference file paths mentioned in the report against repo files.

    Args:
        state (AgentState): Current agent state containing pdf_path.

    Returns:
        Evidence: Structured evidence object with findings.
    """
    pdf_path = state.pdf_path
    doc = doc_tools.ingest_pdf(pdf_path)
    chunks = doc_tools.chunk_document(doc)

    keywords = ["Dialectical Synthesis", "Fan-In", "Fan-Out", "Metacognition"]
    keyword_hits = {kw: doc_tools.query_document(chunks, kw) for kw in keywords}

    # Example repo files list (would be collected by RepoInvestigator in practice)
    repo_files = ["src/state.py", "src/graph.py", "src/tools/repo_tools.py"]
    cross_refs = doc_tools.cross_reference_paths(chunks, repo_files)

    return Evidence(
        goal="PDF Report Forensics",
        found=True,
        content=str({"keywords": keyword_hits, "cross_refs": cross_refs}),
        location=pdf_path,
        rationale="PDF parsed and cross-referenced successfully.",
        confidence=0.85,
    )


# Example wiring into a StateGraph
def build_detective_graph() -> StateGraph:
    """
    Build a partial StateGraph wiring RepoInvestigator and DocAnalyst
    in parallel with an EvidenceAggregator node.

    Returns:
        StateGraph: A LangGraph StateGraph object with detective nodes.
    """
    graph = StateGraph(AgentState)

    # Add detective nodes
    graph.add_node("RepoInvestigator", repo_investigator_node)
    graph.add_node("DocAnalyst", doc_analyst_node)

    # EvidenceAggregator node (fan-in)
    def evidence_aggregator(state: AgentState) -> AgentState:
        """
        Aggregates evidence from RepoInvestigator and DocAnalyst.
        """
        return state

    graph.add_node("EvidenceAggregator", evidence_aggregator)

    # Wiring: fan-out detectives -> fan-in aggregator
    graph.add_edge("RepoInvestigator", "EvidenceAggregator")
    graph.add_edge("DocAnalyst", "EvidenceAggregator")

    return graph
