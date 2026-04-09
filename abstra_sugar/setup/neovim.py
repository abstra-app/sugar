import shutil
import sys
from pathlib import Path

_EDITORS_DIR = Path(__file__).parent.parent.parent / "editors" / "vim"


def _install_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    shutil.copy2(src, dst)
    print(f"  Installed {dst}")


def setup_neovim() -> None:
    nvim_dir = Path.home() / ".config" / "nvim"
    if not nvim_dir.exists():
        print(f"Neovim config directory not found: {nvim_dir}")
        print("Is Neovim installed?")
        sys.exit(1)

    _install_file(_EDITORS_DIR / "ftdetect" / "sugar.vim", nvim_dir / "ftdetect" / "sugar.vim")
    _install_file(_EDITORS_DIR / "syntax" / "sugar.vim", nvim_dir / "syntax" / "sugar.vim")
    _install_file(_EDITORS_DIR / "lsp.lua", nvim_dir / "after" / "plugin" / "sugar-lsp.lua")

    print()
    print("Sugar LSP configured for Neovim.")
    print("Restart Neovim and open a .sugar file.")
