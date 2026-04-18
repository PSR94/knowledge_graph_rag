import unittest

from citation_graph_rag.services.question_answering import build_evidence_register
from citation_graph_rag.services.question_answering import parse_citation_refs


class QuestionAnsweringHelpersTest(unittest.TestCase):
    def test_build_evidence_register_deduplicates_sources(self) -> None:
        direct_hits = [
            {
                "entity_name": "Graph Services",
                "entity_type": "TEAM",
                "summary": "Owns extraction quality.",
                "source_document": "Ops Memo",
                "source_excerpt": "Graph Services owns extraction quality.",
                "reasoning_path": ["Direct match for: graph"],
            },
            {
                "entity_name": "Graph Services",
                "entity_type": "TEAM",
                "summary": "Owns extraction quality.",
                "source_document": "Ops Memo",
                "source_excerpt": "Graph Services owns extraction quality.",
                "reasoning_path": ["Direct match for: graph"],
            },
        ]

        evidence = build_evidence_register(direct_hits, neighborhood_hits=[], limit=6)

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].ref_id, "E1")

    def test_parse_citation_refs_keeps_first_seen_order(self) -> None:
        refs = parse_citation_refs(
            "Graph Services owns ingestion [E2]. Search validates rollout [E1]. Repeat [E2]."
        )

        self.assertEqual(refs, ["E2", "E1"])


if __name__ == "__main__":
    unittest.main()
