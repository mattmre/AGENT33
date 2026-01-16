# Phase 2.1: Chain of Custody System

## Metadata
| Field | Value |
|-------|-------|
| **Phase ID** | 2.1 |
| **Category** | Forensic Integrity Features |
| **Priority** | Critical |
| **Dependencies** | Phase 1.2 (Database Layer) |
| **Status** | NOT STARTED |
| **Estimated Features** | 13 |

---

## Objective

Implement comprehensive chain of custody tracking for forensic defensibility, ensuring every artifact's lifecycle is documented, signed, and verifiable for court proceedings and e-discovery.

---

## Prerequisites

Before starting this phase, ensure:
- [ ] Phase 1.2 Database Layer is complete
- [ ] SQLAlchemy models for jobs/artifacts exist
- [ ] Repository pattern implemented

Add to `requirements.txt`:
```
cryptography>=41.0
reportlab>=4.0
jinja2>=3.0
```

---

## Features

### Feature 2.1.1: Custody Event Data Model
**Target File**: `src/db/models/custody.py`
**Effort**: Medium
**Agent Type**: Implementer

Define database model for custody events with hash chain integrity.

**Implementation**:
```python
# src/db/models/custody.py
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, IdentifierMixin

if TYPE_CHECKING:
    from .artifact import Artifact


class CustodyEventType(str, Enum):
    """Custody event types for chain of custody tracking."""
    CREATED = "created"
    ACCESSED = "accessed"
    TRANSFERRED = "transferred"
    MODIFIED = "modified"
    VERIFIED = "verified"
    EXPORTED = "exported"
    SEALED = "sealed"


class CustodyEvent(Base, TimestampMixin, IdentifierMixin):
    """Chain of custody event record."""

    __tablename__ = "custody_events"

    # Foreign key to artifact
    artifact_id: Mapped[int] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event identification
    event_type: Mapped[CustodyEventType] = mapped_column(
        SQLEnum(CustodyEventType),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(nullable=False)

    # Actor information
    actor_name: Mapped[str] = mapped_column(String(256), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_organization: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Location/context
    system_name: Mapped[str] = mapped_column(String(256), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    # Event details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    # Forensic integrity
    artifact_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Digital signature
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature_algorithm: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Relationship
    artifact: Mapped["Artifact"] = relationship("Artifact", backref="custody_events")

    __table_args__ = (
        Index("ix_custody_artifact_seq", "artifact_id", "sequence_number"),
    )
```

**Acceptance Criteria**:
- [ ] All custody event types as enum
- [ ] Actor information captured (name, role, org, email)
- [ ] Location context (system, IP, timezone)
- [ ] Hash chain fields (previous_event_hash, event_hash)
- [ ] Digital signature fields
- [ ] Composite index on artifact_id + sequence_number
- [ ] Alembic migration created

**Output Files**:
- `src/db/models/custody.py`
- `src/db/migrations/versions/002_custody_events.py`

---

### Feature 2.1.2: Actor Data Class
**Target File**: `src/forensic/actor.py`
**Effort**: Small
**Agent Type**: Implementer

Create actor identification for custody tracking.

**Implementation**:
```python
# src/forensic/actor.py
from dataclasses import dataclass, field
from typing import Optional
import socket
import os


@dataclass(frozen=True)
class Actor:
    """Represents an actor in chain of custody events."""

    name: str
    role: str
    organization: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    def system_actor(cls) -> "Actor":
        """Create actor for automated system operations."""
        return cls(
            name="EDCwayback System",
            role="automated",
            organization="System",
        )

    @classmethod
    def from_env(cls) -> "Actor":
        """Create actor from environment variables."""
        return cls(
            name=os.getenv("EDC_ACTOR_NAME", os.getlogin()),
            role=os.getenv("EDC_ACTOR_ROLE", "operator"),
            organization=os.getenv("EDC_ACTOR_ORG"),
            email=os.getenv("EDC_ACTOR_EMAIL"),
        )


@dataclass
class CustodyContext:
    """Context for custody event recording."""

    actor: Actor
    system_name: str = field(default_factory=socket.gethostname)
    ip_address: Optional[str] = None
    timezone: str = "UTC"
    reason: Optional[str] = None
    notes: Optional[str] = None
```

