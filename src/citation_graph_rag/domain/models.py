from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DocumentInput:
    name: str
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document_name: str
    position: int
    text: str


@dataclass(frozen=True)
class EntityMention:
    id: str
    name: str
    kind: str
    summary: str
    document_name: str
    chunk_id: str
    excerpt: str


@dataclass(frozen=True)
class RelationshipMention:
    source_name: str
    target_name: str
    kind: str
    summary: str
    document_name: str
    chunk_id: str


@dataclass(frozen=True)
class ExtractionPayload:
    entities: List[EntityMention]
    relationships: List[RelationshipMention]


@dataclass(frozen=True)
class Evidence:
    ref_id: str
    entity_name: str
    entity_type: str
    summary: str
    source_document: str
    source_excerpt: str
    reasoning_path: List[str]


@dataclass(frozen=True)
class Citation:
    ref_id: str
    source_document: str
    source_excerpt: str
    entity_name: str
    reasoning_path: List[str]


@dataclass(frozen=True)
class AnswerPacket:
    answer: str
    citations: List[Citation]
    trace: List[str]


@dataclass(frozen=True)
class IngestionReport:
    document_name: str
    chunk_count: int
    entity_count: int
    relationship_count: int
    warnings: List[str]
