from lsprotocol import types

from .server import create_server


def test_server_creates():
    server = create_server()
    assert server is not None
    assert server.name == "sugar-lsp"


def test_server_has_semantic_tokens():
    server = create_server()
    assert types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL in server.protocol.fm.features


def test_server_has_completion():
    server = create_server()
    assert types.TEXT_DOCUMENT_COMPLETION in server.protocol.fm.features


def test_server_has_definition():
    server = create_server()
    assert types.TEXT_DOCUMENT_DEFINITION in server.protocol.fm.features


def test_server_has_hover():
    server = create_server()
    assert types.TEXT_DOCUMENT_HOVER in server.protocol.fm.features


def test_server_has_document_symbols():
    server = create_server()
    assert types.TEXT_DOCUMENT_DOCUMENT_SYMBOL in server.protocol.fm.features
