import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "lsp":
        from .lsp.server import create_server

        server = create_server()
        server.start_io()
    else:
        print("Usage: abstra-sugar lsp")
        sys.exit(1)
