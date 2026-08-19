from __future__ import annotations

import json
import logging
from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from sqlalchemy import text

from app.db.session import (
    SessionLocal,
)


logger = logging.getLogger(
    __name__
)


class AuditService:
    @staticmethod
    def record(
        *,
        event_type: str,
        outcome: str,
        user_id: str | None = None,
        resource_type: (
            str | None
        ) = None,
        resource_id: (
            str | None
        ) = None,
        details: (
            dict | None
        ) = None,
    ) -> None:
        """
        Best-effort security audit logging.

        Never pass:
        - passwords
        - authentication tokens
        - CSRF values
        - raw medical queries
        - document text
        - extraction contents
        - generated medical answers
        """

        safe_details = (
            details or {}
        )

        db = SessionLocal()

        try:
            db.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        event_id,
                        user_id,
                        event_type,
                        outcome,
                        resource_type,
                        resource_id,
                        details,
                        created_at
                    )
                    VALUES (
                        :event_id,
                        :user_id,
                        :event_type,
                        :outcome,
                        :resource_type,
                        :resource_id,
                        CAST(:details AS JSONB),
                        :created_at
                    )
                    """
                ),
                {
                    "event_id": str(
                        uuid4()
                    ),
                    "user_id": user_id,
                    "event_type": (
                        event_type
                    ),
                    "outcome": outcome,
                    "resource_type": (
                        resource_type
                    ),
                    "resource_id": (
                        resource_id
                    ),
                    "details": (
                        json.dumps(
                            safe_details
                        )
                    ),
                    "created_at": (
                        datetime.now(
                            timezone.utc
                        )
                    ),
                },
            )

            db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "audit_event_write_failed "
                "event_type=%s",
                event_type,
            )

        finally:
            db.close()