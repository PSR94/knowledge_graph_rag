# 🔍 Knowledge Graph RAG with Verifiable Citations

A Streamlit application demonstrating how **Knowledge Graph-based Retrieval-Augmented Generation (RAG)** provides multi-hop reasoning with fully verifiable source attribution.

## 🎯 What Makes This Different?

Traditional vector-based RAG finds similar text chunks, but struggles with:
- Questions requiring information from multiple documents
- Complex reasoning chains
- Providing verifiable sources for each claim

**Knowledge Graph RAG** solves these by:
1. **Building a structured graph** of entities and relationships from documents
2. **Traversing connections** to find related information (multi-hop reasoning)
3. **Tracking provenance** so every claim links back to its source

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **Multi-hop Reasoning** | Traverse entity relationships to answer complex questions |
| 📚 **Verifiable Citations** | Every claim includes source document and text |
| 🧠 **Reasoning Trace** | See exactly how the answer was derived |
| 🏠 **Fully Local** | Uses Ollama for LLM, Neo4j for graph storage |

## 🚀 Quick Start

### Prerequisites

1. **Ollama** - Local LLM inference
   ```bash
   # Install from https://ollama.ai
   ollama pull llama3.2
   ```

2. **Neo4j** - Knowledge graph database
   ```bash
   # Using Docker
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

### Installation

```bash
# Clone and navigate
git clone <your-github-repo-url>
cd knowledge_graph_rag_citations

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run knowledge_graph_rag.py
```

The app also reads these environment variables when present:

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `OLLAMA_HOST`
- `LLM_MODEL`

That means the included Docker setup works without manually changing the Streamlit sidebar.

### Run With Docker Compose

```bash
docker compose up --build
```

Then open:

- Streamlit app: `http://localhost:8501`
- Neo4j browser: `http://localhost:7474`

Default credentials:

- Neo4j user: `neo4j`
- Neo4j password: `password`

## 📖 How It Works

### Step 1: Document → Knowledge Graph

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Document      │ ──► │  LLM Extraction  │ ──► │ Knowledge Graph │
│   (Text/PDF)    │     │  (Entities+Rels) │     │    (Neo4j)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

The LLM extracts:
- **Entities**: People, organizations, concepts, technologies
- **Relationships**: How entities connect (e.g., "works_for", "created", "uses")
- **Provenance**: Source document and chunk for each extraction

### Step 2: Query → Multi-hop Traversal

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐
│  Query  │ ──► │  Find Start │ ──► │  Traverse   │ ──► │  Context  │
│         │     │   Entities  │     │  Relations  │     │  + Sources│
└─────────┘     └─────────────┘     └─────────────┘     └───────────┘
```

### Step 3: Answer → Verified Citations

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Context   │ ──► │  Generate   │ ──► │  Answer with     │
│ + Sources   │     │   Answer    │     │  [1][2] Citations│
└─────────────┘     └─────────────┘     └──────────────────┘
                                                │
                                                ▼
                                        ┌──────────────────┐
                                        │ Citation Details │
                                        │ • Source Doc     │
                                        │ • Source Text    │
                                        │ • Reasoning Path │
                                        └──────────────────┘
```

## 🖥️ Usage Example

### 1. Add a Document

Paste or select a sample document. The system extracts entities and relationships:

```
Document: "GraphRAG was developed by Microsoft Research. 
           Darren Edge led the project..."

Extracted:
  ├── Entity: GraphRAG (TECHNOLOGY)
  ├── Entity: Microsoft Research (ORGANIZATION)  
  ├── Entity: Darren Edge (PERSON)
  └── Relationship: Darren Edge --[WORKS_FOR]--> Microsoft Research
```

### 2. Ask a Question

```
Question: "Who developed GraphRAG and what organization are they from?"
```

### 3. Get Verified Answer

```
Answer: GraphRAG was developed by researchers at Microsoft Research [1], 
        with Darren Edge leading the project [2].

Citations:
  [1] Source: AI Research Paper
      Text: "GraphRAG is a technique developed by Microsoft Research..."
      
  [2] Source: AI Research Paper  
      Text: "...introduced by researchers including Darren Edge..."
```

## 🔧 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Neo4j URI | `bolt://localhost:7687` or `bolt://neo4j:7687` in Docker | Neo4j connection string |
| Neo4j User | `neo4j` | Database username |
| Neo4j Password | `password` in the sample setup | Database password |
| LLM Model | `llama3.2` | Ollama model for extraction/generation |

## 🏗️ Architecture

```
knowledge_graph_rag_citations/
├── knowledge_graph_rag.py   # Main Streamlit application
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Key Components

- **`KnowledgeGraphManager`**: Neo4j interface for graph operations
- **`extract_entities_with_llm()`**: LLM-based entity/relationship extraction
- **`generate_answer_with_citations()`**: Multi-hop RAG with provenance tracking

## 🎓 Learn More

This example is inspired by [VeritasGraph](https://github.com/bibinprathap/VeritasGraph), an enterprise-grade framework for:
- On-premise knowledge graph RAG
- Visual reasoning traces (Veritas-Scope)
- LoRA-tuned LLM integration

## 📝 License

MIT License
