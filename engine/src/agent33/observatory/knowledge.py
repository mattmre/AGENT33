"""Knowledge service for managing facts, sources, and knowledge graph generation.

This service handles:
- Storing ingested content
- Extracting facts using LLM
- Semantic search using pgvector
- Generating D3.js-compatible knowledge graphs
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent33.db.models import ActivityLog, ActivityType, Fact, Source, SourceType

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Protocols for dependency injection
# ---------------------------------------------------------------------------


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers used in fact extraction."""

    async def complete(
        self,
        messages: list[Any],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Any:
        """Generate a completion from the given messages."""
        ...


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------


@dataclass
class IngestedContentCreate:
    """Data for creating ingested content."""

    tenant_id: str
    source_id: str | None
    title: str
    content: str
    source_url: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactResponse:
    """Response model for a fact."""

    id: str
    content: str
    confidence: float
    source_url: str | None
    source_id: str | None
    is_verified: bool
    created_at: datetime
    metadata: dict[str, Any]
    score: float | None = None  # Similarity score for search results

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "confidence": self.confidence,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "score": self.score,
        }


@dataclass
class FactRelation:
    """A relationship between two facts."""

    source_fact_id: str
    target_fact_id: str
    relation_type: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactWithRelations:
    """A fact with its related facts."""

    fact: FactResponse
    related_facts: list[FactResponse]
    relations: list[FactRelation]


@dataclass
class SourceCreate:
    """Data for creating a source."""

    name: str
    source_type: SourceType
    url: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class SourceResponse:
    """Response model for a source."""

    id: str
    name: str
    source_type: str
    url: str | None
    config: dict[str, Any]
    is_active: bool
    last_fetched_at: datetime | None
    last_error: str | None
    items_fetched: int
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "url": self.url,
            "config": self.config,
            "is_active": self.is_active,
            "last_fetched_at": self.last_fetched_at.isoformat() if self.last_fetched_at else None,
            "last_error": self.last_error,
            "items_fetched": self.items_fetched,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    id: str
    label: str
    type: str  # fact_type from metadata or 'fact'
    size: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    source: str
    target: str
    type: str = "related"
    weight: float = 1.0


@dataclass
class KnowledgeGraph:
    """D3.js-compatible knowledge graph data structure."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to D3.js-compatible dictionary format."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type,
                    "size": n.size,
                    **n.metadata,
                }
                for n in self.nodes
            ],
            "links": [  # D3.js uses 'links' instead of 'edges'
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.type,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Fact extraction prompt
# ---------------------------------------------------------------------------

FACT_EXTRACTION_PROMPT = """You are a fact extraction system. Extract discrete, verifiable facts from the given content.

Rules:
1. Each fact should be a single, atomic statement
2. Facts should be self-contained and understandable without context
3. Include entity names, dates, numbers when present
4. Classify each fact with a type: entity, event, relationship, statistic, claim
5. Assign a confidence score (0.0 to 1.0) based on how clearly stated the fact is

Return facts as a JSON array with this structure:
[
  {
    "content": "The statement of the fact",
    "fact_type": "entity|event|relationship|statistic|claim",
    "confidence": 0.95,
    "entities": ["Entity1", "Entity2"],
    "subject": "Main subject of the fact"
  }
]

Content to extract facts from:
{content}

