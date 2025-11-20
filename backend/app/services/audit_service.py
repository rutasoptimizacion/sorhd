"""
Audit Logging Service
Tracks all mutations (create, update, delete) for compliance and debugging
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date
import json

from app.models.audit import AuditLog


def serialize_for_audit(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format for audit logs

    Handles:
    - datetime/date objects -> ISO format strings
    - dict objects -> recursive serialization
    - list objects -> recursive serialization
    - other objects -> string representation
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_audit(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_audit(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle Pydantic models or custom objects
        return serialize_for_audit(obj.__dict__)
    else:
        return obj


class AuditService:
    """Service for audit logging"""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        user_id: Optional[int],
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit action

        Args:
            entity_type: Type of entity (e.g., "personnel", "vehicle")
            entity_id: ID of the entity
            action: Action performed (e.g., "create", "update", "delete")
            user_id: ID of user who performed the action
            changes: Dictionary of changes (for update actions)
            ip_address: IP address of the request

        Returns:
            Created audit log entry
        """
        # Convert changes dict to JSON string, handling date/datetime objects
        changes_json = None
        if changes:
            serialized_changes = serialize_for_audit(changes)
            changes_json = json.dumps(serialized_changes)

        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            changes=changes_json,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def log_create(
        self,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log a create action"""
        return self.log_action(entity_type, entity_id, "create", user_id, ip_address=ip_address)

    def log_update(
        self,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int],
        changes: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log an update action"""
        return self.log_action(entity_type, entity_id, "update", user_id, changes, ip_address)

    def log_delete(
        self,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log a delete action"""
        return self.log_action(entity_type, entity_id, "delete", user_id, ip_address=ip_address)
