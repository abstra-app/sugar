from pygls.lsp.server import LanguageServer
from lsprotocol import types


def create_server() -> LanguageServer:
    server = LanguageServer("sugar-lsp", "v0.1.0")
    return server
