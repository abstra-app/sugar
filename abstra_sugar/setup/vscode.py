import shutil
import subprocess
import sys
from pathlib import Path

_VSCODE_EXT_DIR = Path(__file__).parent / "vscode_extension"


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
    print(f"  Installed extension to {dst}")

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
