"""
schemas/
-------
Pydantic contracts that define the data passing between crews.

  RequirementCrew  →  RequirementSpec
  ArchitectureCrew →  ArchitectureDesign
  SubsystemCrew    →  SubsystemDesign
  ReviewCrew       →  DesignReview
  DocumentationCrew→  (produces raw Markdown, no Pydantic output)
"""

from .requirement_spec import RequirementSpec, Scale, NonFunctionalRequirements
from .architecture_design import (
    ArchitectureDesign,
    Component,
    DataFlow,
    Infrastructure,
    KeyDesignDecision,
)
from .subsystem_design import (
    SubsystemDesign,
    Subsystem,
    ApiEndpoint,
    Database,
    Caching,
    Scalability,
    FailureMode,
    MessageQueue,
)
from .design_review import (
    DesignReview,
    Issue,
    ScalabilityAssessment,
    ReliabilityAssessment,
    SecurityAssessment,
    CostAssessment,
)

__all__ = [
    # Requirement
    "RequirementSpec",
    "Scale",
    "NonFunctionalRequirements",
    # Architecture
    "ArchitectureDesign",
    "Component",
    "DataFlow",
    "Infrastructure",
    "KeyDesignDecision",
    # Subsystem
    "SubsystemDesign",
    "Subsystem",
    "ApiEndpoint",
    "Database",
    "Caching",
    "Scalability",
    "FailureMode",
    "MessageQueue",
    # Review
    "DesignReview",
    "Issue",
    "ScalabilityAssessment",
    "ReliabilityAssessment",
    "SecurityAssessment",
    "CostAssessment",
]
