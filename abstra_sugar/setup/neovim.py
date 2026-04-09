import shutil
import sys
from pathlib import Path

_EDITORS_DIR = Path(__file__).parent.parent.parent / "editors" / "vim"


def setup_neovim() -> None:
    nvim_dir = Path.home() / ".config" / "nvim"
    if not nvim_dir.exists():
        print(f"Neovim config directory not found: {nvim_dir}")
        print("Is Neovim installed?")
        sys.exit(1)

    # Copy ftdetect
    ftdetect_dst = nvim_dir / "ftdetect" / "sugar.vim"
    ftdetect_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_EDITORS_DIR / "ftdetect" / "sugar.vim", ftdetect_dst)
    print(f"  Installed {ftdetect_dst}")

    # Copy syntax
    syntax_dst = nvim_dir / "syntax" / "sugar.vim"
    syntax_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_EDITORS_DIR / "syntax" / "sugar.vim", syntax_dst)
    print(f"  Installed {syntax_dst}")

    # Copy LSP config
    lsp_dst = nvim_dir / "after" / "plugin" / "sugar-lsp.lua"
    lsp_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_EDITORS_DIR / "lsp.lua", lsp_dst)
    print(f"  Installed {lsp_dst}")

    print()
    print("Sugar LSP configured for Neovim.")
    print("Restart Neovim and open a .sugar file.")
