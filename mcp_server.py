"""
MixBot MCP Server

Exposes audio analysis tools over the Model Context Protocol so any
MCP-compatible client (Cursor, Claude Desktop, etc.) can call them.

Run with:
    ./mcp_env/bin/python mcp_server.py

Or register in Cursor's MCP settings:
    {
      "mcpServers": {
        "mixbot": {
          "command": "/absolute/path/to/mixbot/mcp_env/bin/python",
          "args": ["/absolute/path/to/mixbot/mcp_server.py"]
        }
      }
    }

Requires Python 3.10+ (use the mcp_env virtualenv in this project).
"""

from mcp.server.fastmcp import FastMCP
from audio_tools import analyze_audio_file, get_spectral_features, get_mix_recommendations

mcp = FastMCP(
    "MixBot",
    instructions=(
        "You are MixBot, an expert mixing and mastering engineer. "
        "Use the available tools to analyze audio files and provide professional feedback. "
        "Always analyze the audio before giving advice — never guess at metrics. "
        "Call analyze_audio first, then spectral_features for deeper insight, "
        "then synthesize actionable recommendations."
    ),
)


@mcp.tool()
def analyze_audio(file_path: str) -> dict:
    """
    Analyze an audio file and return core mixing metrics.

    Returns: duration, sample rate, RMS level (dB), peak level (dB),
    dynamic range (dB), tempo (BPM), clipping status, silence percentage.

    Args:
        file_path: Absolute path to the audio file (.wav or .mp3).
    """
    return analyze_audio_file(file_path)


@mcp.tool()
def spectral_features(file_path: str) -> dict:
    """
    Extract spectral characteristics of an audio file.

    Returns: spectral centroid, bandwidth, rolloff, zero-crossing rate,
    and energy levels across frequency bands (sub-bass, bass, low-mid,
    mid, high-mid, air).

    Args:
        file_path: Absolute path to the audio file (.wav or .mp3).
    """
    return get_spectral_features(file_path)


@mcp.tool()
def mix_recommendations(
    file_path: str,
    daw: str = "",
    genre: str = "",
) -> dict:
    """
    Analyze an audio file and return structured mixing recommendations.

    Runs full analysis internally and returns a list of issues and
    actionable suggestions tailored to the specified DAW and genre.

    Args:
        file_path: Absolute path to the audio file (.wav or .mp3).
        daw: DAW name, e.g. "FL Studio", "Ableton Live", "Logic Pro X".
        genre: Genre or style, e.g. "hip-hop", "electronic", "pop".
    """
    metrics = analyze_audio_file(file_path)
    if "error" in metrics:
        return metrics
    return get_mix_recommendations(metrics, daw=daw, genre=genre)


if __name__ == "__main__":
    mcp.run()
