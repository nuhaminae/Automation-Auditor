# src/nodes/justice.py
# This module synthesises the conflicting opinions from the Prosecutor,
# Defense, and TechLead into a final `CriterionResult` and ultimately an `AuditReport`.

from typing import Dict, List, Optional

from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion


def normalise_score(score: int) -> int:
    """Convert 0–10 judge score into 1–5 final scale."""
    return max(1, min(5, round(score / 2)))


def deduplicate_all_opinions(opinions: List[JudicialOpinion]) -> List[JudicialOpinion]:
    """Remove duplicate opinions across judges/dimensions."""
    seen = set()
    unique = []
    for op in opinions:
        key = (op.judge, op.criterion_id, op.argument.strip())
        if key not in seen:
            seen.add(key)
            unique.append(op)
    return unique


def chief_justice_node(state: AgentState) -> AuditReport:
    """
    LangGraph node: ChiefJusticeNode (Supreme Court).

    Responsibilities:
        - Resolve conflicts between Prosecutor, Defense, and TechLead opinions.
        - Apply deterministic rules defined in rubric synthesis_rules:
            * Security overrides: confirmed vulnerabilities cap score at 3.
            * Evidence supremacy: detective facts override judge opinions.
            * Functionality priority: TechLead carries highest weight.
            * Dissent requirement: variance > 2 requires dissent summary.
            * Variance re-evaluation: variance > 2 triggers re-evaluation.
        - Generate a structured AuditReport in Markdown-ready format.

    Args:
        state (AgentState): Current agent state containing judge opinions and rubric.

    Returns:
        AuditReport: Final synthesised audit report with
                        scores, dissent summaries, and remediation plan.
    """
    # opinions: List[JudicialOpinion] = state.opinions
    opinions: List[JudicialOpinion] = deduplicate_all_opinions(state.opinions)
    rubric_dimensions: List[Dict] = state.rubric_dimensions or []
    synthesis_rules: Dict = getattr(state, "synthesis_rules", {})

    criteria_results: List[CriterionResult] = []
    rubric_lookup = {dim["id"]: dim for dim in rubric_dimensions}

    # --- NEW: inspect RepoInvestigator evidence ---
    repo_evidence = next(
        (ev for ev in state.evidences if ev.goal == "Repository Forensics"), None
    )
    enriched_commits = []
    if repo_evidence:
        try:
            repo_content = repo_evidence.content or {}
            enriched_commits = repo_content.get("commits", [])
        except Exception:
            pass

    # Group opinions by criterion_id
    grouped = {}
    for opinion in opinions:
        if opinion.criterion_id:
            grouped.setdefault(opinion.criterion_id, []).append(opinion)

    for criterion_id, judge_opinions in grouped.items():
        raw_score = resolve_conflict(judge_opinions, synthesis_rules)
        final_score = normalise_score(raw_score)

        # --- NEW: forensic override based on enriched commits ---
        if enriched_commits:
            authors = {c.get("author") for c in enriched_commits if "author" in c}
            if len(authors) == 1 and synthesis_rules.get("collaboration_override"):
                final_score = min(final_score, 3)  # cap score if only one contributor

        dissent_summary: Optional[str] = None
        scores = [op.score for op in judge_opinions]
        if scores and (max(scores) - min(scores) > 2):
            dissent_summary = "Significant disagreement among judges."
            if synthesis_rules.get("variance_re_evaluation"):
                dissent_summary += " Re-evaluation required."

        dimension_meta = rubric_lookup.get(criterion_id, {})
        dimension_name = dimension_meta.get(
            "name", criterion_id.replace("_", " ").title()
        )
        failure_pattern = dimension_meta.get("failure_pattern", "")
        forensic_instruction = dimension_meta.get("forensic_instruction", "")

        # --- Remediation advice based on rubric and forensic hints ---
        remediation = f"To improve {dimension_name}:\n"
        if dimension_meta.get("success_pattern"):
            remediation += f"- Aim for: {dimension_meta['success_pattern']}.\n"
        if failure_pattern:
            remediation += f"- Avoid: {failure_pattern}.\n"
        if forensic_instruction:
            remediation += f"- Next step: {forensic_instruction}.\n"

        # Add forensic hints
        if enriched_commits and len(authors) == 1:
            remediation += "- Collaboration issue detected: only one contributor in commit history.\n"

        # Add detective evidence examples
        state_evidence = next(
            (ev for ev in state.evidences if ev.goal == "State Management"), None
        )
        if state_evidence and not state_evidence.content.get("reducers_used", True):
            remediation += (
                "- Detective evidence: No reducers detected in state management.\n"
            )

        graph_evidence = next(
            (ev for ev in state.evidences if ev.goal == "Graph Orchestration"), None
        )
        if graph_evidence and not graph_evidence.content.get("parallel_edges", True):
            remediation += "- Detective evidence: Graph orchestration is linear, no parallel fan-out/fan-in.\n"

        criteria_results.append(
            CriterionResult(
                dimension_id=criterion_id,
                dimension_name=dimension_name,
                final_score=final_score,
                judge_opinions=judge_opinions,
                dissent_summary=dissent_summary,
                remediation=remediation,
            )
        )

    overall_score = (
        sum(cr.final_score for cr in criteria_results) / len(criteria_results)
        if criteria_results
        else 0
    )

    report = AuditReport(
        repo_url=state.repo_url,
        executive_summary="Automated audit completed. See detailed criteria below.",
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan="Apply remediation steps per criterion to improve "
        "architecture and compliance.",
    )
    return {"final_report": report}


