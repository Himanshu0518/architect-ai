from pydantic import BaseModel, Field
from typing import List


class Component(BaseModel):
    name: str = Field(..., description="Component name, e.g. 'Ride Matching Service'")
    type: str = Field(..., description="e.g. 'service', 'database', 'cache', 'queue', 'cdn'")
    responsibility: str = Field(..., description="What this component is responsible for")
    technology: str = Field(..., description="Chosen technology, e.g. 'PostgreSQL', 'Redis'")
    justification: str = Field(..., description="Why this technology was chosen")


class DataFlow(BaseModel):
    from_: str = Field(..., alias="from", description="Source component name")
    to: str = Field(..., description="Destination component name")
    protocol: str = Field(..., description="e.g. 'REST', 'gRPC', 'Kafka topic', 'WebSocket'")
    description: str = Field(..., description="What data is being exchanged")

    model_config = {"populate_by_name": True}


class Infrastructure(BaseModel):
    cloud_provider: str = Field(..., description="e.g. 'AWS', 'GCP', 'Azure'")
    regions: int = Field(..., description="Number of deployment regions")
    cdn: bool = Field(..., description="Whether a CDN is used")
    load_balancer: str = Field(..., description="Load balancer technology, e.g. 'AWS ALB'")
    container_orchestration: str = Field(..., description="e.g. 'Kubernetes (EKS)'")


class KeyDesignDecision(BaseModel):
    decision: str = Field(..., description="The decision made")
    rationale: str = Field(..., description="Why this decision was made")
    trade_offs: str = Field(..., description="Known trade-offs or downsides")


class ArchitectureDesign(BaseModel):
    """
    Output contract for ArchitectureCrew.
    Describes the high-level system architecture.
    """

    architecture_style: str = Field(..., description="e.g. 'microservices', 'event-driven monolith'")
    components: List[Component]
    data_flow: List[DataFlow]
    api_patterns: List[str] = Field(..., description="e.g. ['REST', 'GraphQL for client', 'gRPC internal']")
    infrastructure: Infrastructure
    key_design_decisions: List[KeyDesignDecision]
