import unittest

from citation_graph_rag.text import extract_query_terms
from citation_graph_rag.text import split_text


class TextUtilitiesTest(unittest.TestCase):
    def test_split_text_respects_boundaries(self) -> None:
        text = " ".join("token{0}".format(index) for index in range(220))
        chunks = split_text(text, max_chars=120, overlap=20)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks[:-1]))

    def test_extract_query_terms_preserves_order_and_deduplicates(self) -> None:
        terms = extract_query_terms("Which team owns the graph graph pipeline and answer service?")

        self.assertEqual(terms, ["which", "team", "owns", "the", "graph", "pipeline"])


if __name__ == "__main__":
    unittest.main()
