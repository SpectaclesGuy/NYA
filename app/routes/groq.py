from __future__ import annotations

from typing import Any
import json
import time

import anyio
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import require_onboarding_complete


router = APIRouter(prefix="/groq", tags=["groq"])
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_COUNT = 5
_rate_limit_store: dict[str, list[float]] = {}


class CapstoneIdeaRequest(BaseModel):
    field: str = Field(..., min_length=1)
    focus: str = Field(..., min_length=1)
    notes: str | None = None


class CapstoneIdeaResponse(BaseModel):
    idea: str


def _build_prompt(payload: CapstoneIdeaRequest) -> str:
    notes = payload.notes.strip() if payload.notes else ""
    notes_line = f"\nAdditional notes: {notes}" if notes else ""
    return (
    "You are an academic research mentor helping students design industry-relevant and research-driven capstone projects.\n\n"
    
    "=== MANDATORY RESEARCH GAP ANALYSIS ===\n"
    "Before proposing ANY idea, you MUST perform a literature and industry review.\n"
    "This is NOT optional. You must:\n"
    "1. Analyze existing state-of-the-art methods and commercial products\n"
    "2. Identify why current solutions are insufficient\n"
    "3. Document 3-4 SPECIFIC, CONCRETE research gaps\n\n"
    
    "RESEARCH GAP REQUIREMENTS (NON-NEGOTIABLE):\n"
    "• You MUST provide EXACTLY 3-4 research gaps\n"
    "• Each gap MUST be 1-2 sentences with technical specificity\n"
    "• NO generic statements like 'needs improvement' or 'limited accuracy'\n"
    "• Each gap MUST cite a specific limitation (e.g., 'Current OCR models achieve only 78% accuracy on handwritten medical prescriptions due to...')\n\n"
    
    "MANDATORY GAP CATEGORIES (must include BOTH):\n"
    "A. Theoretical Gaps (at least 1-2):\n"
    "   - Algorithm/model limitations: accuracy bottlenecks, failure modes, artifacts\n"
    "   - Architectural constraints: compute inefficiency, memory overhead\n"
    "   - Generalization issues: poor cross-domain performance, data distribution shift\n"
    "   - Training challenges: data scarcity, annotation cost, convergence issues\n"
    "   Example: 'Transformer-based time series models struggle with long-horizon forecasting (>48h) due to quadratic attention complexity, degrading to 65% accuracy vs 89% for short-term.'\n\n"
    
    "B. Practical/Deployment Gaps (at least 1-2):\n"
    "   - Real-time constraints: latency (e.g., '500ms response time fails user expectations')\n"
    "   - Hardware limitations: GPU requirements, mobile deployment barriers, edge compute\n"
    "   - Cost barriers: inference cost per query, training expense\n"
    "   - UX/accessibility issues: complex interfaces, lack of explainability\n"
    "   - Integration challenges: lack of APIs, incompatible data formats\n"
    "   Example: 'Existing medical diagnosis systems require cloud GPUs ($2/hour), making them unaffordable for rural clinics in developing regions.'\n\n"
    
    "=== PROJECT DESIGN (only after gaps are identified) ===\n"
    "Based on the gaps above, propose ONE capstone project that:\n"
    "- Directly addresses 2-3 of the identified gaps\n"
    "- Is feasible in 3-4 months for students\n"
    "- Uses open-source tools and publicly available datasets\n"
    "- Has clear deliverables and success metrics\n\n"
    
    "CONSTRAINTS:\n"
    "- Must be safe, ethical, and legal\n"
    "- No sexual/adult/illegal/harmful content\n"
    "- No over-ambitious goals (e.g., 'solve cancer')\n"
    "- Prefer domains with available data and tooling\n\n"
    
    "If Field or Focus is missing, automatically select a modern real-world domain (healthcare, climate, education, accessibility, etc.).\n\n"
    
    "=== OUTPUT FORMAT ===\n"
    "Return ONLY valid JSON. The 'research_gaps' field is MANDATORY.\n"
    "Each gap must be specific, measurable, and grounded in real limitations.\n\n"
    
    "{\n"
    '  "title": "Clear, specific project title",\n'
    '  "overview": "4-5 sentences explaining the problem, context, and proposed solution with real-world grounding",\n'
    '  "users": "2 sentences: who will use this and why",\n'
    '  "impact": "2 sentences: measurable outcomes and stakeholder benefits",\n'
    '  "research_gaps": [\n'
    '    "Gap 1: [Theoretical] Specific limitation with metrics/evidence (1-2 sentences)",\n'
    '    "Gap 2: [Theoretical] Another algorithm/model constraint (1-2 sentences)",\n'
    '    "Gap 3: [Practical] Deployment/usability barrier with concrete example (1-2 sentences)",\n'
    '    "Gap 4: [Practical] Real-world adoption challenge (1-2 sentences)"\n'
    '  ],\n'
    '  "tech_stack": ["Technology 1 (with purpose)", "Technology 2 (with purpose)", "..."],\n'
    '  "roadmap": [\n'
    '    "Week 1-2: Specific milestone with deliverable",\n'
    '    "Week 3-4: Next phase with metric",\n'
    '    "Week 5-8: Development goal",\n'
    '    "Week 9-12: Testing/evaluation",\n'
    '    "Week 13-16: Documentation and deployment"\n'
    '  ],\n'
    '  "datasets": [\n'
    '    "Dataset 1 name (source, size, purpose)",\n'
    '    "Dataset 2 name (source, size, purpose)",\n'
    '    "Dataset 3 name (source, size, purpose)"\n'
    '  ],\n'
    '  "extensions": [\n'
    '    "Extension 1: How to scale this project further",\n'
    '    "Extension 2: Advanced feature or integration",\n'
    '    "Extension 3: Research publication opportunity"\n'
    '  ]\n'
    "}\n\n"
    
    "VALIDATION CHECKLIST (self-check before responding):\n"
    "☐ Did I identify EXACTLY 3-4 research gaps?\n"
    "☐ Are gaps specific with metrics/examples (not generic)?\n"
    "☐ Do gaps include BOTH theoretical AND practical types?\n"
    "☐ Does the project directly address 2-3 of these gaps?\n"
    "☐ Is the JSON valid and complete?\n\n"
    
    f"Field: {payload.field}\n"
    f"Focus: {payload.focus}{notes_line}"
)







