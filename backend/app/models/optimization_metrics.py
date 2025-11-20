"""
Optimization Metrics Model

This model stores historical optimization metrics for business analysis.
Tracks skill gaps, assignment rates, and hiring impact simulations.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class OptimizationMetrics(Base):
    """
    Store optimization metrics for historical analysis and business insights.

    This table captures skill gap data from each optimization run,
    enabling trend analysis and data-driven hiring decisions.
    """
    __tablename__ = "optimization_metrics"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to routes (nullable - optimization may fail completely)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=True, index=True)

    # Optimization metadata
    optimization_date = Column(Date, nullable=False, index=True)
    optimization_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    strategy_used = Column(String(50), nullable=False, default="ortools")  # "ortools", "heuristic"

    # Assignment metrics
    total_cases_requested = Column(Integer, nullable=False)
    total_cases_assigned = Column(Integer, nullable=False)
    total_cases_unassigned = Column(Integer, nullable=False)
    assignment_rate_percentage = Column(Float, nullable=False)  # 0-100

    # Optimization performance
    optimization_time_seconds = Column(Float, nullable=False)
    total_distance_km = Column(Float, nullable=False, default=0.0)
    total_time_minutes = Column(Integer, nullable=False, default=0)

    # Skill gap analysis (JSONB for flexibility)
    skill_gaps = Column(JSON, nullable=False)
    # Expected structure:
    # {
    #   "unassigned_cases_by_skill": {"skill": [case_ids]},
    #   "unassigned_case_details": [{"case_id": int, "case_name": str, "required_skills": [...], "missing_skills": [...]}],
    #   "most_demanded_skills": [{"skill": str, "demand_count": int}],
    #   "skill_coverage_percentage": {"skill": float},
    #   "hiring_impact_simulation": {"skill": int}
    # }

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    route = relationship("Route", back_populates="optimization_metrics")

    def __repr__(self):
        return (
            f"<OptimizationMetrics(id={self.id}, date={self.optimization_date}, "
            f"assignment_rate={self.assignment_rate_percentage:.1f}%)>"
        )
