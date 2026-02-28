# src/nodes/judges.py
import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from src.state import AgentState, JudicialOpinion

# --- Common parser for structured output ---
judicial_parser = JsonOutputParser()  # returns raw JSON dict

# --- LLM setup ---
llm = None

# Load LLM configuration from environment variables
openai_key = os.getenv("OPENAI_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")
ollama_url = os.getenv("OLLAMA_BASE_URL")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Priority: OpenAI → Gemini → Ollama
if openai_key and not openai_key.startswith("your_"):
    # safer default for free tier: gpt-4o-mini
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    print("Using OpenAI LLM")

elif google_key and not google_key.startswith("your_"):
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    print("Using Google Gemini LLM")

elif ollama_url or ollama_model:
    # Default to Ollama if no cloud API keys are set
    llm = ChatOllama(
        model=ollama_model,
        temperature=0,
        base_url=ollama_url or "http://localhost:11434",
    )
    print(f"Using Ollama LLM ({ollama_model})")

else:
    raise RuntimeError(
        "No supported LLM API key found.\n"
        "Please set OPENAI_API_KEY, GOOGLE_API_KEY, or OLLAMA_BASE_URL in .env"
    )


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
        JudicialOpinion: Structured opinion object with score, argument, and citations.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are the Prosecutor. Trust no one."),
            (
                "user",
                "Evaluate evidence: {evidences}. "
                "Use the following rubric dimensions: {rubric_dimensions}. "
                "Return ONLY a valid JSON object with the following fields: "
                "judge (must be exactly 'Prosecutor'), "
                "criterion_id (must match one of the rubric dimension IDs), "
                "score (integer between 0 and 10), "
                "argument (string), "
                "cited_evidence (list of strings). "
                "Do not include any text outside the JSON.",
            ),
        ]
    )
    """
    raw_output = (prompt | llm).invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )
    print("Raw LLM output (Prosecutor):", raw_output)
    """
    chain = prompt | llm | judicial_parser
    parsed = chain.invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )

    opinion = JudicialOpinion.model_validate(parsed)
    return {"opinions": [opinion]}


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
        JudicialOpinion: Structured opinion object with score, argument, and citations.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are the Defense Attorney. Advocate fiercely."),
            (
                "user",
                "Evaluate evidence: {evidences}. "
                "Use the following rubric dimensions: {rubric_dimensions}. "
                "Return ONLY a valid JSON object with the following fields: "
                "judge (must be exactly 'Defense'), "
                "criterion_id (must match one of the rubric dimension IDs), "
                "score (integer between 0 and 10), argument (string), "
                "cited_evidence (list of strings). "
                "Do not include any text outside the JSON.",
            ),
        ]
    )
    """
    raw_output = (prompt | llm).invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )
    print("Raw LLM output (Defense):", raw_output)
    """
    chain = prompt | llm | judicial_parser
    parsed = chain.invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )

    opinion = JudicialOpinion.model_validate(parsed)
    return {"opinions": [opinion]}


def techlead_node(state: AgentState) -> JudicialOpinion:
    """
    LangGraph node: TechLead (Pragmatic Lens).

    Responsibilities:
        - Focus on whether the code works and is maintainable.
        - Evaluate architectural soundness and practical viability.
        - Provide realistic scores and remediation advice.

    Args:
        state (AgentState): Current agent state containing evidence.

    Returns:
        JudicialOpinion: Structured opinion object with score, argument, and citations.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are the TechLead. Be precise and technical."),
            (
                "user",
                "Evaluate evidence: {evidences}. Focus on technical merit.\n"
                "Use the following rubric dimensions: {rubric_dimensions}.\n"
                "Return ONLY a valid JSON object with the following fields:\n"
                "judge (must be exactly 'TechLead'), "
                "criterion_id (must match one of the rubric dimension IDs), "
                "score (integer between 0 and 10), argument (string), "
                "cited_evidence (list of strings). "
                "Do not include any text outside the JSON.",
            ),
        ]
    )
    """
    raw_output = (prompt | llm).invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )
    print("Raw LLM output (TechLead):", raw_output)
    """
    chain = prompt | llm | judicial_parser
    parsed = chain.invoke(
        {"evidences": state.evidences, "rubric_dimensions": state.rubric_dimensions}
    )
    opinion = JudicialOpinion.model_validate(parsed)
    return {"opinions": [opinion]}
