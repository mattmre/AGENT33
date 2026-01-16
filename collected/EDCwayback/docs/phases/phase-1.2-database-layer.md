# Phase 1.2: Database Layer Foundation

## Metadata
| Field | Value |
|-------|-------|
| **Phase ID** | 1.2 |
| **Category** | Core Infrastructure & Architecture |
| **Priority** | Critical |
| **Dependencies** | Phase 1.1 (Configuration Management) |
| **Status** | NOT STARTED |
| **Estimated Features** | 12 |

---

## Objective

Establish persistent storage infrastructure using SQLAlchemy ORM with support for SQLite (development) and PostgreSQL (production), enabling job tracking, artifact management, and forensic audit logging.

---

## Prerequisites

Before starting this phase, ensure:
- [ ] Phase 1.1 Configuration Management is complete
- [ ] `src/config/schema.py` has DatabaseConfig section
- [ ] Dependencies installed: `sqlalchemy>=2.0`, `alembic>=1.13`

Add to `requirements.txt`:
```
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9
```

---

## Features

### Feature 1.2.1: Database Configuration Schema
**Target File**: `src/config/schema.py` (modify)
**Effort**: Small
**Agent Type**: Implementer

Add database configuration to the existing config schema.

**Implementation**:
```python
# Add to src/config/schema.py

class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    url: str = Field(
        default="sqlite:///edc.db",
        description="Database connection URL (SQLite or PostgreSQL)",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL statements to log",
    )
    pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Connection pool size (PostgreSQL only)",
    )
    pool_recycle: int = Field(
        default=3600,
        ge=300,
        description="Seconds before connection recycling",
    )
    create_tables: bool = Field(
        default=True,
        description="Auto-create tables on startup (dev only)",
    )


# Add to EDCConfig class:
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
```

**Acceptance Criteria**:
- [ ] DatabaseConfig model added to schema.py
- [ ] EDCConfig includes `database: DatabaseConfig` field
- [ ] Environment variable mapping works: `EDC_DATABASE__URL`
- [ ] Validation: pool_size >= 1, pool_recycle >= 300
- [ ] Unit tests added to test_config.py

**Output Files**:
- `src/config/schema.py` (modified)
- `tests/test_config.py` (add database config tests)

---

### Feature 1.2.2: SQLAlchemy Base and Mixins
**Target File**: `src/db/models/base.py`
**Effort**: Small
**Agent Type**: Implementer

Create SQLAlchemy declarative base with common mixins for timestamps and identifiers.

**Implementation**:
```python
# src/db/models/base.py
from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


class TimestampMixin:
    """Mixin adding created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class IdentifierMixin:
    """Mixin adding auto-increment ID and UUID."""

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    uuid: Mapped[str] = mapped_column(
        String(36),
        default=lambda: str(uuid4()),
        unique=True,
        nullable=False,
        index=True,
    )
```

**Acceptance Criteria**:
- [ ] DeclarativeBase created for model inheritance
- [ ] TimestampMixin auto-updates `updated_at` on changes
- [ ] IdentifierMixin generates UUID automatically
- [ ] Compatible with SQLite and PostgreSQL
- [ ] Type hints using `Mapped[]` (SQLAlchemy 2.0 style)

**Output Files**:
- `src/db/__init__.py`
- `src/db/models/__init__.py`
- `src/db/models/base.py`

---

### Feature 1.2.3: Database Engine Manager
**Target File**: `src/db/engine.py`
**Effort**: Medium
**Agent Type**: Implementer

Create database engine with connection pooling and session management.

**Implementation**:
```python
# src/db/engine.py
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.schema import EDCConfig


class DatabaseEngine:
    """Database engine manager with connection pooling."""

    def __init__(self, config: EDCConfig):
        self.config = config.database
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None

    @property
    def engine(self) -> Engine:
        """Lazy-initialize database engine."""
        if self._engine is None:
            connect_args = {}
            # SQLite-specific: enable foreign keys
            if self.config.url.startswith("sqlite"):
                connect_args["check_same_thread"] = False

            self._engine = create_engine(
                self.config.url,
                echo=self.config.echo,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
        return self._engine

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a session context with automatic commit/rollback."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """Create all tables (development use)."""
        from src.db.models.base import Base
        Base.metadata.create_all(bind=self.engine)

    def dispose(self) -> None:
        """Dispose of engine and connection pool."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
```

**Acceptance Criteria**:
- [ ] Lazy engine initialization
- [ ] Context manager for session handling
- [ ] Automatic commit on success, rollback on exception
- [ ] `create_tables()` for development setup
- [ ] `dispose()` for graceful shutdown
- [ ] Works with both SQLite and PostgreSQL URLs

**Output Files**:
- `src/db/engine.py`

