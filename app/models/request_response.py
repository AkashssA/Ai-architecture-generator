from pydantic import BaseModel, Field


class ArchitectureRequest(BaseModel):
    system_prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Short system design prompt such as 'Design Netflix'.",
        examples=["Design a scalable URL shortener"],
    )


class ComponentModel(BaseModel):
    name: str = Field(..., examples=["API Gateway"])
    kind: str = Field(..., examples=["gateway"])
    responsibilities: list[str] = Field(default_factory=list)
    communicates_with: list[str] = Field(default_factory=list)


class ApiEndpointModel(BaseModel):
    method: str = Field(..., examples=["POST"])
    path: str = Field(..., examples=["/api/v1/shorten"])
    purpose: str = Field(..., examples=["Create a new short link"])


class ArchitectureResponse(BaseModel):
    title: str
    components: list[ComponentModel]
    description: str
    mermaid_diagram: str
    api_design: list[ApiEndpointModel]
    scaling_strategy: str


class HealthResponse(BaseModel):
    status: str
    service: str
