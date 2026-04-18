# Evidence Graph RAG

Evidence Graph RAG is a local-first application for ingesting operational documents into Neo4j and answering questions with explicit evidence references. The project is organized as a small Python package with separate adapters, services, domain models, and a thin Streamlit interface.

## What The Application Does

- Splits raw documents into manageable chunks for extraction.
- Uses Ollama to derive entities and relationships from each chunk.
- Persists graph structure and source excerpts in Neo4j.
- Retrieves direct matches plus graph neighbors for a question.
- Produces answers that cite the exact evidence records used during generation.

## Repository Layout

```text
.
├── app.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── src/citation_graph_rag
│   ├── adapters
│   ├── domain
│   ├── services
│   ├── config.py
│   ├── prompts.py
│   ├── samples.py
│   └── text.py
└── tests
```

## Architecture

The codebase is intentionally layered.

- `domain`: immutable data structures that define the application contract.
- `adapters`: infrastructure integrations for Neo4j and Ollama.
- `services`: ingestion and question-answering workflows.
- `app.py`: Streamlit orchestration and user interaction.

This keeps graph persistence, prompt construction, retrieval logic, and presentation concerns isolated from each other.

## Prerequisites

- Python 3.9 or newer
- Docker for Neo4j, unless you already run Neo4j elsewhere
- Ollama with at least one local model, such as `llama3.2`

Pull the default model:

```bash
ollama pull llama3.2
```

## Local Setup

Install the package in editable mode:

```bash
git clone https://github.com/PavanSai-Rayalla/knowledge_graph_rag.git
cd knowledge_graph_rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start Neo4j:

```bash
docker run -d \
  --name evidence-graph-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

Run the application:

```bash
streamlit run app.py
```

## Docker Compose

The repository includes a compose file for Neo4j, Ollama, and the application.

```bash
docker compose up --build
```

Endpoints:

- Streamlit: `http://localhost:8501`
- Neo4j Browser: `http://localhost:7474`

Default Neo4j credentials:

- Username: `neo4j`
- Password: `password`

## Configuration

The runtime reads these environment variables:

| Variable | Default |
| --- | --- |
| `NEO4J_URI` | `bolt://localhost:7687` |
| `NEO4J_USER` | `neo4j` |
| `NEO4J_PASSWORD` | `password` |
| `OLLAMA_HOST` | `http://localhost:11434` |
| `EXTRACTION_MODEL` | `llama3.2` |
| `ANSWER_MODEL` | `llama3.2` |
| `MAX_HOPS` | `2` |
| `MAX_EVIDENCE` | `8` |
| `CHUNK_SIZE` | `900` |
| `CHUNK_OVERLAP` | `120` |

## Development Notes

Run tests:

```bash
python3 -m unittest discover -s tests
```

The current test suite covers pure logic in the chunking and citation assembly paths. Integration with Neo4j and Ollama remains an environment-level concern and should be exercised in a local or CI environment with those services available.

## License

MIT
