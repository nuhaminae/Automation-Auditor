# src/nodes/detectives.py
# This module wraps RepoInvestigator, DocAnalyst, and VisionInspector tools
# so they can run in parallel and output structured Evidence objects.

import os

from langgraph.graph import StateGraph

from src.state import AgentState, Evidence
from src.tools import doc_tools, repo_tools, vision_tools


def repo_investigator_node(state: AgentState) -> Evidence:
    """
    LangGraph node: RepoInvestigator (Code Detective).

    Responsibilities:
        - Clone the target repository in a sandbox.
        - Extract git history for forensic analysis.
        - Analyse graph structure via AST parsing.
        - Enrich commit history with GitHub API data if token is available.

    Args:
        state (AgentState): Current agent state containing repo_url.

    Returns:
        Evidence: Structured evidence object with findings.
    """
    repo_url = state.repo_url
    repo_path = repo_tools.clone_repository(repo_url)
    commits = repo_tools.extract_git_history(repo_path)
    graph_flags = repo_tools.analyse_graph_structure(f"{repo_path}/src/graph.py")

    # Try enrichment if token is present
    token = repo_tools.get_github_token()
    enriched_commits = []
    if token:
        # Derive "owner/repo" from URL
        repo_full_name = repo_url.split("github.com/")[-1].rstrip(".git")
        for c in commits:
            try:
                api_data = repo_tools.fetch_commit_details(repo_full_name, c["hash"])
                enriched_commits.append(
                    {
                        **c,
                        "author": api_data["commit"]["author"]["name"],
                        "files_changed": len(api_data.get("files", [])),
                        "additions": sum(
                            f["additions"] for f in api_data.get("files", [])
                        ),
                        "deletions": sum(
                            f["deletions"] for f in api_data.get("files", [])
                        ),
                    }
                )
            except repo_tools.RepoError:
                enriched_commits.append(c)

        contributors = repo_tools.fetch_contributors(repo_full_name)
        pulls = repo_tools.fetch_pull_requests(repo_full_name, state="all")
        reviews = {
            pr["number"]: repo_tools.fetch_pr_reviews(repo_full_name, pr["number"])
            for pr in pulls
        }
        collab_score = repo_tools.score_collaboration(
            contributors, pulls, reviews, enriched_commits
        )

        collab_evidence = {
            "contributors": contributors,
            "pull_requests": pulls,
            "reviews": reviews,
            "collaboration_score": collab_score,
        }
    else:
        enriched_commits = commits
        collab_evidence = {
            "note": "No GitHub token, collaboration evidence not collected."
        }

    return Evidence(
        goal="Repository Forensics",
        found=True,
        content={
            "commits": enriched_commits,
            "graph_flags": graph_flags,
            "collaboration": collab_evidence,
        },
        location=repo_path,
        rationale="Repo cloned and analysed"
        + (" with GitHub API enrichment" if token else " locally only"),
        confidence=0.9 if token else 0.85,
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
        content={"keywords": keyword_hits, "cross_refs": cross_refs},
        location=pdf_path,
        rationale="PDF parsed and cross-referenced successfully.",
        confidence=0.85,
    )


def vision_inspector_node(state: AgentState) -> Evidence:
    """
    LangGraph node: VisionInspector (Visual Detective).

    Responsibilities:
        - Extract embedded images/figures from the PDF report.
        - Scan repository directories for static image files.
        - Provide structured metadata about visual aids (counts, flags).
        - Lightweight implementation: no deep classification.
    """
    try:
        visual_evidence = vision_tools.analyse_visual_evidence(
            state.pdf_path, state.repo_url
        )
        return Evidence(
            goal="Visual Forensics",
            found=bool(
                visual_evidence["pdf_figures"] or visual_evidence["repo_images"]
            ),
            content=visual_evidence,
            location=f"{state.pdf_path} + {state.repo_url}",
            rationale="Extracted figures from PDF and scanned repo for images.",
            confidence=0.8,
        )
    except vision_tools.VisionError as e:
        return Evidence(
            goal="Visual Forensics",
            found=False,
            content={"error": str(e)},
            location=state.pdf_path,
            rationale="VisionInspector failed to analyse visual evidence.",
            confidence=0.5,
        )


def build_detective_graph() -> StateGraph:
    """
    Build a partial StateGraph wiring RepoInvestigator and DocAnalyst
    in parallel with an EvidenceAggregator node. VisionInspector is optional.
    Returns:
        StateGraph: A LangGraph StateGraph object with detective nodes.
    """
    graph = StateGraph(AgentState)

    # Add detective nodes
    graph.add_node("RepoInvestigator", repo_investigator_node)
    graph.add_node("DocAnalyst", doc_analyst_node)

    # Conditionally add VisionInspector
    enable_vision = os.getenv("ENABLE_VISION_INSPECTOR", "false").lower() == "true"
    if enable_vision:
        print("[INFO] VisionInspector enabled.")
        graph.add_node("VisionInspector", vision_inspector_node)
    else:
        print(
            "[INFO] VisionInspector disabled (set ENABLE_VISION_INSPECTOR=true in .env to enable)."
        )

    def evidence_aggregator(state: AgentState) -> AgentState:
        """
        Aggregates evidence from RepoInvestigator, DocAnalyst, and optionally VisionInspector.
        """
        evidences = getattr(state, "evidences", {})

        if hasattr(state, "RepoInvestigator") and state.RepoInvestigator:
            evidences.setdefault("Repository Forensics", []).append(
                state.RepoInvestigator
            )

        if hasattr(state, "DocAnalyst") and state.DocAnalyst:
            evidences.setdefault("PDF Report Forensics", []).append(state.DocAnalyst)

        if (
            enable_vision
            and hasattr(state, "VisionInspector")
            and state.VisionInspector
        ):
            evidences.setdefault("Visual Forensics", []).append(state.VisionInspector)

        state.evidences = evidences
        return state

    graph.add_node("EvidenceAggregator", evidence_aggregator)

    # Wiring: fan-out detectives -> fan-in aggregator
    graph.add_edge("RepoInvestigator", "EvidenceAggregator")
    graph.add_edge("DocAnalyst", "EvidenceAggregator")
    if enable_vision:
        graph.add_edge("VisionInspector", "EvidenceAggregator")

    return graph
    return graph
