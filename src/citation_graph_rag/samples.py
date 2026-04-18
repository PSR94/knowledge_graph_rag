SAMPLE_DOCUMENTS = {
    "Platform Readout": """
    Meridian Data Platform maintains an internal retrieval stack for engineering knowledge. The Graph Services team owns
    the entity pipeline and publishes a normalized graph into Neo4j every night. Search Infrastructure depends on that
    graph to enrich keyword lookups with dependency and ownership data. The Applied AI group maintains the answer
    synthesis service and consumes graph evidence plus chunk-level excerpts from document storage. Incidents involving
    stale lineage data are routed back to Graph Services because that team owns extraction quality and schema changes.
    """.strip(),
    "Operations Brief": """
    The reliability review for Q2 identified two bottlenecks in the platform. First, ingestion jobs were delayed because
    the scheduler shared workers with analytics backfills. Second, the answer synthesis service was operating without a
    hard evidence budget, which led to bloated prompts and inconsistent citations. The proposed remediation assigns a
    dedicated worker pool to ingestion and adds an evidence cap enforced by the question-answering pipeline. Program
    Management tracks the rollout, while Search Infrastructure validates retrieval latency after each release.
    """.strip(),
}