Return ONLY the JSON array, no other text."""


# ---------------------------------------------------------------------------
# Knowledge Service
# ---------------------------------------------------------------------------


class KnowledgeService:
    """Service for managing facts, sources, and knowledge graph generation.

    This service provides:
    - Content storage and fact extraction
    - Semantic search over facts using pgvector
    - Knowledge graph generation for visualization
    - Source management (CRUD operations)
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider | None = None,
        llm_model: str = "llama3.2",
    ) -> None:
        """Initialize the knowledge service.

        Args:
            session_factory: SQLAlchemy async session factory
            embedding_provider: Provider for generating embeddings
            llm_provider: Optional LLM provider for fact extraction
            llm_model: Model name to use for fact extraction
        """
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider
        self._llm_provider = llm_provider
        self._llm_model = llm_model
        self._log = logger.bind(service="knowledge")

    # -----------------------------------------------------------------------
    # Content Storage
    # -----------------------------------------------------------------------

    async def store_content(self, content: IngestedContentCreate) -> UUID:
        """Store ingested content as a fact with embedding.

        Args:
            content: The content to store

        Returns:
            UUID of the created fact
        """
        self._log.info(
            "storing_content",
            tenant_id=content.tenant_id,
            title=content.title[:50] if content.title else None,
        )

        # Generate content hash for deduplication
        content_hash = hashlib.sha256(content.content.encode()).hexdigest()

        async with self._session_factory() as session:
            # Check for duplicate
            stmt = select(Fact).where(
                Fact.tenant_id == content.tenant_id,
                Fact.content_hash == content_hash,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._log.debug("content_already_exists", fact_id=existing.id)
                return UUID(existing.id)

            # Generate embedding
            try:
                embedding = await self._embedding_provider.embed(content.content)
            except Exception as e:
                self._log.error("embedding_generation_failed", error=str(e))
                embedding = None

            # Create fact
            fact_id = str(uuid4())
            metadata = content.metadata.copy()
            metadata["title"] = content.title
            if content.published_at:
                metadata["published_at"] = content.published_at.isoformat()

            fact = Fact(
                id=fact_id,
                tenant_id=content.tenant_id,
                source_id=content.source_id,
                content=content.content,
                content_hash=content_hash,
                embedding=embedding,
                confidence=1.0,
                metadata_=metadata,
                source_url=content.source_url,
                is_verified=False,
            )

            session.add(fact)

            # Log activity
            activity = ActivityLog(
                id=str(uuid4()),
                tenant_id=content.tenant_id,
                activity_type=ActivityType.INGESTED,
                title=f"Ingested: {content.title[:100]}" if content.title else "Content ingested",
                description=content.content[:500] if content.content else None,
                metadata_={"source_id": content.source_id, "source_url": content.source_url},
                source_id=content.source_id,
                is_public=True,
            )
            session.add(activity)

            await session.commit()

            self._log.info("content_stored", fact_id=fact_id)
            return UUID(fact_id)

    # -----------------------------------------------------------------------
    # Fact Extraction
    # -----------------------------------------------------------------------

    async def extract_facts(self, content_id: UUID) -> list[UUID]:
        """Extract atomic facts from stored content using LLM.

        Args:
            content_id: UUID of the content to extract facts from

        Returns:
            List of UUIDs for newly created facts
        """
        if self._llm_provider is None:
            self._log.warning("no_llm_provider", content_id=str(content_id))
            return []

        async with self._session_factory() as session:
            # Get the source content
            source_fact = await session.get(Fact, str(content_id))
            if not source_fact:
                self._log.error("content_not_found", content_id=str(content_id))
                return []

            self._log.info("extracting_facts", content_id=str(content_id))

            # Call LLM for fact extraction
            try:
                from agent33.llm.base import ChatMessage

                prompt = FACT_EXTRACTION_PROMPT.format(content=source_fact.content[:4000])
                messages = [ChatMessage(role="user", content=prompt)]

                response = await self._llm_provider.complete(
                    messages,
                    model=self._llm_model,
                    temperature=0.1,
                    max_tokens=2000,
                )

                # Parse extracted facts
                facts_data = json.loads(response.content)
            except json.JSONDecodeError as e:
                self._log.error("fact_extraction_parse_error", error=str(e))
                return []
            except Exception as e:
                self._log.error("fact_extraction_failed", error=str(e))
                return []

            # Store extracted facts
            created_ids: list[UUID] = []

            for fact_data in facts_data:
                fact_content = fact_data.get("content", "")
                if not fact_content:
                    continue

                content_hash = hashlib.sha256(fact_content.encode()).hexdigest()

                # Check for duplicate
                stmt = select(Fact).where(
                    Fact.tenant_id == source_fact.tenant_id,
                    Fact.content_hash == content_hash,
                )
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    continue

                # Generate embedding
                try:
                    embedding = await self._embedding_provider.embed(fact_content)
                except Exception as e:
                    self._log.warning("embedding_failed_for_fact", error=str(e))
                    embedding = None

                # Create fact record
                fact_id = str(uuid4())
                fact = Fact(
                    id=fact_id,
                    tenant_id=source_fact.tenant_id,
                    source_id=source_fact.source_id,
                    content=fact_content,
                    content_hash=content_hash,
                    embedding=embedding,
                    confidence=fact_data.get("confidence", 0.8),
                    metadata_={
                        "fact_type": fact_data.get("fact_type", "claim"),
                        "entities": fact_data.get("entities", []),
                        "subject": fact_data.get("subject"),
                        "extracted_from": str(content_id),
                    },
                    source_url=source_fact.source_url,
                    is_verified=False,
                )
                session.add(fact)
                created_ids.append(UUID(fact_id))

            # Log extraction activity
            if created_ids:
                activity = ActivityLog(
                    id=str(uuid4()),
                    tenant_id=source_fact.tenant_id,
                    activity_type=ActivityType.LEARNED,
                    title=f"Extracted {len(created_ids)} facts",
                    description=f"Extracted from content {content_id}",
                    metadata_={
                        "source_content_id": str(content_id),
                        "fact_ids": [str(fid) for fid in created_ids],
                    },
                    source_id=source_fact.source_id,
                    is_public=True,
                )
                session.add(activity)

            await session.commit()

            self._log.info(
                "facts_extracted",
                content_id=str(content_id),
                count=len(created_ids),
            )
            return created_ids

    # -----------------------------------------------------------------------
    # Semantic Search
    # -----------------------------------------------------------------------

    async def search_facts(
        self,
        query: str,
        tenant_id: UUID | None = None,
        limit: int = 10,
    ) -> list[FactResponse]:
        """Search facts using semantic similarity with pgvector.

        Args:
            query: Search query text
            tenant_id: Optional tenant filter
            limit: Maximum number of results

        Returns:
            List of matching facts with similarity scores
        """
        self._log.info("searching_facts", query=query[:50], tenant_id=str(tenant_id) if tenant_id else None)

        # Generate query embedding
        try:
            query_embedding = await self._embedding_provider.embed(query)
        except Exception as e:
            self._log.error("query_embedding_failed", error=str(e))
            return []

        embedding_literal = f"[{','.join(str(v) for v in query_embedding)}]"

        async with self._session_factory() as session:
            # Build query with cosine similarity
            # Using 1 - cosine_distance for similarity score
            if tenant_id:
                sql = text("""
                    SELECT id, content, confidence, source_url, source_id, is_verified,
                           created_at, metadata,
                           1 - (embedding <=> :emb::vector) AS score
                    FROM facts
                    WHERE tenant_id = :tenant_id
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :emb::vector
                    LIMIT :limit
                """)
                params = {"emb": embedding_literal, "tenant_id": str(tenant_id), "limit": limit}
            else:
                sql = text("""
                    SELECT id, content, confidence, source_url, source_id, is_verified,
                           created_at, metadata,
                           1 - (embedding <=> :emb::vector) AS score
                    FROM facts
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> :emb::vector
                    LIMIT :limit
                """)
                params = {"emb": embedding_literal, "limit": limit}

            result = await session.execute(sql, params)
            rows = result.fetchall()

            facts = [
                FactResponse(
                    id=row[0],
                    content=row[1],
                    confidence=float(row[2]),
                    source_url=row[3],
                    source_id=row[4],
                    is_verified=row[5],
                    created_at=row[6],
                    metadata=row[7] or {},
                    score=float(row[8]) if row[8] is not None else None,
                )
                for row in rows
            ]

            self._log.info("search_complete", results=len(facts))
            return facts

    # -----------------------------------------------------------------------
    # Fact Retrieval
    # -----------------------------------------------------------------------

    async def get_fact(
        self,
        fact_id: UUID,
        tenant_id: UUID | None = None,
    ) -> FactWithRelations | None:
        """Get a fact with its related facts.

        Args:
            fact_id: UUID of the fact to retrieve
            tenant_id: Optional tenant filter for security

        Returns:
            Fact with relations, or None if not found
        """
        async with self._session_factory() as session:
            # Get the fact
            stmt = select(Fact).where(Fact.id == str(fact_id))
            if tenant_id:
                stmt = stmt.where(Fact.tenant_id == str(tenant_id))

            result = await session.execute(stmt)
            fact = result.scalar_one_or_none()

            if not fact:
                return None

            fact_response = FactResponse(
                id=fact.id,
                content=fact.content,
                confidence=float(fact.confidence),
                source_url=fact.source_url,
                source_id=fact.source_id,
                is_verified=fact.is_verified,
                created_at=fact.created_at,
                metadata=fact.metadata_ or {},
            )

            # Find related facts using embedding similarity
            related_facts: list[FactResponse] = []
            relations: list[FactRelation] = []

            if fact.embedding is not None:
                embedding_literal = f"[{','.join(str(v) for v in fact.embedding)}]"
                sql = text("""
                    SELECT id, content, confidence, source_url, source_id, is_verified,
                           created_at, metadata,
                           1 - (embedding <=> :emb::vector) AS score
                    FROM facts
                    WHERE id != :fact_id
                      AND tenant_id = :tenant_id
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :emb::vector
                    LIMIT 5
                """)

                result = await session.execute(
                    sql,
                    {
                        "emb": embedding_literal,
                        "fact_id": str(fact_id),
                        "tenant_id": fact.tenant_id,
                    },
                )
                rows = result.fetchall()

                for row in rows:
                    score = float(row[8]) if row[8] is not None else 0.0
                    # Only include if similarity is above threshold
                    if score > 0.5:
                        related_facts.append(
                            FactResponse(
                                id=row[0],
                                content=row[1],
                                confidence=float(row[2]),
                                source_url=row[3],
                                source_id=row[4],
                                is_verified=row[5],
                                created_at=row[6],
                                metadata=row[7] or {},
                                score=score,
                            )
                        )
                        relations.append(
                            FactRelation(
                                source_fact_id=str(fact_id),
                                target_fact_id=row[0],
                                relation_type="similar",
                                confidence=score,
                            )
                        )

            return FactWithRelations(
                fact=fact_response,
                related_facts=related_facts,
                relations=relations,
            )

    # -----------------------------------------------------------------------
    # Knowledge Graph
    # -----------------------------------------------------------------------

    async def get_graph(
        self,
        tenant_id: UUID | None = None,
        limit: int = 100,
        fact_types: list[str] | None = None,
        subject_filter: str | None = None,
    ) -> KnowledgeGraph:
        """Generate a D3.js-compatible knowledge graph.

        Args:
            tenant_id: Optional tenant filter
            limit: Maximum number of nodes
            fact_types: Optional filter by fact type (entity, event, etc.)
            subject_filter: Optional filter by subject

        Returns:
            KnowledgeGraph with nodes and edges
        """
        self._log.info(
            "generating_graph",
            tenant_id=str(tenant_id) if tenant_id else None,
            limit=limit,
        )

        async with self._session_factory() as session:
            # Build query for facts
            stmt = select(Fact).where(Fact.embedding.isnot(None))

            if tenant_id:
                stmt = stmt.where(Fact.tenant_id == str(tenant_id))

            stmt = stmt.order_by(Fact.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            facts = result.scalars().all()

            # Filter by fact_types if specified
            if fact_types:
                facts = [
                    f for f in facts
                    if f.metadata_ and f.metadata_.get("fact_type") in fact_types
                ]

            # Filter by subject if specified
            if subject_filter:
                subject_lower = subject_filter.lower()
                facts = [
                    f for f in facts
                    if f.metadata_
                    and f.metadata_.get("subject", "").lower().find(subject_lower) >= 0
                ]

            # Build nodes from facts
            nodes: list[GraphNode] = []
            node_ids: set[str] = set()

            for fact in facts:
                metadata = fact.metadata_ or {}
                fact_type = metadata.get("fact_type", "fact")

                # Truncate content for label
                label = fact.content[:80] + "..." if len(fact.content) > 80 else fact.content

                nodes.append(
                    GraphNode(
                        id=fact.id,
                        label=label,
                        type=fact_type,
                        size=float(fact.confidence) if fact.confidence else 1.0,
                        metadata={
                            "confidence": fact.confidence,
                            "source_url": fact.source_url,
                            "entities": metadata.get("entities", []),
                            "subject": metadata.get("subject"),
                        },
                    )
                )
                node_ids.add(fact.id)

            # Generate edges based on embedding similarity
            edges: list[GraphEdge] = []
            processed_pairs: set[tuple[str, str]] = set()

            for i, fact in enumerate(facts):
                if fact.embedding is None:
                    continue

                embedding_literal = f"[{','.join(str(v) for v in fact.embedding)}]"

                # Find similar facts
                sql = text("""
                    SELECT id, 1 - (embedding <=> :emb::vector) AS score
                    FROM facts
                    WHERE id != :fact_id
                      AND tenant_id = :tenant_id
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :emb::vector
                    LIMIT 3
                """)

                result = await session.execute(
                    sql,
                    {
                        "emb": embedding_literal,
                        "fact_id": fact.id,
                        "tenant_id": fact.tenant_id,
                    },
                )
                similar_rows = result.fetchall()

                for row in similar_rows:
                    target_id = row[0]
                    score = float(row[1]) if row[1] is not None else 0.0

                    # Only create edge if:
                    # 1. Target is in our node set
                    # 2. Similarity is above threshold
                    # 3. We haven't processed this pair
                    if (
                        target_id in node_ids
                        and score > 0.6
                        and (fact.id, target_id) not in processed_pairs
                        and (target_id, fact.id) not in processed_pairs
                    ):
                        edges.append(
                            GraphEdge(
                                source=fact.id,
                                target=target_id,
                                type="similar",
                                weight=score,
                            )
                        )
                        processed_pairs.add((fact.id, target_id))

            # Also create edges based on shared entities
            entity_to_facts: dict[str, list[str]] = {}
            for fact in facts:
                metadata = fact.metadata_ or {}
                for entity in metadata.get("entities", []):
                    entity_lower = entity.lower()
                    if entity_lower not in entity_to_facts:
                        entity_to_facts[entity_lower] = []
                    entity_to_facts[entity_lower].append(fact.id)

            for entity, fact_ids in entity_to_facts.items():
                if len(fact_ids) > 1:
                    # Create edges between facts sharing this entity
                    for i in range(len(fact_ids)):
                        for j in range(i + 1, len(fact_ids)):
                            pair = (fact_ids[i], fact_ids[j])
                            reverse_pair = (fact_ids[j], fact_ids[i])
                            if pair not in processed_pairs and reverse_pair not in processed_pairs:
                                edges.append(
                                    GraphEdge(
                                        source=fact_ids[i],
                                        target=fact_ids[j],
                                        type="shared_entity",
                                        weight=0.8,
                                    )
                                )
                                processed_pairs.add(pair)

            graph = KnowledgeGraph(
                nodes=nodes,
                edges=edges,
                metadata={
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            )

            self._log.info(
                "graph_generated",
                nodes=len(nodes),
                edges=len(edges),
            )
            return graph

    # -----------------------------------------------------------------------
    # Source Management
    # -----------------------------------------------------------------------

    async def list_sources(self, tenant_id: UUID | None = None) -> list[SourceResponse]:
        """List all sources for a tenant.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            List of sources
        """
        async with self._session_factory() as session:
            stmt = select(Source)
            if tenant_id:
                stmt = stmt.where(Source.tenant_id == str(tenant_id))
            stmt = stmt.order_by(Source.created_at.desc())

            result = await session.execute(stmt)
            sources = result.scalars().all()

            return [
                SourceResponse(
                    id=s.id,
                    name=s.name,
                    source_type=s.source_type.value,
                    url=s.url,
                    config=s.config or {},
                    is_active=s.is_active,
                    last_fetched_at=s.last_fetched_at,
                    last_error=s.last_error,
                    items_fetched=s.items_fetched,
                    created_at=s.created_at,
                )
                for s in sources
            ]

    async def create_source(
        self,
        source: SourceCreate,
        tenant_id: UUID,
    ) -> SourceResponse:
        """Create a new source.

        Args:
            source: Source data to create
            tenant_id: Tenant that owns this source

        Returns:
            Created source
        """
        self._log.info(
            "creating_source",
            name=source.name,
            source_type=source.source_type.value,
            tenant_id=str(tenant_id),
        )

        async with self._session_factory() as session:
            source_record = Source(
                id=str(uuid4()),
                tenant_id=str(tenant_id),
                source_type=source.source_type,
                name=source.name,
                url=source.url,
                config=source.config,
                is_active=source.is_active,
            )
            session.add(source_record)
            await session.commit()
            await session.refresh(source_record)

            self._log.info("source_created", source_id=source_record.id)

            return SourceResponse(
                id=source_record.id,
                name=source_record.name,
                source_type=source_record.source_type.value,
                url=source_record.url,
                config=source_record.config or {},
                is_active=source_record.is_active,
                last_fetched_at=source_record.last_fetched_at,
                last_error=source_record.last_error,
                items_fetched=source_record.items_fetched,
                created_at=source_record.created_at,
            )

    async def delete_source(self, source_id: UUID, tenant_id: UUID) -> bool:
        """Delete a source.

        Args:
            source_id: UUID of the source to delete
            tenant_id: Tenant for security check

        Returns:
            True if deleted, False if not found
        """
        self._log.info(
            "deleting_source",
            source_id=str(source_id),
            tenant_id=str(tenant_id),
        )

        async with self._session_factory() as session:
            # Verify ownership
            stmt = select(Source).where(
                Source.id == str(source_id),
                Source.tenant_id == str(tenant_id),
            )
            result = await session.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                self._log.warning("source_not_found_for_delete", source_id=str(source_id))
                return False

            await session.delete(source)
            await session.commit()

            self._log.info("source_deleted", source_id=str(source_id))
            return True

    async def update_source_cursor(self, source_id: UUID, cursor: str) -> None:
        """Update the cursor/checkpoint for a source.

        This is used to track ingestion progress (e.g., last fetched item ID,
        page token, timestamp).

        Args:
            source_id: UUID of the source
            cursor: New cursor value to store
        """
        self._log.debug(
            "updating_source_cursor",
            source_id=str(source_id),
            cursor=cursor[:50] if len(cursor) > 50 else cursor,
        )

        async with self._session_factory() as session:
            source = await session.get(Source, str(source_id))
            if source:
                # Store cursor in the config JSONB field
                config = source.config or {}
                config["cursor"] = cursor
                config["cursor_updated_at"] = datetime.now(UTC).isoformat()
                source.config = config
                source.last_fetched_at = datetime.now(UTC)
                await session.commit()
                self._log.debug("source_cursor_updated", source_id=str(source_id))
            else:
                self._log.warning("source_not_found_for_cursor_update", source_id=str(source_id))
