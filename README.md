# Egwu — AI Mixing Assistant

An AI-powered audio mixing engineer built with Claude, MCP, and Python DSP. *Egwu* means music and dance in Igbo.

Upload a track → Egwu analyzes it → Claude calls your audio tools autonomously → you get professional mixing feedback and can chat about your mix.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                    │
│   Upload → Analyze → AI Feedback → Chat          │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │     AI Agent          │
         │  (Claude tool-use)    │
         │                       │
         │  1. analyze_audio()   │
         │  2. spectral_features │
         │  3. mix_recommendations│
         └───────────┬───────────┘
                     │ calls
         ┌───────────▼───────────┐
         │     MCP Server        │  ◄── Also usable from Cursor
         │   (mcp_server.py)     │       and Claude Desktop
         │                       │
         │  • Audio DSP (librosa)│
         │  • Spectral analysis  │
         │  • Stem separation    │
         └───────────────────────┘
```

Claude doesn't just read pre-packaged numbers — it **calls the tools itself**, reasons across results, and writes the feedback. The same tools are exposed as a live **MCP server** that any MCP-compatible client (Cursor, Claude Desktop) can call directly.

---

## Features

- **Agentic AI Feedback** — Claude runs an autonomous tool-use loop: calls `analyze_audio`, `spectral_features`, and `mix_recommendations` in sequence, then synthesizes a full mixing report
- **Conversational Chat** — follow-up Q&A with the AI while your track's context is held in memory
- **MCP Server** — exposes your audio tools over the Model Context Protocol; connect to Cursor or Claude Desktop and analyze tracks from inside your IDE
- **Stem Separation** — separates audio into vocals, drums, bass, and other using Demucs (falls back to librosa HPSS + band filtering)
- **Per-Stem Analysis** — vocal clarity, sibilance, pitch range, kick punch, snare presence, bass weight, sub-bass energy
- **Spectral Analysis** — frequency band energy (sub-bass through air), centroid, rolloff, bandwidth
- **DAW-Specific Recommendations** — tailored plugin suggestions for FL Studio, Ableton, Logic Pro, Pro Tools, Cubase, Reaper, Studio One, Bitwig, and DJ software
- **Genre-Aware** — different loudness targets and recommendations for hip-hop, electronic, rock, pop, acoustic
- **Analytics & Error Tracking** — session analytics and structured error logging built in

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI / LLM | Anthropic Claude (tool-use API) |
| MCP Protocol | FastMCP (Python MCP SDK) |
| Audio DSP | librosa, soundfile, numpy, scipy |
| Stem Separation | Demucs (htdemucs model) + librosa HPSS fallback |
| Visualizations | Plotly |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/bginigeme/mixbot-ai-mixing-assistant.git
cd mixbot-ai-mixing-assistant
pip install -r requirements.txt
```

### 2. Add your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Get one at https://console.anthropic.com/
```

### 3. Run

```bash
STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll streamlit run app.py
```

Open **http://localhost:8501**

---

## MCP Server Setup (Cursor / Claude Desktop)

The MCP server runs in a separate Python 3.10+ environment.

```bash
# Install uv (fast Python environment manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the MCP environment
uv venv mcp_env --python 3.13
uv pip install -r mcp_requirements.txt --python mcp_env/bin/python
```

Then add to your Cursor MCP config (`Settings → MCP → Edit config`):

```json
{
  "mcpServers": {
    "mixbot": {
      "command": "/absolute/path/to/mixbot/mcp_env/bin/python",
      "args": ["/absolute/path/to/mixbot/mcp_server.py"]
    }
  }
}
```

Now you can ask Cursor: *"Analyze `/path/to/track.wav` and tell me what's wrong with the mix"* — and it will call your tools directly.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_audio` | Core metrics: RMS, peak, dynamic range, tempo, clipping, silence |
| `spectral_features` | Frequency band energies, centroid, bandwidth, rolloff |
| `mix_recommendations` | Structured issues + suggestions list, DAW and genre aware |

---

## Project Structure

```
mixbot/
├── app.py                  # Streamlit web application
├── ai_agent.py             # Claude agentic loop (tool-use)
├── mcp_server.py           # FastMCP server (MCP protocol)
├── audio_tools.py          # Shared DSP functions (used by agent + MCP)
├── audio_analyzer.py       # Core analysis engine
├── stem_separator.py       # Stem separation (Demucs + librosa fallback)
├── requirements.txt        # Main app dependencies (Python 3.9+)
├── mcp_requirements.txt    # MCP server dependencies (Python 3.10+)
├── packages.txt            # System packages for Streamlit Cloud
└── .env.example            # Environment variable template
```

---

## Streamlit Cloud Deployment

1. Fork or push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo, branch `main` (or `development`), entry point `app.py`
4. In **Advanced settings → Secrets**, add:

```toml
ANTHROPIC_API_KEY = "your_key_here"
```

5. Deploy — the app works without Demucs/PyTorch on Cloud (librosa fallback handles stem separation)

---

## Resume Description

```
Egwu — AI Mixing Assistant
• Built a custom MCP server exposing audio DSP tools as callable tools
  for AI agents via the Model Context Protocol (Cursor, Claude Desktop)
• Implemented an agentic Claude loop (Anthropic tool-use API) that
  autonomously calls analyze_audio → spectral_features → key_detection → mix_recommendations
  and synthesizes professional mixing feedback
• Full-stack: Streamlit UI, Python DSP (librosa), Demucs stem separation,
  spectral analysis, conversational AI chat, session analytics
• Stack: Python, Anthropic Claude API, FastMCP, librosa, Demucs, Streamlit
```