**Acceptance Criteria**:
- [ ] Immutable Actor dataclass
- [ ] Factory methods for system/env actors
- [ ] CustodyContext for event recording
- [ ] Default system name from hostname

**Output Files**:
- `src/forensic/__init__.py`
- `src/forensic/actor.py`

---

### Feature 2.1.3: Chain of Custody Core Module
**Target File**: `src/forensic/chain_of_custody.py`
**Effort**: Large
**Agent Type**: Implementer

Core chain of custody management with hash chain integrity.

**Implementation**:
```python
# src/forensic/chain_of_custody.py
import hashlib
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from src.db.models.custody import CustodyEvent, CustodyEventType
from src.db.models.artifact import Artifact
from .actor import Actor, CustodyContext


class ChainOfCustody:
    """Manages chain of custody for artifacts."""

    def __init__(self, session: Session, signing_key: Optional[bytes] = None):
        self.session = session
        self.signing_key = signing_key

    def record_event(
        self,
        artifact: Artifact,
        event_type: CustodyEventType,
        context: CustodyContext,
    ) -> CustodyEvent:
        """Record a custody event with hash chain integrity."""
        # Get previous event for this artifact
        previous = self._get_latest_event(artifact.id)

        # Calculate sequence number
        sequence = (previous.sequence_number + 1) if previous else 1

        # Calculate event hash
        event_hash = self._calculate_event_hash(
            artifact_id=artifact.id,
            event_type=event_type,
            sequence=sequence,
            timestamp=datetime.utcnow(),
            actor=context.actor,
            previous_hash=previous.event_hash if previous else None,
        )

        # Create event
        event = CustodyEvent(
            artifact_id=artifact.id,
            event_type=event_type,
            sequence_number=sequence,
            actor_name=context.actor.name,
            actor_role=context.actor.role,
            actor_organization=context.actor.organization,
            actor_email=context.actor.email,
            system_name=context.system_name,
            ip_address=context.ip_address,
            timezone=context.timezone,
            reason=context.reason,
            notes=context.notes,
            artifact_hash=artifact.sha256 or "",
            previous_event_hash=previous.event_hash if previous else None,
            event_hash=event_hash,
        )

        # Sign if key available
        if self.signing_key:
            event.signature = self._sign_event(event)
            event.signature_algorithm = "RSA-SHA256"

        self.session.add(event)
        self.session.flush()
        return event

    def record_creation(
        self,
        artifact: Artifact,
        actor: Actor,
        reason: Optional[str] = None,
    ) -> CustodyEvent:
        """Record artifact creation event."""
        context = CustodyContext(actor=actor, reason=reason or "Artifact created")
        return self.record_event(artifact, CustodyEventType.CREATED, context)

    def record_access(
        self,
        artifact: Artifact,
        actor: Actor,
        reason: str,
    ) -> CustodyEvent:
        """Record artifact access event."""
        context = CustodyContext(actor=actor, reason=reason)
        return self.record_event(artifact, CustodyEventType.ACCESSED, context)

    def record_verification(
        self,
        artifact: Artifact,
        actor: Actor,
        verified: bool,
    ) -> CustodyEvent:
        """Record hash verification event."""
        context = CustodyContext(
            actor=actor,
            reason=f"Hash verification: {'passed' if verified else 'failed'}",
        )
        return self.record_event(artifact, CustodyEventType.VERIFIED, context)

    def get_chain(self, artifact_id: int) -> List[CustodyEvent]:
        """Get complete custody chain for artifact."""
        return (
            self.session.query(CustodyEvent)
            .filter(CustodyEvent.artifact_id == artifact_id)
            .order_by(CustodyEvent.sequence_number)
            .all()
        )

    def verify_chain(self, artifact_id: int) -> tuple[bool, List[str]]:
        """Verify integrity of custody chain."""
        events = self.get_chain(artifact_id)
        errors = []

        for i, event in enumerate(events):
            # Check sequence
            if event.sequence_number != i + 1:
                errors.append(f"Sequence gap at event {event.id}")

            # Check hash chain
            if i > 0:
                expected_prev = events[i - 1].event_hash
                if event.previous_event_hash != expected_prev:
                    errors.append(f"Hash chain broken at event {event.id}")

            # Verify event hash
            calculated = self._calculate_event_hash(
                artifact_id=event.artifact_id,
                event_type=event.event_type,
                sequence=event.sequence_number,
                timestamp=event.created_at,
                actor=Actor(
                    name=event.actor_name,
                    role=event.actor_role,
                    organization=event.actor_organization,
                ),
                previous_hash=event.previous_event_hash,
            )
            if calculated != event.event_hash:
                errors.append(f"Event hash mismatch at event {event.id}")

        return len(errors) == 0, errors

    def _get_latest_event(self, artifact_id: int) -> Optional[CustodyEvent]:
        """Get most recent custody event for artifact."""
        return (
            self.session.query(CustodyEvent)
            .filter(CustodyEvent.artifact_id == artifact_id)
            .order_by(CustodyEvent.sequence_number.desc())
            .first()
        )

    def _calculate_event_hash(
        self,
        artifact_id: int,
        event_type: CustodyEventType,
        sequence: int,
        timestamp: datetime,
        actor: Actor,
        previous_hash: Optional[str],
    ) -> str:
        """Calculate SHA-256 hash for event."""
        data = f"{artifact_id}|{event_type.value}|{sequence}|{timestamp.isoformat()}|{actor.name}|{actor.role}|{previous_hash or ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _sign_event(self, event: CustodyEvent) -> str:
        """Sign event with RSA key."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        import base64

        private_key = load_pem_private_key(self.signing_key, password=None)
        signature = private_key.sign(
            event.event_hash.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()
```

