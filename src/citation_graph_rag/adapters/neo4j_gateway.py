from typing import Dict
from typing import List

from neo4j import GraphDatabase

from citation_graph_rag.domain import DocumentChunk
from citation_graph_rag.domain import EntityMention
from citation_graph_rag.domain import ExtractionPayload
from citation_graph_rag.domain import RelationshipMention
from citation_graph_rag.text import normalize_identifier


class Neo4jGateway:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self.ensure_schema()

    def close(self) -> None:
        self._driver.close()

    def ensure_schema(self) -> None:
        statements = [
            "CREATE CONSTRAINT entity_name_key IF NOT EXISTS FOR (e:Entity) REQUIRE e.name_key IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT document_name IF NOT EXISTS FOR (d:Document) REQUIRE d.name IS UNIQUE",
        ]
        with self._driver.session() as session:
            for statement in statements:
                session.run(statement)

    def clear_graph(self) -> None:
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def store_chunk(self, chunk: DocumentChunk, payload: ExtractionPayload) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (document:Document {name: $document_name})
                MERGE (chunk:Chunk {id: $chunk_id})
                SET chunk.position = $position,
                    chunk.text = $text
                MERGE (document)-[:HAS_CHUNK]->(chunk)
                """,
                document_name=chunk.document_name,
                chunk_id=chunk.id,
                position=chunk.position,
                text=chunk.text,
            )
            for entity in payload.entities:
                self._upsert_entity(session, entity)
            for relationship in payload.relationships:
                self._upsert_relationship(session, relationship)

    def search_entities(self, term: str, limit: int) -> List[Dict[str, object]]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (entity:Entity)<-[:MENTIONS]-(chunk:Chunk)<-[:HAS_CHUNK]-(document:Document)
                WHERE toLower(entity.display_name) CONTAINS $term
                   OR toLower(coalesce(entity.summary, "")) CONTAINS $term
                RETURN entity.display_name AS entity_name,
                       entity.entity_type AS entity_type,
                       coalesce(entity.summary, "") AS summary,
                       document.name AS source_document,
                       chunk.text AS source_excerpt,
                       ["Direct match for: " + $term] AS reasoning_path
                LIMIT $limit
                """,
                term=term.lower(),
                limit=limit,
            )
            return [dict(record) for record in result]

    def expand_neighborhood(self, entity_name: str, hops: int, limit: int) -> List[Dict[str, object]]:
        query = """
            MATCH (seed:Entity {name_key: $name_key})-[rels:RELATES_TO*1..%d]-(related:Entity)
            WHERE related.name_key <> $name_key
            OPTIONAL MATCH (related)<-[:MENTIONS]-(chunk:Chunk)<-[:HAS_CHUNK]-(document:Document)
            RETURN related.display_name AS entity_name,
                   related.entity_type AS entity_type,
                   coalesce(related.summary, "") AS summary,
                   coalesce(document.name, "Unknown source") AS source_document,
                   coalesce(chunk.text, "") AS source_excerpt,
                   [rel IN rels | coalesce(rel.summary, rel.kind)] AS reasoning_path
            LIMIT $limit
        """ % hops
        with self._driver.session() as session:
            result = session.run(
                query,
                name_key=normalize_identifier(entity_name),
                limit=limit,
            )
            return [dict(record) for record in result]

    def graph_stats(self) -> Dict[str, int]:
        with self._driver.session() as session:
            return {
                "documents": session.run("MATCH (d:Document) RETURN count(d) AS count").single()["count"],
                "chunks": session.run("MATCH (c:Chunk) RETURN count(c) AS count").single()["count"],
                "entities": session.run("MATCH (e:Entity) RETURN count(e) AS count").single()["count"],
                "relationships": session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS count").single()["count"],
            }

    def _upsert_entity(self, session, entity: EntityMention) -> None:
        session.run(
            """
            MERGE (graph_entity:Entity {name_key: $name_key})
            SET graph_entity.display_name = $display_name,
                graph_entity.entity_type = $entity_type,
                graph_entity.summary = CASE
                    WHEN coalesce(graph_entity.summary, "") = "" THEN $summary
                    ELSE graph_entity.summary
                END
            WITH graph_entity
            MATCH (chunk:Chunk {id: $chunk_id})
            MERGE (chunk)-[:MENTIONS]->(graph_entity)
            """,
            name_key=normalize_identifier(entity.name),
            display_name=entity.name,
            entity_type=entity.kind,
            summary=entity.summary,
            chunk_id=entity.chunk_id,
        )

    def _upsert_relationship(self, session, relationship: RelationshipMention) -> None:
        session.run(
            """
            MERGE (source:Entity {name_key: $source_key})
            ON CREATE SET source.display_name = $source_name,
                          source.entity_type = "CONCEPT",
                          source.summary = ""
            MERGE (target:Entity {name_key: $target_key})
            ON CREATE SET target.display_name = $target_name,
                          target.entity_type = "CONCEPT",
                          target.summary = ""
            MERGE (source)-[rel:RELATES_TO {
                kind: $kind,
                chunk_id: $chunk_id,
                document_name: $document_name,
                target_key: $target_key
            }]->(target)
            SET rel.summary = $summary
            """,
            source_key=normalize_identifier(relationship.source_name),
            target_key=normalize_identifier(relationship.target_name),
            source_name=relationship.source_name,
            target_name=relationship.target_name,
            kind=relationship.kind,
            chunk_id=relationship.chunk_id,
            document_name=relationship.document_name,
            summary=relationship.summary,
        )
