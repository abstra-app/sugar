import sys

USAGE = """\
Usage: abstra-sugar <command>

Commands:
  lsp              Start the Language Server (stdio)
  setup neovim     Install Sugar support for Neovim
  setup vscode     Install Sugar support for VS Code\
"""


def main():
    args = sys.argv[1:]

    if args == ["lsp"]:
        from .lsp.server import create_server

        server = create_server()
        server.start_io()
    elif args == ["setup", "neovim"]:
        from .setup.neovim import setup_neovim

        setup_neovim()
    elif args == ["setup", "vscode"]:
        from .setup.vscode import setup_vscode

        setup_vscode()
    else:
        print(USAGE)
        sys.exit(1)
