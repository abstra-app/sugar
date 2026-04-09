from pygls.lsp.server import LanguageServer
from lsprotocol import types

from .semantic_tokens import TOKEN_MODIFIERS, TOKEN_TYPES, get_semantic_tokens
from .state import DocumentState


def create_server() -> LanguageServer:
    server = LanguageServer("sugar-lsp", "v0.1.0")
    documents: dict[str, DocumentState] = {}

    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: types.DidOpenTextDocumentParams):
        uri = params.text_document.uri
        documents[uri] = DocumentState(uri, params.text_document.text)
        _publish_diagnostics(server, documents[uri])

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: types.DidChangeTextDocumentParams):
        uri = params.text_document.uri
        doc = server.workspace.get_text_document(uri)
        if uri in documents:
            documents[uri].update(doc.source)
        else:
            documents[uri] = DocumentState(uri, doc.source)
        _publish_diagnostics(server, documents[uri])

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params: types.DidCloseTextDocumentParams):
        documents.pop(params.text_document.uri, None)

    @server.feature(
        types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
        types.SemanticTokensOptions(
            legend=types.SemanticTokensLegend(
                token_types=TOKEN_TYPES,
                token_modifiers=TOKEN_MODIFIERS,
            ),
            full=True,
        ),
    )
    def semantic_tokens_full(params: types.SemanticTokensParams):
        uri = params.text_document.uri
        doc = documents.get(uri)
        if doc is None:
            return types.SemanticTokens(data=[])
        data = get_semantic_tokens(doc.source)
        return types.SemanticTokens(data=data)

    @server.feature(
        types.TEXT_DOCUMENT_COMPLETION,
        types.CompletionOptions(trigger_characters=[".", "=", " "]),
    )
    def completions(params: types.CompletionParams):
        from .completion import get_completions
        uri = params.text_document.uri
        doc = documents.get(uri)
        if doc is None:
            return types.CompletionList(is_incomplete=False, items=[])
        items = get_completions(doc, params.position.line, params.position.character)
        return types.CompletionList(is_incomplete=False, items=items)

    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    def definition(params: types.DefinitionParams):
        from .definition import get_definition
        uri = params.text_document.uri
        doc = documents.get(uri)
        if doc is None:
            return None
        return get_definition(doc, params.position.line, params.position.character)

    @server.feature(types.TEXT_DOCUMENT_HOVER)
    def hover(params: types.HoverParams):
        from .hover import get_hover
        uri = params.text_document.uri
        doc = documents.get(uri)
        if doc is None:
            return None
        return get_hover(doc, params.position.line, params.position.character)

    @server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbols(params: types.DocumentSymbolParams):
        from .symbols import get_document_symbols
        uri = params.text_document.uri
        doc = documents.get(uri)
        if doc is None:
            return []
        return get_document_symbols(doc)

    return server


def _publish_diagnostics(server: LanguageServer, state: DocumentState) -> None:
    server.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=state.uri,
            diagnostics=state.diagnostics,
        )
    )
