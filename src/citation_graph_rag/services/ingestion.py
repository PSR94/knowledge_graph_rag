from typing import Any
from typing import List

from citation_graph_rag.config import AppSettings
from citation_graph_rag.domain import DocumentChunk
from citation_graph_rag.domain import DocumentInput
from citation_graph_rag.domain import IngestionReport
from citation_graph_rag.text import normalize_identifier
from citation_graph_rag.text import split_text


class IngestionService:
    def __init__(self, store: Any, llm: Any, settings: AppSettings):
        self._store = store
        self._llm = llm
        self._settings = settings

    def ingest_document(self, document: DocumentInput) -> IngestionReport:
        chunks = self._build_chunks(document)
        warnings = []
        entity_count = 0
        relationship_count = 0

        for chunk in chunks:
            payload = self._llm.extract(chunk, self._settings.extraction_model)
            if not payload.entities and not payload.relationships:
                warnings.append("Chunk {0} produced no graph structure.".format(chunk.position))
            entity_count += len(payload.entities)
            relationship_count += len(payload.relationships)
            self._store.store_chunk(chunk, payload)

        return IngestionReport(
            document_name=document.name,
            chunk_count=len(chunks),
            entity_count=entity_count,
            relationship_count=relationship_count,
            warnings=warnings,
        )

    def _build_chunks(self, document: DocumentInput) -> List[DocumentChunk]:
        parts = split_text(
            document.text,
            max_chars=self._settings.chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        prefix = normalize_identifier(document.name)
        return [
            DocumentChunk(
                id="{0}-chunk-{1}".format(prefix, index + 1),
                document_name=document.name,
                position=index + 1,
                text=part,
            )
            for index, part in enumerate(parts)
        ]
