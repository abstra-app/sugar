from pygls.lsp.server import LanguageServer


def create_server() -> LanguageServer:
    server = LanguageServer("sugar-lsp", "v0.1.0")
    return server
