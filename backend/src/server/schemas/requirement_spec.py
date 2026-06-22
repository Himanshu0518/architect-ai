from pydantic import BaseModel, Field
from typing import List


class Scale(BaseModel):
    daily_active_users: int = Field(..., description="Estimated daily active users")
    peak_requests_per_second: int = Field(..., description="Peak RPS the system must handle")
    data_volume_tb: float = Field(..., description="Estimated total data volume in terabytes")


class NonFunctionalRequirements(BaseModel):
    availability: str = Field(..., description="Target availability, e.g. '99.99%'")
    latency_p99_ms: int = Field(..., description="p99 response latency in milliseconds")
    throughput_rps: int = Field(..., description="Sustained throughput in requests per second")
    consistency: str = Field(..., description="Consistency model, e.g. 'eventual' or 'strong'")


class RequirementSpec(BaseModel):
    """
    Output contract for RequirementCrew.
    Describes the functional and non-functional requirements for a system.
    """

    company_name: str = Field(..., description="Name of the company or product")
    system_type: str = Field(..., description="e.g. 'ride-sharing platform', 'e-commerce marketplace'")
    scale: Scale
    functional_requirements: List[str] = Field(..., description="List of what the system must do")
    non_functional_requirements: NonFunctionalRequirements
    user_personas: List[str] = Field(..., description="Key user roles interacting with the system")
    core_entities: List[str] = Field(..., description="Primary domain entities, e.g. ['User', 'Order', 'Listing']")
    assumptions: List[str] = Field(..., description="Gaps filled with industry-standard assumptions")
