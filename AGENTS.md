# MixBot — Agent Instructions

Read this before making any changes. It covers architecture, conventions, and things not to break.

---

## What This Project Is

AI-powered audio mixing assistant. Users upload a track → audio is analyzed with librosa DSP →
Claude runs an agentic tool-use loop (calling analyze_audio, spectral_features, key_detection,
mix_recommendations) → returns professional mixing feedback and holds a conversational chat.

The same audio tools are also exposed as a standalone MCP server so Cursor and Claude Desktop
can call them directly from the IDE.

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI — upload, analysis, AI feedback, chat, stem results |
| `ai_agent.py` | Claude agentic tool-use loop, lazy Anthropic client init |
| `audio_tools.py` | Shared DSP functions used by both the agent and MCP server |
| `mcp_server.py` | FastMCP server exposing audio tools over MCP protocol |
| `audio_analyzer.py` | Core librosa analysis engine (CLI + imported by app) |
| `stem_separator.py` | StemSeparator class — Demucs if available, librosa HPSS fallback |
| `requirements.txt` | Main app deps (Python 3.9+) |
| `mcp_requirements.txt` | MCP server deps (Python 3.10+ — use mcp_env venv) |

---

## Architecture

```
User → Streamlit UI (app.py)
           │
           ▼
    AI Agent (ai_agent.py)
    Claude tool-use loop
           │ calls
           ▼
    audio_tools.py  ◄──── also used by ────► MCP Server (mcp_server.py)
    - analyze_audio_file()                    Tools: analyze_audio,
    - get_spectral_features()                         spectral_features,
    - detect_key()                                    key_detection,
    - get_mix_recommendations()                       mix_recommendations
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_audio` | RMS, peak, dynamic range, BPM, clipping, silence percentage |
| `spectral_features` | Frequency band energies (sub-bass → air), centroid, rolloff |
| `key_detection` | Musical key, mode, confidence, relative key, Autotune recommendation |
| `mix_recommendations` | Structured issues + suggestions, DAW and genre aware |

To run the MCP server locally:
```bash
mcp_env/bin/python mcp_server.py
```

The `mcp_env/` virtualenv uses Python 3.13 and is gitignored. Rebuild with:
```bash
source $HOME/.local/bin/env  # activate uv
uv venv mcp_env --python 3.13
uv pip install -r mcp_requirements.txt --python mcp_env/bin/python
```

---

## Branch & Deploy Rules

- **Always work on `development`**
- **Merge to `main` to deploy** — Streamlit Cloud watches `main` and redeploys on every push
- Never force push to either branch

```bash
# Standard deploy flow
git add <files>
git commit -m "description"
git push origin development
git checkout main && git pull origin main && git merge development && git push origin main
git checkout development
```

---

## Session State (app.py) — Do Not Break

These keys must stay in `st.session_state`:

| Key | Type | Purpose |
|-----|------|---------|
| `analysis_results` | str | Raw analysis output |
| `feedback_sections` | dict | Rule-based feedback sections |
| `metrics` | dict | Extracted numeric metrics |
| `stem_results` | dict | Per-stem analysis data |
| `ai_feedback` | str | Claude's markdown feedback |
| `chat_history` | list | Conversation history for Claude |
| `audio_file_path` | str\|None | Temp file path — kept alive for agent tool calls |
| `key_results` | dict\|None | Key detection result — computed at analysis time |

---

## Critical Patterns — Never Remove

**1. Lazy Anthropic client init (`ai_agent.py`)**
The client is built on first call, not at import time. This is required for Streamlit Cloud
where `st.secrets` isn't available during module import. Do not move client initialization
to module level.

**2. File existence check before passing to agent (`app.py`)**
```python
live_path = st.session_state.audio_file_path
if live_path and not os.path.exists(live_path):
    live_path = None
```
On Streamlit Cloud temp files may not persist. Always verify before passing to Claude.

**3. Key detection at analysis time**
`detect_key()` is called immediately after analysis while the file exists, and stored in
`st.session_state.key_results`. Do not move this to the chat handler — the file may be
gone by then.

**4. API key priority**
Streamlit secrets are checked first, env var second. This order matters for Cloud deployment.

---

## Never Commit

- `.env` — contains the live Anthropic API key
- `.streamlit/secrets.toml` — Streamlit Cloud secrets
- `user_analytics.jsonl` — user session data
- `error_log.jsonl` — error logs
- `mcp_env/` — local virtualenv (gitignored)
- Any `.wav`, `.mp3`, or audio files

---

## Running Locally

```bash
# Install deps
pip install -r requirements.txt

# Add API key
cp .env.example .env
# Edit .env → add ANTHROPIC_API_KEY

# Start app with polling file watcher (avoids FSEvents error on macOS)
STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll streamlit run app.py
```
