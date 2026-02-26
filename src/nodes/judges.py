# src/nodes/judges.py
# This module defines the three judge personas (Prosecutor, Defense, Tech Lead)
# each returning structured `JudicialOpinion` objects.

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.state import AgentState, JudicialOpinion

# --- Common parser for structured output ---
judicial_parser = PydanticOutputParser(pydantic_object=JudicialOpinion)


def prosecutor_node(state: AgentState) -> JudicialOpinion:
    """
    LangGraph node: Prosecutor (Critical Lens).

    Responsibilities:
        - Scrutinise evidence for gaps, flaws, and lasiness.
        - Apply harsh scoring when orchestration or structure is missing.
        - Charge violations like "Orchestration Fraud" or "Hallucination Liability".

    Args:
        state (AgentState): Current agent state containing evidence.

    Returns:
        JudicialOpinion: Structured opinion object with score, argu, and citations.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Prosecutor. Trust no one. Assume vibe coding."),
        (
            "user",
            "Evaluate evidence: {evidences}. "
            "Apply rubric strictly. "
            "Return JSON with judge, criterion_id, score, argument, cited_evidence.",
        ),
    ])
    formatted = prompt.format_prompt(evidences=state.evidences)
    return judicial_parser.parse(formatted.to_string())


def defense_node(state: AgentState) -> JudicialOpinion:
    """
    LangGraph node: Defense Attorney (Optimistic Lens).

    Responsibilities:
        - Highlight effort, creativity, and intent even if imperfect.
        - Argue for higher scores when evidence shows deep thought or iteration.
        - Mitigate harsh penalties with context.

    Args:
        state (AgentState): Current agent state containing evidence.

    Returns:
        JudicialOpinion: Structured opinion object with score, argu, and citations.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Defense Attorney. Reward effort and intent."),
        (
            "user",
            "Evaluate evidence: {evidences}. "
            "Look for signs of deep thought or iteration. "
            "Return JSON with judge, criterion_id, score, argument, cited_evidence.",
        ),
    ])
    formatted = prompt.format_prompt(evidences=state.evidences)
    return judicial_parser.parse(formatted.to_string())


def techlead_node(state: AgentState) -> JudicialOpinion:
    """
    LangGraph node: Tech Lead (Pragmatic Lens).

    Responsibilities:
        - Focus on whether the code works and is maintainable.
        - Evaluate architectural soundness and practical viability.
        - Provide realistic scores and remediation advice.

    Args:
        state (AgentState): Current agent state containing evidence.

    Returns:
        JudicialOpinion: Structured opinion object with score, argu, and citations.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Tech Lead. Focus on practicality and maintainability."),
        (
            "user",
            "Evaluate evidence: {evidences}. "
            "Ignore vibe and struggle. "
            "Return JSON with judge, criterion_id, score, argument, cited_evidence.",
        ),
    ])
    formatted = prompt.format_prompt(evidences=state.evidences)
    return judicial_parser.parse(formatted.to_string())