**Acceptance Criteria**:
- [ ] Record creation, access, transfer, verification events
- [ ] Hash chain automatically maintained
- [ ] Sequence numbers auto-increment
- [ ] Optional digital signing
- [ ] Chain verification method
- [ ] Get complete chain for artifact

**Output Files**:
- `src/forensic/chain_of_custody.py`

---

### Feature 2.1.4: Automatic Custody Logging Decorator
**Target File**: `src/forensic/auto_custody.py`
**Effort**: Medium
**Agent Type**: Implementer

Decorator and context manager for automatic custody event logging.

**Implementation**:
```python
# src/forensic/auto_custody.py
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional
import threading

from .actor import Actor, CustodyContext
from .chain_of_custody import ChainOfCustody
from src.db.models.custody import CustodyEventType

# Thread-local storage for current custody context
_custody_context = threading.local()


@contextmanager
def custody_context(
    actor: Actor,
    reason: Optional[str] = None,
    session=None,
):
    """Context manager for custody tracking."""
    ctx = CustodyContext(actor=actor, reason=reason)
    _custody_context.current = ctx
    _custody_context.session = session
    try:
        yield ctx
    finally:
        _custody_context.current = None
        _custody_context.session = None


def track_custody(event_type: CustodyEventType):
    """Decorator to automatically log custody events."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Check if custody context is active
            ctx = getattr(_custody_context, "current", None)
            session = getattr(_custody_context, "session", None)

            if ctx and session:
                # Extract artifact from result or kwargs
                artifact = kwargs.get("artifact") or (
                    result if hasattr(result, "sha256") else None
                )
                if artifact:
                    coc = ChainOfCustody(session)
                    coc.record_event(artifact, event_type, ctx)

            return result
        return wrapper
    return decorator


# Integration with artifacts module
def integrate_custody_logging():
    """Patch artifact functions to auto-log custody events."""
    from src import artifacts

    original_save_capture_html = artifacts.save_capture_html

    @track_custody(CustodyEventType.CREATED)
    def patched_save_capture_html(*args, **kwargs):
        return original_save_capture_html(*args, **kwargs)

    artifacts.save_capture_html = patched_save_capture_html
    # ... similar for other artifact functions
```

**Acceptance Criteria**:
- [ ] `@track_custody` decorator for functions
- [ ] `custody_context` context manager
- [ ] Thread-safe context storage
- [ ] Integration hooks for artifact module

**Output Files**:
- `src/forensic/auto_custody.py`

---

### Feature 2.1.5: Custody Repository
**Target File**: `src/db/repositories/custody.py`
**Effort**: Medium
**Agent Type**: Implementer

Repository for custody event persistence and queries.

