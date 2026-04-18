import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AppSettings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    ollama_host: str
    extraction_model: str
    answer_model: str
    max_hops: int
    max_evidence: int
    chunk_size: int
    chunk_overlap: int

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            extraction_model=os.getenv("EXTRACTION_MODEL", "llama3.2"),
            answer_model=os.getenv("ANSWER_MODEL", "llama3.2"),
            max_hops=int(os.getenv("MAX_HOPS", "2")),
            max_evidence=int(os.getenv("MAX_EVIDENCE", "8")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
        )

    def model_options(self) -> List[str]:
        ordered = [
            self.answer_model,
            self.extraction_model,
            "llama3.2",
            "mistral",
            "phi3",
        ]
        unique = []
        for model in ordered:
            if model not in unique:
                unique.append(model)
        return unique
