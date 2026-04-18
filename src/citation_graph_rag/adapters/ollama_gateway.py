import json
from typing import Dict
from typing import List

from ollama import Client

from citation_graph_rag.domain import DocumentChunk
from citation_graph_rag.domain import EntityMention
from citation_graph_rag.domain import Evidence
from citation_graph_rag.domain import ExtractionPayload
from citation_graph_rag.domain import RelationshipMention
from citation_graph_rag.prompts import build_answer_prompt
from citation_graph_rag.prompts import build_extraction_prompt
from citation_graph_rag.text import normalize_identifier


class OllamaGateway:
    def __init__(self, host: str):
        self._client = Client(host=host)

    def extract(self, chunk: DocumentChunk, model: str) -> ExtractionPayload:
        response = self._client.chat(
            model=model,
            messages=[{"role": "user", "content": build_extraction_prompt(chunk.text)}],
            format="json",
        )
        data = json.loads(response["message"]["content"])
        return ExtractionPayload(
            entities=self._parse_entities(data.get("entities", []), chunk),
            relationships=self._parse_relationships(data.get("relationships", []), chunk),
        )

    def answer(self, question: str, evidence: List[Evidence], model: str) -> str:
        response = self._client.chat(
            model=model,
            messages=[{"role": "user", "content": build_answer_prompt(question, evidence)}],
        )
        return response["message"]["content"].strip()

    def _parse_entities(self, raw_entities: List[Dict[str, str]], chunk: DocumentChunk) -> List[EntityMention]:
        entities = []
        seen = set()
        for item in raw_entities:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            entities.append(
                EntityMention(
                    id=normalize_identifier("{0}-{1}-{2}".format(chunk.document_name, chunk.id, name)),
                    name=name,
                    kind=str(item.get("kind", "CONCEPT")).strip().upper() or "CONCEPT",
                    summary=str(item.get("summary", "")).strip() or "No summary provided.",
                    document_name=chunk.document_name,
                    chunk_id=chunk.id,
                    excerpt=chunk.text[:280].strip(),
                )
            )
        return entities

    def _parse_relationships(
        self,
        raw_relationships: List[Dict[str, str]],
        chunk: DocumentChunk,
    ) -> List[RelationshipMention]:
        relationships = []
        seen = set()
        for item in raw_relationships:
            source_name = str(item.get("source", "")).strip()
            target_name = str(item.get("target", "")).strip()
            relation = str(item.get("kind", "RELATED_TO")).strip().upper() or "RELATED_TO"
            if not source_name or not target_name:
                continue
            key = (source_name.lower(), target_name.lower(), relation)
            if key in seen:
                continue
            seen.add(key)
            relationships.append(
                RelationshipMention(
                    source_name=source_name,
                    target_name=target_name,
                    kind=relation,
                    summary=str(item.get("summary", "")).strip() or relation.replace("_", " ").title(),
                    document_name=chunk.document_name,
                    chunk_id=chunk.id,
                )
            )
        return relationships
