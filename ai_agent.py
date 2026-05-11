"""
MixBot AI Agent

Claude-powered mixing engineer with an agentic tool-use loop.

Claude decides which audio analysis tools to call, interprets the raw
results, and writes back professional mixing feedback — rather than
just reading pre-packaged numbers.

The same tools are also exposed as an MCP server (mcp_server.py) so
any MCP-compatible client (Cursor, Claude Desktop) can call them too.

Requires ANTHROPIC_API_KEY in .env.
"""

import os
import json
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

from audio_tools import analyze_audio_file, get_spectral_features, get_mix_recommendations

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are MixBot, an expert mixing and mastering engineer with 20+ years of experience 
across all genres. You have tools to analyze audio files directly.

Your workflow:
1. Always call analyze_audio first to get core metrics.
2. Call spectral_features when you need frequency balance details.
3. Call mix_recommendations to get a structured issue/suggestion list.
4. Synthesize everything into clear, actionable feedback.

Your feedback should be:
- Specific and technical but accessible to intermediate producers
- DAW-aware: tailor plugin/workflow suggestions to the user's DAW
- Genre-aware: reference genre norms for loudness and dynamics
- Prioritized: lead with critical issues (clipping, over-limiting) first
- Encouraging but honest

Use markdown formatting with clear section headers."""

# Tool definitions sent to Claude
TOOLS = [
    {
        "name": "analyze_audio",
        "description": (
            "Analyze an audio file and return core mixing metrics: duration, "
            "sample rate, RMS level (dB), peak level (dB), dynamic range (dB), "
            "tempo (BPM), clipping status, and silence percentage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the audio file (.wav or .mp3).",
                }
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "spectral_features",
        "description": (
            "Extract spectral characteristics: centroid, bandwidth, rolloff, "
            "zero-crossing rate, and energy across frequency bands "
            "(sub-bass, bass, low-mid, mid, high-mid, air)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the audio file (.wav or .mp3).",
                }
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "mix_recommendations",
        "description": (
            "Run analysis on an audio file and return structured mixing "
            "recommendations: a list of issues and actionable suggestions "
            "tailored to the DAW and genre."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the audio file (.wav or .mp3).",
                },
                "daw": {
                    "type": "string",
                    "description": "DAW name, e.g. 'FL Studio', 'Ableton Live'.",
                },
                "genre": {
                    "type": "string",
                    "description": "Genre or style, e.g. 'hip-hop', 'electronic'.",
                },
            },
            "required": ["file_path"],
        },
    },
]


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as a JSON string."""
    try:
        if tool_name == "analyze_audio":
            result = analyze_audio_file(tool_input["file_path"])
        elif tool_name == "spectral_features":
            result = get_spectral_features(tool_input["file_path"])
        elif tool_name == "mix_recommendations":
            result = get_mix_recommendations(
                analyze_audio_file(tool_input["file_path"]),
                daw=tool_input.get("daw", ""),
                genre=tool_input.get("genre", ""),
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


def is_available() -> bool:
    """Returns True if the Anthropic client is ready."""
    return _ANTHROPIC_AVAILABLE


def generate_ai_feedback(
    metrics: dict,
    daw: str,
    vibe: str = "",
    stem_data: Optional[dict] = None,
    file_path: Optional[str] = None,
) -> Optional[str]:
    """
    Generate Claude-powered mix feedback using the agentic tool-use loop.

    If file_path is provided Claude will call the audio tools itself.
    If not (e.g. the temp file was already deleted), falls back to
    describing the pre-extracted metrics.

    Returns a markdown string on success, or None if unavailable.
    """
    if not _ANTHROPIC_AVAILABLE:
        return None

    if file_path:
        user_content = (
            f"Please analyze the audio file at `{file_path}` and give me a full "
            f"mixing/mastering feedback report.\n\n"
            f"DAW: {daw or 'not specified'}\n"
            f"Genre/Vibe: {vibe or 'not specified'}\n\n"
            f"Call the tools in sequence: analyze_audio → spectral_features → "
            f"mix_recommendations, then write your full report."
        )
    else:
        # Fallback: describe metrics inline without tool calls
        stem_section = ""
        if stem_data:
            lines = ["Stem analysis:"]
            for stem, sm in stem_data.items():
                lines.append(
                    f"  {stem}: RMS {sm.get('rms_db', 0):.1f} dB, "
                    f"Peak {sm.get('peak_db', 0):.1f} dB"
                )
            stem_section = "\n" + "\n".join(lines)

        user_content = (
            f"The audio has already been analyzed. Here are the results:\n\n"
            f"- RMS: {metrics.get('rms_db', 0):.1f} dB\n"
            f"- Peak: {metrics.get('peak_db', 0):.1f} dB\n"
            f"- Dynamic Range: {metrics.get('peak_db', 0) - metrics.get('rms_db', 0):.1f} dB\n"
            f"- Tempo: {metrics.get('tempo', 0):.0f} BPM\n"
            f"- Clipping: {'YES' if metrics.get('clipping') else 'No'}\n"
            f"- Silence: {metrics.get('silence_percentage', 0):.1f}%\n"
            f"- Duration: {metrics.get('duration', 'unknown')}\n"
            f"{stem_section}\n\n"
            f"DAW: {daw or 'not specified'}\n"
            f"Genre/Vibe: {vibe or 'not specified'}\n\n"
            "Please write a full mixing/mastering feedback report."
        )

    messages = [{"role": "user", "content": user_content}]

    try:
        # Agentic loop — keep going until Claude stops calling tools
        while True:
            response = _client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                tools=TOOLS if file_path else [],
                messages=messages,
            )

            # Collect any tool calls
            tool_calls = [b for b in response.content if b.type == "tool_use"]

            if not tool_calls or response.stop_reason == "end_turn":
                # Final text response
                text_blocks = [b.text for b in response.content if hasattr(b, "text")]
                return "\n".join(text_blocks).strip() or None

            # Execute tool calls and feed results back
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tc in tool_calls:
                result_str = _execute_tool(tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            messages.append({"role": "user", "content": tool_results})

    except Exception as e:
        return None


def chat_with_agent(
    user_message: str,
    metrics: dict,
    daw: str,
    vibe: str,
    chat_history: list,
    file_path: Optional[str] = None,
) -> str:
    """
    Conversational follow-up using the agentic tool-use loop.

    chat_history is a list of {"role": "user"|"assistant", "content": ...} dicts.
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
        f"[Track context — {tempo:.0f} BPM, RMS {rms_db:.1f} dB, "
        f"Peak {peak_db:.1f} dB, Clipping: {'yes' if clipping else 'no'}, "
        f"DAW: {daw or 'unknown'}, Vibe: {vibe or 'not specified'}"
        + (f", file: {file_path}" if file_path else "")
        + "]"
    )

    messages = list(chat_history)

    if not messages:
        messages.append({
            "role": "user",
            "content": f"{context_note}\n\n{user_message}",
        })
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        while True:
            response = _client.messages.create(
                model=MODEL,
                max_tokens=700,
                system=SYSTEM_PROMPT,
                tools=TOOLS if file_path else [],
                messages=messages,
            )

            tool_calls = [b for b in response.content if b.type == "tool_use"]

            if not tool_calls or response.stop_reason == "end_turn":
                text_blocks = [b.text for b in response.content if hasattr(b, "text")]
                return "\n".join(text_blocks).strip()

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tc in tool_calls:
                result_str = _execute_tool(tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            messages.append({"role": "user", "content": tool_results})

    except Exception as e:
        return f"Error reaching AI: {str(e)}"