def resolve_conflict(
    judge_opinions: List[JudicialOpinion], synthesis_rules: Dict
) -> int:
    """
    Resolve conflicts among judge opinions using rubric synthesis rules.

    Args:
        judge_opinions (List[JudicialOpinion]): Opinions from
        Prosecutor, Defense, TechLead.
        synthesis_rules (Dict): Rules from rubric JSON.

    Returns:
        int: Final score (1–10) after applying conflict resolution rules.
    """
    prosecutor_score = next(
        (op.score for op in judge_opinions if op.judge == "Prosecutor"), None
    )
    techlead_score = next(
        (op.score for op in judge_opinions if op.judge == "TechLead"), None
    )

    # Rule of Security Override
    if prosecutor_score == 1 and synthesis_rules.get("security_override"):
        return min(3, prosecutor_score)

    # Rule of Functionality Weight
    if techlead_score is not None and synthesis_rules.get("functionality_weight"):
        return techlead_score

    # Default: average of scores
    return int(round(sum(op.score for op in judge_opinions) / len(judge_opinions)))


def format_audit_report(report: AuditReport) -> str:
    """
    Format the AuditReport into a Markdown-style string
    including each criterion, scores, dissent summaries,
    remediation, and judge opinions.
    """
    lines = []
    lines.append(f"# Audit Report for {report.repo_url}")
    lines.append("")
    lines.append(f"**Executive Summary:** {report.executive_summary}")
    lines.append(
        "**Note:** Judge scores are on a 0–10 scale. Final scores are normalised to a 1–5 scale."
    )
    lines.append(f"**Overall Score:** {report.overall_score:.2f}")
    lines.append("")

    for cr in report.criteria:
        lines.append(f"## Criterion: {cr.dimension_name} ({cr.dimension_id})")
        # Normalised scores are always on a 1–5 scale
        lines.append(f"Final Score: {cr.final_score} out of 5")
        if cr.dissent_summary:
            lines.append(f"Dissent: {cr.dissent_summary}")
        lines.append("### Judge Opinions:")
        for op in cr.judge_opinions:
            # Judge scores are always on a 0–10 scale
            lines.append(
                f"- **{op.judge}**: Score {op.score} out of 10, Argument: {op.argument}"
            )
        lines.append("### Remediation:")
        lines.append(cr.remediation)
        lines.append("")

    lines.append("## Remediation Plan")
    lines.append(report.remediation_plan)
    return "\n".join(lines)
