import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _install_test_stubs() -> None:
    mlx_whisper = types.ModuleType("mlx_whisper")
    mlx_whisper.transcribe = lambda *_args, **_kwargs: {"text": ""}
    sys.modules.setdefault("mlx_whisper", mlx_whisper)

    mlx_audio = types.ModuleType("mlx_audio")
    tts = types.ModuleType("mlx_audio.tts")
    utils = types.ModuleType("mlx_audio.tts.utils")
    utils.load_model = lambda *_args, **_kwargs: types.SimpleNamespace(
        generate=lambda *_a, **_k: []
    )
    tts.utils = utils
    mlx_audio.tts = tts
    sys.modules.setdefault("mlx_audio", mlx_audio)
    sys.modules.setdefault("mlx_audio.tts", tts)
    sys.modules.setdefault("mlx_audio.tts.utils", utils)

    mlx_lm = types.ModuleType("mlx_lm")
    mlx_lm.generate = lambda *_args, **_kwargs: ""
    mlx_lm.load = lambda *_args, **_kwargs: (object(), object())
    mlx_lm.stream_generate = lambda *_args, **_kwargs: []
    sys.modules.setdefault("mlx_lm", mlx_lm)

    mcp = types.ModuleType("mcp")
    mcp_types = types.SimpleNamespace(
        CallToolResult=object,
        TextContent=type("TextContent", (), {}),
    )
    mcp.ClientSession = object
    mcp.StdioServerParameters = object
    mcp.types = mcp_types
    sys.modules.setdefault("mcp", mcp)

    mcp_client = types.ModuleType("mcp.client")
    mcp_stdio = types.ModuleType("mcp.client.stdio")
    mcp_stdio.stdio_client = lambda *_args, **_kwargs: None
    mcp_client.stdio = mcp_stdio
    sys.modules.setdefault("mcp.client", mcp_client)
    sys.modules.setdefault("mcp.client.stdio", mcp_stdio)


_install_test_stubs()
