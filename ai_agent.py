"""
MixBot AI Agent

Claude-powered mixing engineer. Provides intelligent feedback based on
audio analysis metrics and holds conversational follow-up with users.

Requires ANTHROPIC_API_KEY environment variable (or set via .env file).
Falls back gracefully to rule-based feedback if the key is missing.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_ANTHROPIC_AVAILABLE = False
_client = None

try:
    import anthropic
    _api_key = os.getenv("ANTHROPIC_API_KEY")
    if _api_key:
        _client = anthropic.Anthropic(api_key=_api_key)
        _ANTHROPIC_AVAILABLE = True
except ImportError:
    pass


MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are MixBot, an expert mixing and mastering engineer with 20+ years of experience 
across all genres. You analyze audio metrics and give actionable, professional mixing advice.

Your feedback should be:
- Specific and technical but accessible to intermediate producers
- DAW-aware: tailor plugin/workflow suggestions to the user's DAW
- Genre-aware: reference genre norms when assessing loudness, dynamics, and tone
- Prioritized: lead with the most critical issues first
- Encouraging but honest — celebrate what works, flag what needs fixing

When given analysis metrics, provide feedback in clear sections using markdown.
When chatting, be concise and conversational. Always reference the actual numbers from the analysis.
"""


def is_available() -> bool:
    """Returns True if the Anthropic client is ready."""
    return _ANTHROPIC_AVAILABLE


def _build_metrics_summary(metrics: dict, daw: str, vibe: str, stem_data: Optional[dict]) -> str:
    """Build a structured text summary of the analysis to pass to Claude."""
    rms_db = metrics.get("rms_db", 0)
    peak_db = metrics.get("peak_db", 0)
    dynamic_range = peak_db - rms_db
    tempo = metrics.get("tempo", 0)
    silence_pct = metrics.get("silence_percentage", 0)
    clipping = metrics.get("clipping", False)
    duration = metrics.get("duration", "unknown")

    stem_section = ""
    if stem_data:
        lines = ["\n**Stem Analysis:**"]
        for stem_name, stem_metrics in stem_data.items():
            lines.append(
                f"- {stem_name.capitalize()}: RMS {stem_metrics.get('rms_db', 0):.1f} dB, "
                f"Peak {stem_metrics.get('peak_db', 0):.1f} dB, "
                f"Dynamic Range {stem_metrics.get('dynamic_range', 0):.1f} dB"
            )
        stem_section = "\n".join(lines)

    return f"""**Audio Analysis Results:**

- DAW: {daw if daw else 'Not specified'}
- Vibe / Reference style: {vibe if vibe else 'Not specified'}
- Duration: {duration}
- Tempo: {tempo:.0f} BPM
- RMS Level: {rms_db:.1f} dB
- Peak Level: {peak_db:.1f} dB
- Dynamic Range: {dynamic_range:.1f} dB
- Silence: {silence_pct:.1f}% of track
- Clipping detected: {'YES — CRITICAL' if clipping else 'No'}
{stem_section}

Please give me a full mixing/mastering feedback report covering:
1. Overall assessment
2. Loudness & dynamics
3. Clipping (if any)
4. EQ recommendations
5. Compression recommendations
6. Effects recommendations  
7. Mastering preparation tips

Tailor everything to the DAW and vibe/genre above. Use markdown formatting with headers."""


def generate_ai_feedback(
    metrics: dict,
    daw: str,
    vibe: str = "",
    stem_data: Optional[dict] = None,
) -> Optional[str]:
    """
    Generate Claude-powered mix feedback.

    Returns a markdown string on success, or None if unavailable.
    """
    if not _ANTHROPIC_AVAILABLE:
        return None

    prompt = _build_metrics_summary(metrics, daw, vibe, stem_data)

    try:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return None


def chat_with_agent(
    user_message: str,
    metrics: dict,
    daw: str,
    vibe: str,
    chat_history: list,
) -> str:
    """
    Conversational follow-up about the mix.

    chat_history is a list of {"role": "user"|"assistant", "content": str} dicts.
    Returns the assistant's reply as a string.
    """
    if not _ANTHROPIC_AVAILABLE:
        return (
            "AI chat is not available — add your ANTHROPIC_API_KEY to a `.env` file "
            "in the project root to enable it."
        )

    rms_db = metrics.get("rms_db", 0)
    peak_db = metrics.get("peak_db", 0)
    tempo = metrics.get("tempo", 0)
    clipping = metrics.get("clipping", False)

    context_note = (
        f"[Context: user's track — {tempo:.0f} BPM, RMS {rms_db:.1f} dB, "
        f"Peak {peak_db:.1f} dB, Clipping: {'yes' if clipping else 'no'}, "
        f"DAW: {daw or 'unknown'}, Vibe: {vibe or 'not specified'}]"
    )

    messages = []

    # Inject context as a silent system note in the first turn if no history
    if not chat_history:
        messages.append({
            "role": "user",
            "content": f"{context_note}\n\n{user_message}",
        })
    else:
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

    try:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Error reaching AI: {str(e)}"
