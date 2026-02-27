# src/nodes/justice.py
# This module synthesizes the conflicting opinions from the Prosecutor,
# Defense, and TechLead into a final `CriterionResult` and ultimately an `AuditReport`.

from typing import List, Dict, Optional

from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion

def normalise_score(score: int) -> int:
    """Convert 0–10 judge score into 1–5 final scale."""
    return max(1, min(5, round(score / 2)))

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
    opinions: List[JudicialOpinion] = state.opinions
    rubric_dimensions: List[Dict] = state.rubric_dimensions or []
    synthesis_rules: Dict = getattr(state, "synthesis_rules", {})

    criteria_results: List[CriterionResult] = []

    # Helper: map criterion_id -> rubric dimension metadata
    rubric_lookup = {dim["id"]: dim for dim in rubric_dimensions}

    # Group opinions by criterion_id, skipping any missing/empty IDs
    grouped = {}
    for opinion in opinions:
        if opinion.criterion_id:  # safeguard against empty IDs
            grouped.setdefault(opinion.criterion_id, []).append(opinion)

    for criterion_id, judge_opinions in grouped.items():
        scores = [op.score for op in judge_opinions]
        #final_score = resolve_conflict(judge_opinions, synthesis_rules)
        raw_score = resolve_conflict(judge_opinions, synthesis_rules)
        final_score = normalise_score(raw_score)

        # Dissent requirement
        dissent_summary: Optional[str] = None
        if scores and (max(scores) - min(scores) > 2):
            dissent_summary = "Significant disagreement among judges."
            if synthesis_rules.get("variance_re_evaluation"):
                dissent_summary += " Re-evaluation required."

        # Lookup rubric metadata
        dimension_meta = rubric_lookup.get(criterion_id, {})
        dimension_name = dimension_meta.get("name", criterion_id.replace("_", " ").title())
        failure_pattern = dimension_meta.get("failure_pattern", "")
        forensic_instruction = dimension_meta.get("forensic_instruction", "")

        remediation = f"Review files related to {criterion_id}.\n"
        if failure_pattern:
            remediation += f" Common failure: {failure_pattern}\n"
        if forensic_instruction:
            remediation += f"Instruction: {forensic_instruction}\n"
        remediation += "Address issues noted by judges."

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

    # Guard against division by zero if no criteria results
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
        remediation_plan="Apply remediation steps per criterion to improve architecture and compliance.",
    )
    return {"final_report": report}

def resolve_conflict(judge_opinions: List[JudicialOpinion], synthesis_rules: Dict) -> int:
    """
    Resolve conflicts among judge opinions using rubric synthesis rules.

    Args:
        judge_opinions (List[JudicialOpinion]): Opinions from Prosecutor, Defense, TechLead.
        synthesis_rules (Dict): Rules from rubric JSON.

    Returns:
        int: Final score (1–10) after applying conflict resolution rules.
    """
    prosecutor_score = next((op.score for op in judge_opinions if op.judge == "Prosecutor"), None)
    techlead_score = next((op.score for op in judge_opinions if op.judge == "TechLead"), None)

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
    lines.append(f"**Overall Score:** {report.overall_score:.2f}")
    lines.append("")

    for cr in report.criteria:
        lines.append(f"## Criterion: {cr.dimension_name} ({cr.dimension_id})")
        lines.append(f"Final Score: {cr.final_score}")
        if cr.dissent_summary:
            lines.append(f"Dissent: {cr.dissent_summary}")
        lines.append("### Judge Opinions:")
        for op in cr.judge_opinions:
            lines.append(f"- **{op.judge}**: Score {op.score}, Argument: {op.argument}")
        lines.append("### Remediation:")
        lines.append(cr.remediation)
        lines.append("")

    lines.append("## Remediation Plan")
    lines.append(report.remediation_plan)
    return "\n".join(lines)