def _call_groq(prompt: str) -> str:
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Groq API key is not configured.")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            "temperature": 0.7,
            "max_tokens": 1200,
        },
        timeout=20,
    )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Groq request error: {exc}") from exc
    if response.status_code >= 400:
        detail = response.text.strip() or "Groq request failed."
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = payload.get("error", {}).get("message") or payload.get("message") or detail
        except ValueError:
            pass
        raise HTTPException(status_code=502, detail=f"Groq error ({response.status_code}): {detail}")

    data: dict[str, Any] = response.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="Groq returned an empty response.")
    return _normalize_response(content)


def _normalize_response(content: str) -> str:
    # Try strict JSON first for stable formatting.
    try:
        payload = json.loads(content)
        if isinstance(payload, dict):
            return _format_from_json(payload)
    except json.JSONDecodeError:
        pass
    # If the model didn't return JSON, attempt to coerce common single-line formatting.
    if "Title:" in content and "Overview:" in content:
        return _normalize_inline_sections(content)
    # Normalize common formatting quirks into the expected multi-line layout.
    text = content.replace("\r\n", "\n")
    if "##" in text:
        text = text.replace("## ", "").replace(" ##", "\n")
    text = text.replace("Roadmap: -", "Roadmap:\n-")
    text = text.replace("Datasets: -", "Datasets:\n-")
    text = text.replace("Extensions: -", "Extensions:\n-")
    text = text.replace("Tech Stack:", "Tech Stack:")
    text = text.replace("Overview:", "Overview:")
    return text.strip()


def _normalize_inline_sections(text: str) -> str:
    sections = [
        "Title:",
        "Overview:",
        "Users:",
        "Impact:",
        "Tech Stack:",
        "Roadmap:",
        "Datasets:",
        "Extensions:",
    ]
    normalized = text.replace("\r\n", "\n")
    for section in sections:
        normalized = normalized.replace(f" {section}", f"\n{section}")
        normalized = normalized.replace(section, f"\n{section}")
    normalized = normalized.replace("\n\n", "\n")
    normalized = normalized.replace("Roadmap: -", "Roadmap:\n-")
    normalized = normalized.replace("Datasets: -", "Datasets:\n-")
    normalized = normalized.replace("Extensions: -", "Extensions:\n-")
    return normalized.strip()


def _format_from_json(payload: dict[str, Any]) -> str:
    def _join_list(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    def _bullets(value: Any) -> str:
        if isinstance(value, list):
            return "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
        text = str(value).strip()
        return f"- {text}" if text else ""

    title = str(payload.get("title", "")).strip()
    overview = str(payload.get("overview", "")).strip()
    users = str(payload.get("users", "")).strip()
    impact = str(payload.get("impact", "")).strip()
    tech = _join_list(payload.get("tech_stack", []))
    roadmap = _bullets(payload.get("roadmap", []))
    datasets = _bullets(payload.get("datasets", []))
    extensions = _bullets(payload.get("extensions", []))

    return (
        f"Title: {title}\n"
        f"Overview: {overview}\n"
        f"Users: {users}\n"
        f"Impact: {impact}\n"
        f"Tech Stack: {tech}\n"
        "Roadmap:\n"
        f"{roadmap}\n"
        "Datasets:\n"
        f"{datasets}\n"
        "Extensions:\n"
        f"{extensions}"
    ).strip()


@router.post("/capstone", response_model=CapstoneIdeaResponse)
async def generate_capstone_idea(
    payload: CapstoneIdeaRequest,
    request: Request,
    _current_user=Depends(require_onboarding_complete),
) -> CapstoneIdeaResponse:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _rate_limit_store.get(client_ip, [])
    timestamps = [ts for ts in timestamps if now - ts < _RATE_LIMIT_WINDOW]
    if len(timestamps) >= _RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    timestamps.append(now)
    _rate_limit_store[client_ip] = timestamps
    prompt = _build_prompt(payload)
    idea = await anyio.to_thread.run_sync(_call_groq, prompt)
    return CapstoneIdeaResponse(idea=idea)
