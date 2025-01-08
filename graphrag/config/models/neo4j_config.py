from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """The default configuration section for Neo4j."""

    uri: str | None = Field(
        description="The uri to the Neo4j DB.", default=None
    )
    username: str = Field(
        description="The neo4j username.", default="neo4j"
    )
    password: str | None = Field(
        description="The neo4j password.", default=None
    )
    database: str = Field(
        description="The neo4j database name.", default="neo4j"
    )