---

### Feature 1.2.4: Job Model
**Target File**: `src/db/models/job.py`
**Effort**: Medium
**Agent Type**: Implementer

Define the Job model for tracking capture requests and results.

**Implementation**:
```python
# src/db/models/job.py
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Float, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, IdentifierMixin

if TYPE_CHECKING:
    from .artifact import Artifact
    from .audit import AuditLog


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base, TimestampMixin, IdentifierMixin):
    """Capture job record."""

    __tablename__ = "jobs"

    # Request fields (from CSV input)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    when: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), default="closest")
    mode: Mapped[str] = mapped_column(String(16), default="fetch")

    # Processing result
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING,
        index=True,
    )
    memento_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    variance_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    source: Mapped[str] = mapped_column(String(64), default="wayback")
    options: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="job",
    )

    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
        Index("ix_jobs_url_when", "url", "when"),
    )
```

**Acceptance Criteria**:
- [ ] All CSV input fields represented
- [ ] JobStatus enum with all states
- [ ] Composite indexes for common queries
- [ ] JSON field for extensible options
- [ ] Relationships to artifacts and audit_logs
- [ ] Type hints for all fields

**Output Files**:
- `src/db/models/job.py`

---

### Feature 1.2.5: Artifact Model
**Target File**: `src/db/models/artifact.py`
**Effort**: Medium
**Agent Type**: Implementer

Define the Artifact model for tracking generated files with forensic hashes.

**Implementation**:
```python
# src/db/models/artifact.py
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, ForeignKey, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, IdentifierMixin

if TYPE_CHECKING:
    from .job import Job


class ArtifactType(str, Enum):
    """Artifact file type."""
    HTML = "html"
    RAW = "raw"
    PDF = "pdf"
    PNG = "png"
    WARC = "warc"


class Artifact(Base, TimestampMixin, IdentifierMixin):
    """Generated artifact record with forensic hashes."""

    __tablename__ = "artifacts"

    # Foreign key to job
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Artifact identification
    artifact_type: Mapped[ArtifactType] = mapped_column(
        SQLEnum(ArtifactType),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Forensic hash values
    md5: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sha1: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Source tracking
    source: Mapped[str] = mapped_column(String(16), default="archived")
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationship
    job: Mapped["Job"] = relationship("Job", back_populates="artifacts")

    __table_args__ = (
        Index("ix_artifacts_job_type", "job_id", "artifact_type"),
    )
```

**Acceptance Criteria**:
- [ ] All artifact types as enum
- [ ] Hash fields for MD5, SHA1, SHA256
- [ ] Foreign key with cascade delete
- [ ] File size as BigInteger (large files)
- [ ] Relationship back to job

**Output Files**:
- `src/db/models/artifact.py`

---

### Feature 1.2.6: Audit Log Model
**Target File**: `src/db/models/audit.py`
**Effort**: Medium
**Agent Type**: Implementer

Define the AuditLog model for forensic audit trail with hash chain integrity.

**Implementation**:
```python
# src/db/models/audit.py
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, IdentifierMixin

if TYPE_CHECKING:
    from .job import Job


class AuditAction(str, Enum):
    """Audit event action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    VERIFY = "verify"
    ACCESS = "access"


class AuditLog(Base, TimestampMixin, IdentifierMixin):
    """Forensic audit log with hash chain for tamper detection."""

    __tablename__ = "audit_logs"

    # Optional foreign keys (some events are system-wide)
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Audit event details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True,
    )
    actor: Mapped[str] = mapped_column(String(256), default="system")
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Additional context
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Hash chain for tamper detection
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Relationship
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_action_created", "action", "created_at"),
        Index("ix_audit_actor_created", "actor", "created_at"),
    )
```

**Acceptance Criteria**:
- [ ] All audit action types as enum
- [ ] Hash chain fields (previous_hash, entry_hash)
- [ ] IP address and user agent for forensic context
- [ ] Nullable job_id for system events
- [ ] Indexes for common query patterns
- [ ] Append-only by design (no update methods)

**Output Files**:
- `src/db/models/audit.py`

---

### Feature 1.2.7: Alembic Migration Setup
**Target Directory**: `src/db/migrations/`
**Effort**: Medium
**Agent Type**: Implementer

Initialize Alembic for database migrations with config integration.

**Directory Structure**:
```
src/db/migrations/
├── alembic.ini
├── env.py
├── script.py.mako
└── versions/
    └── 001_initial_schema.py
```

