import re
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from citation_graph_rag.config import AppSettings
from citation_graph_rag.domain import AnswerPacket
from citation_graph_rag.domain import Citation
from citation_graph_rag.domain import Evidence
from citation_graph_rag.text import extract_query_terms


class QuestionAnsweringService:
    def __init__(self, store: Any, llm: Any, settings: AppSettings):
        self._store = store
        self._llm = llm
        self._settings = settings

    def answer_question(self, question: str) -> AnswerPacket:
        trace = ["Received question: {0}".format(question)]
        direct_hits = []

        query_terms = extract_query_terms(question)
        trace.append("Query terms: {0}".format(", ".join(query_terms) if query_terms else "none"))
        for term in query_terms or [question.lower()]:
            direct_hits.extend(self._store.search_entities(term, limit=3))

        trace.append("Direct matches collected: {0}".format(len(direct_hits)))

        neighborhood_hits = []
        seed_names = []
        for hit in direct_hits:
            name = str(hit.get("entity_name", ""))
            if name and name not in seed_names:
                seed_names.append(name)
        for name in seed_names[:3]:
            expanded = self._store.expand_neighborhood(name, hops=self._settings.max_hops, limit=4)
            neighborhood_hits.extend(expanded)
            trace.append("Expanded neighborhood for {0}: {1} hits".format(name, len(expanded)))

        evidence = build_evidence_register(direct_hits, neighborhood_hits, limit=self._settings.max_evidence)
        trace.append("Evidence catalog size: {0}".format(len(evidence)))

        if not evidence:
            return AnswerPacket(
                answer="No evidence matched the question. Ingest a document first or ask a narrower question.",
                citations=[],
                trace=trace,
            )

        answer = self._llm.answer(question, evidence, self._settings.answer_model)
        evidence_map = {item.ref_id: item for item in evidence}
        citations = build_citations(answer, evidence_map)
        trace.append("Citations resolved: {0}".format(len(citations)))
        return AnswerPacket(answer=answer, citations=citations, trace=trace)


def build_evidence_register(
    direct_hits: Iterable[Dict[str, object]],
    neighborhood_hits: Iterable[Dict[str, object]],
    limit: int,
) -> List[Evidence]:
    evidence = []
    seen = set()

    for source in [direct_hits, neighborhood_hits]:
        for item in source:
            signature = (
                str(item.get("entity_name", "")),
                str(item.get("source_document", "")),
                str(item.get("summary", "")),
            )
            if signature in seen:
                continue
            seen.add(signature)
            evidence.append(
                Evidence(
                    ref_id="E{0}".format(len(evidence) + 1),
                    entity_name=str(item.get("entity_name", "Unknown entity")),
                    entity_type=str(item.get("entity_type", "CONCEPT")),
                    summary=str(item.get("summary", "")),
                    source_document=str(item.get("source_document", "Unknown source")),
                    source_excerpt=str(item.get("source_excerpt", "")).strip(),
                    reasoning_path=[str(part) for part in item.get("reasoning_path", []) if str(part).strip()],
                )
            )
            if len(evidence) >= limit:
                return evidence
    return evidence


def parse_citation_refs(answer: str) -> List[str]:
    refs = re.findall(r"\[(E\d+)\]", answer)
    ordered = []
    for ref in refs:
        if ref not in ordered:
            ordered.append(ref)
    return ordered


def build_citations(answer: str, evidence_map: Dict[str, Evidence]) -> List[Citation]:
    citations = []
    for ref in parse_citation_refs(answer):
        evidence = evidence_map.get(ref)
        if evidence is None:
            continue
        citations.append(
            Citation(
                ref_id=evidence.ref_id,
                source_document=evidence.source_document,
                source_excerpt=evidence.source_excerpt,
                entity_name=evidence.entity_name,
                reasoning_path=evidence.reasoning_path,
            )
        )
    return citations
