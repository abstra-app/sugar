import shutil
import subprocess
import sys
from pathlib import Path

_VSCODE_EXT_DIR = Path(__file__).parent / "vscode_extension"

_EXTENSION_JS = """\
const {{ LanguageClient, TransportKind }} = require("vscode-languageclient/node");

let client;

function activate(context) {{
  const serverOptions = {{
    command: "{python_path}",
    args: ["-m", "abstra_sugar.lsp"],
    transport: TransportKind.stdio,
  }};

  const clientOptions = {{
    documentSelector: [{{ scheme: "file", language: "sugar" }}],
  }};

  client = new LanguageClient(
    "sugar-lsp",
    "Sugar Language Server",
    serverOptions,
    clientOptions
  );

  client.start();
}}

function deactivate() {{
  if (client) {{
    return client.stop();
  }}
}}

module.exports = {{ activate, deactivate }};
"""


def setup_vscode() -> None:
    extensions_dir = _find_extensions_dir()
    if extensions_dir is None:
        print("Could not find VS Code extensions directory.")
        print("Is VS Code installed?")
        sys.exit(1)

    dst = extensions_dir / "sugar-lsp"
    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(_VSCODE_EXT_DIR, dst)

    # Write extension.js with resolved Python path
    python_path = sys.executable
    (dst / "extension.js").write_text(
        _EXTENSION_JS.format(python_path=python_path)
    )
    print(f"  Installed extension to {dst}")
    print(f"  Server command: {python_path} -m abstra_sugar.lsp")

    # Install npm dependencies
    print("  Installing dependencies...")
    result = subprocess.run(
        ["npm", "install", "--production"],
        cwd=dst,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  npm install failed: {result.stderr}")
        sys.exit(1)

    print()
    print("Sugar LSP extension installed for VS Code.")
    print("Restart VS Code and open a .sugar file.")


def _find_extensions_dir() -> Path | None:
    import platform

    system = platform.system()
    home = Path.home()

    candidates = []
    if system == "Darwin":
        candidates = [
            home / ".vscode" / "extensions",
            home / ".vscode-insiders" / "extensions",
        ]
    elif system == "Linux":
        candidates = [
            home / ".vscode" / "extensions",
            home / ".vscode-server" / "extensions",
            home / ".vscode-insiders" / "extensions",
        ]
    elif system == "Windows":
        candidates = [
            home / ".vscode" / "extensions",
            home / ".vscode-insiders" / "extensions",
        ]

    for path in candidates:
        if path.exists():
            return path

    # Default: create the standard one
    default = home / ".vscode" / "extensions"
    default.mkdir(parents=True, exist_ok=True)
    return default