**Implementation** (`env.py`):
```python
# src/db/migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from src.config.loader import load_config
from src.db.models.base import Base

# Load application config
config = context.config
app_config = load_config()

# Set database URL from config
config.set_main_option("sqlalchemy.url", app_config.database.url)

# Import all models to register them
from src.db.models import job, artifact, audit  # noqa

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Acceptance Criteria**:
- [ ] Alembic initialized with proper structure
- [ ] `env.py` loads database URL from EDCConfig
- [ ] Initial migration creates jobs, artifacts, audit_logs tables
- [ ] All indexes created in migration
- [ ] Migrations reversible (upgrade/downgrade)
- [ ] Works with SQLite and PostgreSQL

**Output Files**:
- `src/db/migrations/alembic.ini`
- `src/db/migrations/env.py`
- `src/db/migrations/script.py.mako`
- `src/db/migrations/versions/001_initial_schema.py`

---

### Feature 1.2.8: Job Repository
**Target File**: `src/db/repositories/job.py`
**Effort**: Medium
**Agent Type**: Implementer

Implement repository pattern for Job CRUD operations.

**Implementation**:
```python
# src/db/repositories/job.py
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from src.db.models.job import Job, JobStatus


class JobRepository:
    """Repository for Job CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        url: str,
        when: str,
        direction: str = "closest",
        mode: str = "fetch",
        **kwargs,
    ) -> Job:
        """Create a new job record."""
        job = Job(
            uuid=str(uuid4()),
            url=url,
            when=when,
            direction=direction,
            mode=mode,
            status=JobStatus.PENDING,
            **kwargs,
        )
        self.session.add(job)
        self.session.flush()  # Get ID without committing
        return job

    def get_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by internal ID."""
        return self.session.get(Job, job_id)

    def get_by_uuid(self, uuid: str) -> Optional[Job]:
        """Get job by public UUID."""
        stmt = select(Job).where(Job.uuid == uuid)
        return self.session.scalar(stmt)

    def list_by_status(
        self,
        status: JobStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        """List jobs by status with pagination."""
        stmt = (
            select(Job)
            .where(Job.status == status)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def update_status(
        self,
        job: Job,
        status: JobStatus,
        memento_url: Optional[str] = None,
        variance_days: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> Job:
        """Update job status and result fields."""
        job.status = status
        if memento_url is not None:
            job.memento_url = memento_url
        if variance_days is not None:
            job.variance_days = variance_days
        if error_message is not None:
            job.error_message = error_message
        self.session.flush()
        return job

    def count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        stmt = select(Job).where(Job.status == status)
        return len(list(self.session.scalars(stmt)))
```

**Acceptance Criteria**:
- [ ] Create job with UUID generation
- [ ] Get by ID and UUID
- [ ] List with status filter and pagination
- [ ] Update status with optional result fields
- [ ] Count by status for metrics
- [ ] No commit in repository (caller manages transaction)

**Output Files**:
- `src/db/repositories/__init__.py`
- `src/db/repositories/job.py`

---

### Feature 1.2.9: Artifact Repository
**Target File**: `src/db/repositories/artifact.py`
**Effort**: Medium
**Agent Type**: Implementer

Implement repository pattern for Artifact CRUD operations.

**Implementation**:
```python
# src/db/repositories/artifact.py
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models.artifact import Artifact, ArtifactType


class ArtifactRepository:
    """Repository for Artifact CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        job_id: int,
        artifact_type: ArtifactType,
        file_path: str,
        file_size: Optional[int] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
        sha256: Optional[str] = None,
        **kwargs,
    ) -> Artifact:
        """Create a new artifact record."""
        artifact = Artifact(
            uuid=str(uuid4()),
            job_id=job_id,
            artifact_type=artifact_type,
            file_path=file_path,
            file_size=file_size,
            md5=md5,
            sha1=sha1,
            sha256=sha256,
            **kwargs,
        )
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def get_by_job(
        self,
        job_id: int,
        artifact_type: Optional[ArtifactType] = None,
    ) -> List[Artifact]:
        """Get all artifacts for a job, optionally filtered by type."""
        stmt = select(Artifact).where(Artifact.job_id == job_id)
        if artifact_type:
            stmt = stmt.where(Artifact.artifact_type == artifact_type)
        return list(self.session.scalars(stmt))

    def verify_hash(self, artifact_id: int, sha256: str) -> bool:
        """Verify artifact hash matches stored value."""
        artifact = self.session.get(Artifact, artifact_id)
        if artifact is None:
            return False
        return artifact.sha256 == sha256

    def create_bulk(self, artifacts: List[dict]) -> List[Artifact]:
        """Bulk create artifacts."""
        records = [
            Artifact(uuid=str(uuid4()), **data)
            for data in artifacts
        ]
        self.session.add_all(records)
        self.session.flush()
        return records
```

**Acceptance Criteria**:
- [ ] Create single artifact with hashes
- [ ] Get artifacts by job with type filter
- [ ] Hash verification method
- [ ] Bulk create for efficiency
- [ ] Foreign key integrity maintained

**Output Files**:
- `src/db/repositories/artifact.py`

---

### Feature 1.2.10: CLI Database Commands
**Target File**: `src/cli.py` (modify)
**Effort**: Medium
**Agent Type**: Implementer

Add database management subcommands to CLI.

**Target Commands**:
```bash
edc db init        # Create tables (development)
edc db upgrade     # Run Alembic migrations
edc db downgrade   # Rollback last migration
edc db status      # Show migration status
edc db seed        # Seed with sample data
```

**Implementation**:
```python
# Add to src/cli.py

def cmd_db_init(args: argparse.Namespace) -> int:
    """Initialize database tables."""
    config = _get_config(args)
    from src.db.engine import DatabaseEngine
    engine = DatabaseEngine(config)
    engine.create_tables()
    print(f"Database initialized: {config.database.url}")
    return 0

def cmd_db_upgrade(args: argparse.Namespace) -> int:
    """Run database migrations."""
    from alembic import command
    from alembic.config import Config
    alembic_cfg = Config("src/db/migrations/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete")
    return 0

# ... similar for downgrade, status, seed
```

**Acceptance Criteria**:
- [ ] `edc db` subcommand group added
- [ ] `init` creates tables without Alembic
- [ ] `upgrade/downgrade` wrap Alembic commands
- [ ] `status` shows current migration revision
- [ ] `seed` creates sample jobs/artifacts for dev
- [ ] All commands respect `--config` flag

**Output Files**:
- `src/cli.py` (modified)

---

### Feature 1.2.11: Unit Tests
**Target Files**: `tests/test_db_models.py`, `tests/test_repositories.py`
**Effort**: Medium
**Agent Type**: Tester

Comprehensive tests using in-memory SQLite.

**Test Cases**:
```python
# tests/test_db_models.py

class TestJobModel:
    def test_create_job(self, db_session):
        """Test job creation with defaults."""

    def test_job_status_transition(self, db_session):
        """Test status enum values."""

    def test_job_artifact_relationship(self, db_session):
        """Test cascade delete to artifacts."""


class TestArtifactModel:
    def test_create_artifact_with_hashes(self, db_session):
        """Test artifact with all hash fields."""

    def test_artifact_type_enum(self, db_session):
        """Test artifact type validation."""


class TestAuditLogModel:
    def test_hash_chain_integrity(self, db_session):
        """Test that entry_hash is set."""


# tests/test_repositories.py

class TestJobRepository:
    def test_create_and_get(self, db_session):
        """Test CRUD operations."""

    def test_list_by_status_pagination(self, db_session):
        """Test pagination."""

    def test_update_status(self, db_session):
        """Test status update with result fields."""
```

**Acceptance Criteria**:
- [ ] All models tested for creation
- [ ] Repository CRUD operations tested
- [ ] Relationship cascades tested
- [ ] Use in-memory SQLite for speed
- [ ] Pytest fixtures for session management
- [ ] >90% code coverage for db module

**Output Files**:
- `tests/test_db_models.py`
- `tests/test_repositories.py`
- `tests/conftest.py` (add db fixtures)

---

### Feature 1.2.12: Documentation
**Target File**: `docs/database.md`
**Effort**: Small
**Agent Type**: Documentation

Create comprehensive database documentation.

**Sections**:
```markdown
# Database Layer

## Overview
- SQLAlchemy ORM with SQLite/PostgreSQL support

## Configuration
- Database URL formats
- Connection pooling options
- Environment variables

## Schema
- ERD diagram
- Table descriptions
- Index explanations

## Migrations
- Running migrations
- Creating new migrations
- Rollback procedures

## Repository Pattern
- Usage examples
- Transaction management

## Forensic Integrity
- Hash storage
- Audit log chain

## Backup & Restore
- SQLite backup
- PostgreSQL pg_dump
```

**Acceptance Criteria**:
- [ ] Configuration options documented
- [ ] ERD diagram (ASCII or Mermaid)
- [ ] Migration workflow documented
- [ ] Repository usage examples
- [ ] Backup procedures documented

**Output Files**:
- `docs/database.md`

---

## Verification Checklist

Before marking this phase complete:

- [ ] All 12 features implemented
- [ ] Models have proper indexes
- [ ] Migrations run on SQLite and PostgreSQL
- [ ] Repository tests pass with >90% coverage
- [ ] CLI `edc db` commands functional
- [ ] Documentation complete

---

## Dependencies for Next Phase

Phase 1.3 (Dependency Injection) will require:
- `DatabaseEngine` class for injection
- Repository classes for service layer
- Session context manager pattern
