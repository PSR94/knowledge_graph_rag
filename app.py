from typing import Iterable

import streamlit as st

from citation_graph_rag.adapters.neo4j_gateway import Neo4jGateway
from citation_graph_rag.adapters.ollama_gateway import OllamaGateway
from citation_graph_rag.config import AppSettings
from citation_graph_rag.domain import DocumentInput
from citation_graph_rag.samples import SAMPLE_DOCUMENTS
from citation_graph_rag.services.ingestion import IngestionService
from citation_graph_rag.services.question_answering import QuestionAnsweringService


def main() -> None:
    st.set_page_config(
        page_title="Evidence Graph RAG",
        page_icon="KG",
        layout="wide",
    )
    base_settings = AppSettings.from_env()
    settings = render_sidebar(base_settings)
    initialize_session_state()

    st.title("Evidence Graph RAG")
    st.caption(
        "Local question answering over a Neo4j knowledge graph with explicit evidence and traceable citations."
    )

    ingest_tab, ask_tab, admin_tab = st.tabs(["Ingest", "Ask", "Operate"])

    with ingest_tab:
        render_ingest_tab(settings)

    with ask_tab:
        render_question_tab(settings)

    with admin_tab:
        render_operations_tab(settings)


def render_sidebar(base_settings: AppSettings) -> AppSettings:
    st.sidebar.header("Configuration")
    model_options = base_settings.model_options()

    neo4j_uri = st.sidebar.text_input("Neo4j URI", value=base_settings.neo4j_uri)
    neo4j_user = st.sidebar.text_input("Neo4j User", value=base_settings.neo4j_user)
    neo4j_password = st.sidebar.text_input(
        "Neo4j Password",
        value=base_settings.neo4j_password,
        type="password",
    )
    ollama_host = st.sidebar.text_input("Ollama Host", value=base_settings.ollama_host)
    extraction_model = st.sidebar.selectbox(
        "Extraction Model",
        model_options,
        index=model_options.index(base_settings.extraction_model),
    )
    answer_model = st.sidebar.selectbox(
        "Answer Model",
        model_options,
        index=model_options.index(base_settings.answer_model),
    )
    max_hops = st.sidebar.slider("Traversal Depth", min_value=1, max_value=3, value=base_settings.max_hops)
    max_evidence = st.sidebar.slider("Evidence Budget", min_value=3, max_value=12, value=base_settings.max_evidence)

    return AppSettings(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        ollama_host=ollama_host,
        extraction_model=extraction_model,
        answer_model=answer_model,
        max_hops=max_hops,
        max_evidence=max_evidence,
        chunk_size=base_settings.chunk_size,
        chunk_overlap=base_settings.chunk_overlap,
    )


def initialize_session_state() -> None:
    if "documents" not in st.session_state:
        st.session_state.documents = []


def render_ingest_tab(settings: AppSettings) -> None:
    st.subheader("Document Ingestion")
    sample_names = ["Custom text"] + list(SAMPLE_DOCUMENTS.keys())

    with st.form("ingest_form"):
        selected_sample = st.selectbox("Seed document", sample_names)
        default_text = SAMPLE_DOCUMENTS.get(selected_sample, "") if selected_sample != "Custom text" else ""
        document_name = st.text_input(
            "Document name",
            value=selected_sample if selected_sample != "Custom text" else "",
            placeholder="Quarterly operations memo",
        )
        document_text = st.text_area("Document body", value=default_text, height=260)
        submitted = st.form_submit_button("Build graph")

    if not submitted:
        return

    payload = DocumentInput(name=document_name.strip(), text=document_text.strip())
    if not payload.name or not payload.text:
        st.error("Document name and content are both required.")
        return

    with st.spinner("Extracting entities and relationships..."):
        store = Neo4jGateway(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        llm = OllamaGateway(settings.ollama_host)
        service = IngestionService(store, llm, settings)
        try:
            report = service.ingest_document(payload)
        finally:
            store.close()

    if payload.name not in st.session_state.documents:
        st.session_state.documents.append(payload.name)

    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Chunks", report.chunk_count)
    metric_two.metric("Entities", report.entity_count)
    metric_three.metric("Relationships", report.relationship_count)

    if report.warnings:
        for warning in report.warnings:
            st.warning(warning)
    else:
        st.success("Graph ingestion completed without warnings.")


def render_question_tab(settings: AppSettings) -> None:
    st.subheader("Question Answering")
    if st.session_state.documents:
        st.caption("Loaded documents: " + ", ".join(st.session_state.documents))
    else:
        st.caption("No documents have been ingested in this session yet.")

    with st.form("question_form"):
        query = st.text_input(
            "Question",
            value="Which teams own the graph pipeline and what dependencies do they have?",
        )
        submitted = st.form_submit_button("Generate answer")

    if not submitted:
        return

    if not query.strip():
        st.error("A question is required.")
        return

    with st.spinner("Collecting graph evidence and drafting an answer..."):
        store = Neo4jGateway(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        llm = OllamaGateway(settings.ollama_host)
        service = QuestionAnsweringService(store, llm, settings)
        try:
            result = service.answer_question(query.strip())
        finally:
            store.close()

    st.markdown(result.answer)

    st.markdown("### Citations")
    if result.citations:
        for citation in result.citations:
            with st.expander("{0} · {1}".format(citation.ref_id, citation.source_document)):
                st.write("Entity: {0}".format(citation.entity_name))
                st.write("Path: {0}".format(" -> ".join(citation.reasoning_path)))
                st.write("Excerpt:")
                st.code(citation.source_excerpt)
    else:
        st.info("The model did not anchor the answer to any evidence references.")

    st.markdown("### Retrieval Trace")
    for entry in result.trace:
        st.write("- {0}".format(entry))


def render_operations_tab(settings: AppSettings) -> None:
    st.subheader("Repository Operations")

    stats_col, reset_col = st.columns(2)
    if stats_col.button("Refresh graph statistics"):
        store = Neo4jGateway(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        try:
            stats = store.graph_stats()
        finally:
            store.close()
        display_stats(stats.values())

    if reset_col.button("Clear graph"):
        store = Neo4jGateway(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        try:
            store.clear_graph()
        finally:
            store.close()
        st.session_state.documents = []
        st.success("Graph state cleared.")


def display_stats(values: Iterable[int]) -> None:
    labels = ["Documents", "Chunks", "Entities", "Relationships"]
    columns = st.columns(len(labels))
    for column, label, value in zip(columns, labels, values):
        column.metric(label, value)


if __name__ == "__main__":
    main()
