from typing import Iterable

from citation_graph_rag.domain import Evidence


def build_extraction_prompt(chunk_text: str) -> str:
    return """Extract structured knowledge from the passage below.

Return valid JSON with this shape:
{{
  "entities": [
    {{
      "name": "canonical display name",
      "kind": "PERSON | TEAM | SYSTEM | PRODUCT | ORGANIZATION | DATASET | CONCEPT | EVENT | LOCATION",
      "summary": "short factual summary grounded in the passage"
    }}
  ],
  "relationships": [
    {{
      "source": "entity name",
      "target": "entity name",
      "kind": "OWNS | DEPENDS_ON | REPORTS_TO | BUILDS | OPERATES | USES | SUPPORTS | LOCATED_IN | RELATED_TO",
      "summary": "short factual description grounded in the passage"
    }}
  ]
}}

Rules:
- Keep summaries factual and concise.
- Do not invent missing entities or relationships.
- Prefer stable entity names over pronouns.
- Return empty arrays when the passage has no useful structure.

Passage:
{0}
""".format(chunk_text)


def build_answer_prompt(query: str, evidence: Iterable[Evidence]) -> str:
    evidence_blocks = []
    for item in evidence:
        evidence_blocks.append(
            """[{ref_id}]
Entity: {entity_name}
Type: {entity_type}
Summary: {summary}
Source document: {source_document}
Source excerpt: {source_excerpt}
Reasoning path: {reasoning_path}
""".format(
                ref_id=item.ref_id,
                entity_name=item.entity_name,
                entity_type=item.entity_type,
                summary=item.summary,
                source_document=item.source_document,
                source_excerpt=item.source_excerpt,
                reasoning_path=" | ".join(item.reasoning_path),
            )
        )

    return """Answer the question using only the evidence catalog below.

Requirements:
- Cite every factual claim with one or more references using the exact evidence ids, for example [E1].
- If the evidence is incomplete, say what is uncertain.
- Do not mention any source that is not in the catalog.
- Keep the answer concise and operational.

Question:
{0}

Evidence catalog:
{1}
""".format(query, "\n".join(evidence_blocks))