**Implementation**:
```python
# src/db/repositories/custody.py
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.db.models.custody import CustodyEvent, CustodyEventType


class CustodyRepository:
    """Repository for custody event operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_chain(self, artifact_id: int) -> List[CustodyEvent]:
        """Get complete custody chain for artifact."""
        stmt = (
            select(CustodyEvent)
            .where(CustodyEvent.artifact_id == artifact_id)
            .order_by(CustodyEvent.sequence_number)
        )
        return list(self.session.scalars(stmt))

    def get_latest(self, artifact_id: int) -> Optional[CustodyEvent]:
        """Get most recent custody event."""
        stmt = (
            select(CustodyEvent)
            .where(CustodyEvent.artifact_id == artifact_id)
            .order_by(CustodyEvent.sequence_number.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_by_actor(
        self,
        actor_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CustodyEvent]:
        """Get custody events by actor with optional date range."""
        conditions = [CustodyEvent.actor_name == actor_name]
        if start_date:
            conditions.append(CustodyEvent.created_at >= start_date)
        if end_date:
            conditions.append(CustodyEvent.created_at <= end_date)

        stmt = select(CustodyEvent).where(and_(*conditions))
        return list(self.session.scalars(stmt))

    def get_by_type(
        self,
        event_type: CustodyEventType,
        limit: int = 100,
    ) -> List[CustodyEvent]:
        """Get custody events by type."""
        stmt = (
            select(CustodyEvent)
            .where(CustodyEvent.event_type == event_type)
            .order_by(CustodyEvent.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count_by_artifact(self, artifact_id: int) -> int:
        """Count custody events for artifact."""
        return len(self.get_chain(artifact_id))
```

**Acceptance Criteria**:
- [ ] Get complete chain by artifact
- [ ] Get latest event
- [ ] Query by actor with date range
- [ ] Query by event type
- [ ] Count events per artifact

**Output Files**:
- `src/db/repositories/custody.py`

---

### Feature 2.1.6: Custody Report Generator
**Target File**: `src/forensic/custody_report.py`
**Effort**: Large
**Agent Type**: Implementer

Generate professional custody reports in PDF and HTML formats.

**Implementation**:
```python
# src/forensic/custody_report.py
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, PackageLoader

from src.db.models.custody import CustodyEvent
from src.db.models.artifact import Artifact


class CustodyReportGenerator:
    """Generate chain of custody reports."""

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("src.forensic", "templates"),
            autoescape=True,
        )

    def generate_html(
        self,
        artifact: Artifact,
        events: List[CustodyEvent],
        verified: bool,
        output_path: Path,
    ) -> Path:
        """Generate HTML custody report."""
        template = self.env.get_template("custody_report.html")

        html = template.render(
            artifact=artifact,
            events=events,
            verified=verified,
            generated_at=datetime.utcnow(),
            event_count=len(events),
        )

        output_path.write_text(html)
        return output_path

    def generate_pdf(
        self,
        artifact: Artifact,
        events: List[CustodyEvent],
        verified: bool,
        output_path: Path,
    ) -> Path:
        """Generate PDF custody report."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Chain of Custody Report", styles["Heading1"]))
        story.append(Spacer(1, 12))

        # Artifact info
        story.append(Paragraph("Artifact Information", styles["Heading2"]))
        artifact_data = [
            ["UUID", artifact.uuid],
            ["Type", artifact.artifact_type.value],
            ["File Path", str(artifact.file_path)],
            ["SHA-256", artifact.sha256 or "N/A"],
            ["Created", str(artifact.created_at)],
        ]
        t = Table(artifact_data, colWidths=[100, 400])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Custody events
        story.append(Paragraph("Custody Events", styles["Heading2"]))
        event_data = [["#", "Type", "Actor", "Timestamp", "Reason"]]
        for event in events:
            event_data.append([
                str(event.sequence_number),
                event.event_type.value,
                event.actor_name,
                str(event.created_at),
                event.reason or "",
            ])
        t = Table(event_data, colWidths=[30, 80, 100, 150, 140])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Verification status
        status = "VERIFIED" if verified else "VERIFICATION FAILED"
        story.append(Paragraph(f"Chain Integrity: {status}", styles["Heading2"]))

        # Attestation
        story.append(Spacer(1, 24))
        story.append(Paragraph(
            f"Report generated: {datetime.utcnow().isoformat()}",
            styles["Normal"]
        ))
        story.append(Paragraph(
            "This report was automatically generated by EDCwayback.",
            styles["Normal"]
        ))

        doc.build(story)
        return output_path
```

