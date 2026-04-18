import unittest

from citation_graph_rag.prompts import build_extraction_prompt


class PromptBuilderTest(unittest.TestCase):
    def test_extraction_prompt_keeps_literal_json_schema(self) -> None:
        prompt = build_extraction_prompt("Alice owns the ingestion service.")

        self.assertIn('"entities"', prompt)
        self.assertIn('"relationships"', prompt)
        self.assertIn("Alice owns the ingestion service.", prompt)


if __name__ == "__main__":
    unittest.main()
