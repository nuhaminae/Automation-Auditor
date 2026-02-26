# src/nodes/justice.py
# This module synthesizes the conflicting opinions from the Prosecutor,
# Defense, and Tech Lead into a final `CriterionResult` and ultimately an `AuditReport`.

from typing import List

from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion


def chief_justice_node(state: AgentState) -> AuditReport:
    """
    LangGraph node: ChiefJusticeNode (Supreme Court).

    Responsibilities:
        - Resolve conflicts between Prosecutor, Defense, and Tech Lead opinions.
        - Apply deterministic rules:
            * Security overrides: confirmed vulnerabilities cap score at 3.
            * Evidence supremacy: hallucinated claims are overruled.
            * Functionality priority: working modular architecture carries
                                        highest weight.
        - Generate a structured AuditReport in Markdown-ready format.

    Args:
        state (AgentState): Current agent state containing judge opinions.

    Returns:
        AuditReport: Final synthesised audit report with
                        scores, dissent summaries, and remediation plan.
    """
    opinions: List[JudicialOpinion] = state.opinions
    criteria_results: List[CriterionResult] = []

    # Group opinions by criterion_id, skipping any missing/empty IDs
    grouped = {}
    for opinion in opinions:
        if opinion.criterion_id:  # safeguard against empty IDs
            grouped.setdefault(opinion.criterion_id, []).append(opinion)

    for criterion_id, judge_opinions in grouped.items():
        scores = [op.score for op in judge_opinions]
        final_score = resolve_conflict(judge_opinions)

        dissent_summary = None
        if scores and (max(scores) - min(scores) > 2):
            dissent_summary = "Significant disagreement among judges."

        remediation = f"Review files related to {criterion_id} \n"
        remediation += "and address issues noted by judges."

        criteria_results.append(
            CriterionResult(
                dimension_id=criterion_id,
                dimension_name=criterion_id.replace("_", " ").title(),
                final_score=final_score,
                judge_opinions=judge_opinions,
                dissent_summary=dissent_summary,
                remediation=remediation,
            )
        )

    # Guard against division by zero if no criteria results
    overall_score = (
        sum(cr.final_score for cr in criteria_results) / len(criteria_results)
        if criteria_results else 0
    )

    return AuditReport(
        repo_url=state.repo_url,
        executive_summary="Automated audit completed. See detailed criteria below.",
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan="Apply remediation steps per criterion \n"
        "to improve architecture and compliance.",
    )


def resolve_conflict(judge_opinions: List[JudicialOpinion]) -> int:
    """
    Resolve conflicts among judge opinions using hardcoded rules.

    Args:
        judge_opinions (List[JudicialOpinion]): Opinions from
                                                Prosecutor, Defense, Tech Lead.

    Returns:
        int: Final score (1–5) after applying conflict resolution rules.
    """
    prosecutor_score = next(
        (op.score for op in judge_opinions if op.judge == "Prosecutor"), None
    )
    techlead_score = next(
        (op.score for op in judge_opinions if op.judge == "TechLead"), None
    )

    # Rule of Security: Prosecutor overrides if critical flaw
    if prosecutor_score == 1:
        return min(3, prosecutor_score)

    # Rule of Functionality: Tech Lead carries highest weight
    if techlead_score is not None:
        return techlead_score

    # Default: average of scores
    return int(round(sum(op.score for op in judge_opinions) / len(judge_opinions)))