**Acceptance Criteria**:
- [ ] HTML report with Jinja2 template
- [ ] PDF report with ReportLab
- [ ] Artifact information section
- [ ] Complete custody event timeline
- [ ] Verification status prominently displayed
- [ ] Professional formatting

**Output Files**:
- `src/forensic/custody_report.py`
- `src/forensic/templates/custody_report.html`

---

### Feature 2.1.7: CLI Custody Commands
**Target File**: `src/cli.py` (modify)
**Effort**: Medium
**Agent Type**: Implementer

Add custody management subcommands to CLI.

**Target Commands**:
```bash
edc custody list <artifact_uuid>      # List custody events
edc custody verify <artifact_uuid>    # Verify chain integrity
edc custody report <artifact_uuid>    # Generate report
edc custody export <artifact_uuid>    # Export to JSON/CSV
```

**Acceptance Criteria**:
- [ ] `edc custody` subcommand group
- [ ] List events with table formatting
- [ ] Verify command with pass/fail exit codes
- [ ] Report generation in PDF/HTML
- [ ] Export to JSON and CSV formats

**Output Files**:
- `src/cli.py` (modified)

---

### Feature 2.1.8: API Custody Endpoints
**Target File**: `src/api.py` (modify)
**Effort**: Medium
**Agent Type**: Implementer

Add REST API endpoints for custody management.

**Endpoints**:
```
GET  /api/v1/artifacts/{uuid}/custody         # Get custody chain
GET  /api/v1/artifacts/{uuid}/custody/verify  # Verify chain
GET  /api/v1/artifacts/{uuid}/custody/report  # Download report
POST /api/v1/artifacts/{uuid}/custody/events  # Record manual event
```

**Acceptance Criteria**:
- [ ] RESTful endpoint design
- [ ] JSON response format
- [ ] PDF/HTML report download
- [ ] OpenAPI documentation
- [ ] Authentication required

**Output Files**:
- `src/api.py` (modified)

---

### Feature 2.1.9: Custody Export Formats
**Target File**: `src/forensic/custody_export.py`
**Effort**: Medium
**Agent Type**: Implementer

Export custody chains in various formats for legal proceedings.

**Implementation**:
```python
# src/forensic/custody_export.py
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List
from src.db.models.custody import CustodyEvent


class CustodyExporter:
    """Export custody chains in various formats."""

    def to_json(self, events: List[CustodyEvent], output_path: Path) -> Path:
        """Export to JSON format."""
        data = [self._event_to_dict(e) for e in events]
        output_path.write_text(json.dumps(data, indent=2, default=str))
        return output_path

    def to_csv(self, events: List[CustodyEvent], output_path: Path) -> Path:
        """Export to CSV format."""
        fieldnames = [
            "sequence", "event_type", "timestamp",
            "actor_name", "actor_role", "actor_organization",
            "reason", "artifact_hash", "event_hash",
        ]
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow({
                    "sequence": event.sequence_number,
                    "event_type": event.event_type.value,
                    "timestamp": event.created_at.isoformat(),
                    "actor_name": event.actor_name,
                    "actor_role": event.actor_role,
                    "actor_organization": event.actor_organization or "",
                    "reason": event.reason or "",
                    "artifact_hash": event.artifact_hash,
                    "event_hash": event.event_hash,
                })
        return output_path

    def to_edrm(self, events: List[CustodyEvent], output_path: Path) -> Path:
        """Export to EDRM XML format for legal production."""
        # EDRM XML implementation
        pass

    def _event_to_dict(self, event: CustodyEvent) -> dict:
        """Convert event to dictionary."""
        return {
            "uuid": event.uuid,
            "sequence_number": event.sequence_number,
            "event_type": event.event_type.value,
            "timestamp": event.created_at.isoformat(),
            "actor": {
                "name": event.actor_name,
                "role": event.actor_role,
                "organization": event.actor_organization,
                "email": event.actor_email,
            },
            "location": {
                "system_name": event.system_name,
                "ip_address": event.ip_address,
                "timezone": event.timezone,
            },
            "reason": event.reason,
            "notes": event.notes,
            "artifact_hash": event.artifact_hash,
            "previous_event_hash": event.previous_event_hash,
            "event_hash": event.event_hash,
            "signature": event.signature,
        }
```

**Acceptance Criteria**:
- [ ] JSON export with full details
- [ ] CSV export for spreadsheet analysis
- [ ] EDRM XML format for legal production
- [ ] All exports include hash chain data

