from pydantic import BaseModel, Field
from typing import List, Optional


class ApiEndpoint(BaseModel):
    method: str = Field(..., description="HTTP method: GET, POST, PUT, DELETE, etc.")
    path: str = Field(..., description="Endpoint path, e.g. '/api/v1/rides'")
    description: str = Field(..., description="What this endpoint does")
    request_body: str = Field(..., description="Request body schema or 'N/A'")
    response: str = Field(..., description="Response schema or description")


class SchemaEntry(BaseModel):
    table_or_collection: str = Field(..., description="Table or collection name")
    fields: List[str] = Field(..., description="List of field definitions, e.g. ['id UUID PK', 'name VARCHAR(255)']")
    indexes: List[str] = Field(..., description="Index definitions, e.g. ['idx_user_id on user_id']")
    partitioning: str = Field(..., description="Partitioning strategy, or 'None'")


class Database(BaseModel):
    type: str = Field(..., description="Database type, e.g. 'PostgreSQL', 'Cassandra', 'DynamoDB'")
    schema_: List[SchemaEntry] = Field(..., alias="schema", description="Schema tables or collections")

    model_config = {"populate_by_name": True}


class Caching(BaseModel):
    strategy: str = Field(..., description="e.g. 'cache-aside', 'write-through'")
    ttl_seconds: int = Field(..., description="Default TTL in seconds")
    cache_keys: List[str] = Field(..., description="Example cache key patterns")


class Scalability(BaseModel):
    horizontal_scaling: bool = Field(..., description="Whether horizontal scaling is supported")
    replication: str = Field(..., description="Replication strategy, e.g. 'multi-AZ primary-replica'")
    sharding_strategy: str = Field(..., description="Sharding approach, or 'None'")


class FailureMode(BaseModel):
    scenario: str = Field(..., description="Failure scenario description")
    mitigation: str = Field(..., description="How the system handles or recovers from this failure")


class Subsystem(BaseModel):
    name: str = Field(..., description="Subsystem name, matching a component from ArchitectureDesign")
    type: str = Field(..., description="e.g. 'service', 'database', 'cache'")
    api_endpoints: List[ApiEndpoint] = Field(default_factory=list)
    database: Optional[Database] = None
    caching: Optional[Caching] = None
    scalability: Scalability
    failure_modes: List[FailureMode]


class MessageQueue(BaseModel):
    name: str = Field(..., description="Queue or topic group name")
    technology: str = Field(..., description="e.g. 'Kafka', 'RabbitMQ', 'AWS SQS'")
    topics: List[str] = Field(..., description="Topic names")
    consumers: List[str] = Field(..., description="Services that consume from this queue")
    producers: List[str] = Field(..., description="Services that produce to this queue")


class SubsystemDesign(BaseModel):
    """
    Output contract for SubsystemCrew.
    Contains detailed specs for every component in the architecture.
    """

    subsystems: List[Subsystem]
    message_queues: List[MessageQueue] = Field(default_factory=list)
    external_integrations: List[str] = Field(default_factory=list, description="Third-party services used, e.g. 'Twilio SMS', 'Stripe Payments'")