**Output Files**:
- `src/forensic/custody_export.py`

---

### Feature 2.1.10: Signing Key Management
**Target File**: `src/forensic/key_management.py`
**Effort**: Medium
**Agent Type**: Implementer

Manage RSA keys for custody event signing.

**Implementation**:
```python
# src/forensic/key_management.py
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class KeyManager:
    """Manage cryptographic keys for custody signing."""

    def __init__(self, key_dir: Path):
        self.key_dir = key_dir
        self.key_dir.mkdir(parents=True, exist_ok=True)

    def generate_keypair(self, key_name: str = "custody") -> Tuple[Path, Path]:
        """Generate new RSA keypair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_path = self.key_dir / f"{key_name}_private.pem"
        public_path = self.key_dir / f"{key_name}_public.pem"

        private_path.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

        public_path.write_bytes(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

        return private_path, public_path

    def load_private_key(self, key_name: str = "custody") -> Optional[bytes]:
        """Load private key for signing."""
        path = self.key_dir / f"{key_name}_private.pem"
        if path.exists():
            return path.read_bytes()
        return None

    def load_public_key(self, key_name: str = "custody") -> Optional[bytes]:
        """Load public key for verification."""
        path = self.key_dir / f"{key_name}_public.pem"
        if path.exists():
            return path.read_bytes()
        return None
```

**Acceptance Criteria**:
- [ ] Generate RSA keypair
- [ ] Store keys securely in PEM format
- [ ] Load keys for signing/verification
- [ ] Key rotation support

**Output Files**:
- `src/forensic/key_management.py`

---

### Feature 2.1.11: Unit Tests
**Target File**: `tests/test_chain_of_custody.py`
**Effort**: Medium
**Agent Type**: Tester

Comprehensive tests for chain of custody system.

**Test Cases**:
- [ ] Create custody events
- [ ] Hash chain integrity maintained
- [ ] Sequence numbers auto-increment
- [ ] Chain verification passes for valid chain
- [ ] Chain verification fails for tampered chain
- [ ] Digital signatures generated and verified
- [ ] Report generation (HTML/PDF)
- [ ] Export formats (JSON/CSV)
- [ ] Actor context management

**Output Files**:
- `tests/test_chain_of_custody.py`
- `tests/test_custody_report.py`
- `tests/conftest.py` (add custody fixtures)

---

### Feature 2.1.12: Integration Tests
**Target File**: `tests/test_custody_integration.py`
**Effort**: Medium
**Agent Type**: Tester

End-to-end custody tracking tests.

**Test Scenarios**:
- [ ] Artifact creation triggers CREATED event
- [ ] Artifact access triggers ACCESSED event
- [ ] Full workflow: create → access → export → verify
- [ ] CLI commands work correctly
- [ ] API endpoints return correct data

**Output Files**:
- `tests/test_custody_integration.py`

---

### Feature 2.1.13: Documentation
**Target File**: `docs/forensic/chain-of-custody.md`
**Effort**: Medium
**Agent Type**: Documentation

Comprehensive chain of custody documentation.

**Sections**:
```markdown
# Chain of Custody

## Overview
- What is chain of custody
- Why it matters for e-discovery
- Legal requirements

## Configuration
- Setting up signing keys
- Actor configuration
- Storage options

## Event Types
- CREATED, ACCESSED, TRANSFERRED, etc.
- When each is triggered
- Required fields

## Using the CLI
- Recording events
- Verifying chains
- Generating reports

## API Reference
- Endpoints
- Request/response formats
- Authentication

## Report Formats
- PDF report layout
- HTML report features
- Export formats

## Best Practices
- Actor identification
- Audit procedures
- Legal hold considerations
```

**Output Files**:
- `docs/forensic/chain-of-custody.md`

---

## Verification Checklist

Before marking this phase complete:

- [ ] All 13 features implemented
- [ ] Custody events auto-logged for artifact operations
- [ ] Hash chain integrity verified
- [ ] Digital signatures working (optional)
- [ ] Reports generate correctly
- [ ] CLI and API commands functional
- [ ] Tests pass with >90% coverage
- [ ] Documentation complete

---

## Dependencies for Next Phase

Phase 2.2 (Cryptographic Verification) will build on:
- CustodyEvent model for logging verification events
- Hash calculation utilities
- Key management infrastructure
