import hashlib
import json
import logging
from typing import Any

from fastapi.encoders import jsonable_encoder

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None

from app.core.cache import CacheBackend
from app.core.config import Settings
from app.core.exceptions import ArchitectureGenerationError
from app.models.request_response import (
    ApiEndpointModel,
    ArchitectureRequest,
    ArchitectureResponse,
    ComponentModel,
)
from app.utils.mermaid_generator import build_mermaid_diagram

logger = logging.getLogger(__name__)


class ArchitectureGeneratorService:
    def __init__(self, settings: Settings, cache: CacheBackend) -> None:
        self.settings = settings
        self.cache = cache
        self.client = (
            AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.groq_api_key,
                timeout=settings.groq_timeout_seconds,
            )
            if settings.groq_api_key and AsyncOpenAI
            else None
        )

    async def generate(self, payload: ArchitectureRequest) -> ArchitectureResponse:
        cache_key = self._cache_key(payload.system_prompt)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("Cache hit for prompt: %s", payload.system_prompt)
            return ArchitectureResponse.model_validate(cached)

        raw_data = await self._generate_architecture_data(payload.system_prompt)
        response = self._build_response(raw_data)
        await self.cache.set(
            cache_key,
            jsonable_encoder(response),
            ttl_seconds=self.settings.cache_ttl_seconds,
        )
        return response

    async def _generate_architecture_data(self, system_prompt: str) -> dict[str, Any]:
        if self.client:
            try:
                return await self._generate_with_llm(system_prompt)
            except Exception as exc:  # pragma: no cover
                logger.exception("LLM generation failed; falling back to deterministic mode.")
                logger.warning("LLM error: %s", exc)

        return self._generate_fallback_architecture(system_prompt)

    async def _generate_with_llm(self, system_prompt: str) -> dict[str, Any]:
        completion = await self.client.chat.completions.create(
            model=self.settings.groq_model,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Principal Staff Systems Architect at a top-tier tech company. "
                        "You design hyper-scalable, production-ready, domain-specific system architectures. "
                        "You must deeply analyze the use case and include necessary specialized components "
                        "(e.g., WebSockets for real-time, CDN/Object Storage for media, Pub/Sub for events, sharding strategies, presence services). "
                        "Avoid generic 3-tier templates. Think deeply about delivery guarantees, fault tolerance, and concurrency. "
                        "Always return strict JSON and no markdown."
                    ),
                },
                {"role": "user", "content": self._build_prompt(system_prompt)},
            ],
        )
        content = completion.choices[0].message.content
        if not content:
            raise ArchitectureGenerationError("The LLM returned an empty response.")
        return json.loads(content)

    def _build_prompt(self, system_prompt: str) -> str:
        return f"""
Generate a comprehensive, production-ready system architecture for the following domain:
"{system_prompt}"

Return strict JSON only, using this exact schema:
{{
  "title": "string (A professional title for the architecture)",
  "description": "string (A detailed architectural summary explaining the core design choices, data flow, and specialized components)",
  "components": [
    {{
      "name": "string (Short, Mermaid-friendly name)",
      "kind": "string (e.g., client, edge, gateway, service, database, cache, queue, websocket, storage, pubsub, worker)",
      "responsibilities": ["string (Be specific to the domain, not generic)"],
      "communicates_with": ["string (Exact names of other components)"]
    }}
  ],
  "api_design": [
    {{
      "method": "GET|POST|PUT|PATCH|DELETE|WS",
      "path": "/path",
      "purpose": "string"
    }}
  ],
  "scaling_strategy": "string (Explain how to handle millions of users, sharding, partitioning, event streams, and bottleneck mitigation)"
}}

CRITICAL INSTRUCTIONS:
1. DO NOT return a generic template. The architecture MUST be highly specific to the requested domain.
2. If real-time, include WebSockets/SSE, Presence Services, and Event Streaming (Pub/Sub, Kafka).
3. If media-heavy, include CDNs, Object Storage, and transcoding workers.
4. If transaction-heavy, include distributed locks, idempotency, and ACID-compliant relational stores.
5. Provide 5 to 10 practical, domain-specific endpoints/connections (include WS paths if applicable).
6. Provide deeply technical component responsibilities (e.g., "Maintains persistent TCP connections", "Fans out messages via Pub/Sub", "Handles offline delivery retries").
7. Ensure all communication paths are realistic and explicitly named.
8. Output MUST be valid, parseable JSON with NO markdown blocks (do not use ```json fences).
""".strip()

    def _build_response(self, raw_data: dict[str, Any]) -> ArchitectureResponse:
        try:
            components = [
                ComponentModel.model_validate(item)
                for item in raw_data.get("components", [])
            ]
            api_design = [
                ApiEndpointModel.model_validate(item)
                for item in raw_data.get("api_design", [])
            ]
        except Exception as exc:
            raise ArchitectureGenerationError("Failed to validate generated architecture.") from exc

        if not components:
            raise ArchitectureGenerationError("Generated architecture contained no components.")

        return ArchitectureResponse(
            title=raw_data.get("title", "System Architecture"),
            components=components,
            description=raw_data.get("description", "Architecture description unavailable."),
            mermaid_diagram=build_mermaid_diagram(components),
            api_design=api_design,
            scaling_strategy=raw_data.get(
                "scaling_strategy",
                "Scale stateless services horizontally, place hot reads behind caches, "
                "and isolate asynchronous workloads behind durable queues.",
            ),
        )

    def _generate_fallback_architecture(self, system_prompt: str) -> dict[str, Any]:
        prompt = system_prompt.lower()

        if "url shortener" in prompt:
            return {
                "title": "Scalable URL Shortener Architecture",
                "description": (
                    "Clients enter through an edge layer and hit stateless API services. "
                    "The write path stores mappings in the primary database and warms Redis, "
                    "while redirect reads are served from cache first to minimize latency."
                ),
                "components": [
                    {"name": "User", "kind": "client", "responsibilities": ["Creates and opens short links"], "communicates_with": ["CDN"]},
                    {"name": "CDN", "kind": "edge", "responsibilities": ["Caches redirects and static content"], "communicates_with": ["Load Balancer"]},
                    {"name": "Load Balancer", "kind": "network", "responsibilities": ["Distributes traffic"], "communicates_with": ["API Service"]},
                    {"name": "API Service", "kind": "backend", "responsibilities": ["Creates short links", "Resolves redirects"], "communicates_with": ["Redis Cache", "Primary DB", "Analytics Queue"]},
                    {"name": "Redis Cache", "kind": "cache", "responsibilities": ["Stores hot key mappings"], "communicates_with": ["Primary DB"]},
                    {"name": "Primary DB", "kind": "database", "responsibilities": ["Stores canonical URL mappings"], "communicates_with": ["Analytics Worker"]},
                    {"name": "Analytics Queue", "kind": "queue", "responsibilities": ["Buffers click events"], "communicates_with": ["Analytics Worker"]},
                    {"name": "Analytics Worker", "kind": "worker", "responsibilities": ["Builds usage reports"], "communicates_with": ["Primary DB"]},
                ],
                "api_design": [
                    {"method": "POST", "path": "/api/v1/links", "purpose": "Create a short URL"},
                    {"method": "GET", "path": "/{short_code}", "purpose": "Resolve and redirect to the original URL"},
                    {"method": "GET", "path": "/api/v1/links/{short_code}", "purpose": "Fetch link metadata"},
                    {"method": "DELETE", "path": "/api/v1/links/{short_code}", "purpose": "Delete a short link"},
                    {"method": "GET", "path": "/api/v1/links/{short_code}/analytics", "purpose": "Get click analytics"},
                ],
                "scaling_strategy": (
                    "Keep the API tier stateless for horizontal scaling, place Redis and the CDN "
                    "in front of the database for hot reads, shard data by short code, and move "
                    "analytics to queue-backed workers. Add read replicas, retries, tracing, and autoscaling."
                ),
            }

        if "netflix" in prompt or "stream" in prompt:
            return {
                "title": "Video Streaming Platform Architecture",
                "description": (
                    "Users request playback metadata through an API gateway while video segments "
                    "are delivered from object storage through a CDN. Stateful playback concerns "
                    "are isolated into session services, and recommendation pipelines consume events asynchronously."
                ),
                "components": [
                    {"name": "User", "kind": "client", "responsibilities": ["Consumes content"], "communicates_with": ["CDN"]},
                    {"name": "CDN", "kind": "edge", "responsibilities": ["Delivers video segments"], "communicates_with": ["API Gateway", "Object Storage"]},
                    {"name": "API Gateway", "kind": "gateway", "responsibilities": ["Routes authenticated requests"], "communicates_with": ["Catalog Service", "Playback Service", "User Service"]},
                    {"name": "Catalog Service", "kind": "service", "responsibilities": ["Serves content metadata"], "communicates_with": ["Catalog DB", "Redis Cache"]},
                    {"name": "Playback Service", "kind": "service", "responsibilities": ["Creates playback sessions"], "communicates_with": ["Session Cache", "Object Storage"]},
                    {"name": "User Service", "kind": "service", "responsibilities": ["Manages profiles and subscriptions"], "communicates_with": ["User DB"]},
                    {"name": "Recommendation Service", "kind": "service", "responsibilities": ["Generates personalized rails"], "communicates_with": ["Event Queue", "Analytics Store"]},
                    {"name": "Event Queue", "kind": "queue", "responsibilities": ["Streams watch events"], "communicates_with": ["Recommendation Service"]},
                    {"name": "Catalog DB", "kind": "database", "responsibilities": ["Stores title metadata"], "communicates_with": []},
                    {"name": "User DB", "kind": "database", "responsibilities": ["Stores accounts and profiles"], "communicates_with": []},
                    {"name": "Redis Cache", "kind": "cache", "responsibilities": ["Caches hot metadata"], "communicates_with": []},
                    {"name": "Session Cache", "kind": "cache", "responsibilities": ["Stores session state"], "communicates_with": []},
                    {"name": "Object Storage", "kind": "storage", "responsibilities": ["Stores encoded video files"], "communicates_with": []},
                    {"name": "Analytics Store", "kind": "warehouse", "responsibilities": ["Supports recommendation training"], "communicates_with": []},
                ],
                "api_design": [
                    {"method": "POST", "path": "/api/v1/auth/login", "purpose": "Authenticate a subscriber"},
                    {"method": "GET", "path": "/api/v1/catalog/home", "purpose": "Fetch homepage rails"},
                    {"method": "GET", "path": "/api/v1/catalog/titles/{title_id}", "purpose": "Fetch title details"},
                    {"method": "POST", "path": "/api/v1/playback/sessions", "purpose": "Start playback for a title"},
                    {"method": "GET", "path": "/api/v1/recommendations", "purpose": "Fetch personalized recommendations"},
                ],
                "scaling_strategy": (
                    "Push media delivery to CDN edges, keep APIs stateless, separate metadata and "
                    "session workloads, and process watch telemetry asynchronously. Replicate content "
                    "globally, shard high-volume stores, and instrument playback flows with tracing and metrics."
                ),
            }

        if "uber" in prompt or "ride" in prompt:
            return {
                "title": "Ride Sharing Platform Architecture",
                "description": (
                    "Rider and driver applications communicate with an API gateway that fans out "
                    "to trip orchestration, geospatial tracking, and payment services. Real-time "
                    "location updates feed a matching engine while events are streamed to analytics."
                ),
                "components": [
                    {"name": "Rider App", "kind": "client", "responsibilities": ["Requests rides"], "communicates_with": ["API Gateway"]},
                    {"name": "Driver App", "kind": "client", "responsibilities": ["Publishes location", "Accepts trips"], "communicates_with": ["API Gateway"]},
                    {"name": "API Gateway", "kind": "gateway", "responsibilities": ["Routes requests", "Handles auth"], "communicates_with": ["Trip Service", "Location Service", "Payment Service"]},
                    {"name": "Trip Service", "kind": "service", "responsibilities": ["Manages trip lifecycle"], "communicates_with": ["Matching Engine", "Trip DB", "Event Bus"]},
                    {"name": "Location Service", "kind": "service", "responsibilities": ["Processes driver coordinates"], "communicates_with": ["Geo Index", "Matching Engine"]},
                    {"name": "Matching Engine", "kind": "service", "responsibilities": ["Matches nearby drivers"], "communicates_with": ["Geo Index", "Event Bus"]},
                    {"name": "Payment Service", "kind": "service", "responsibilities": ["Charges completed trips"], "communicates_with": ["Payment DB"]},
                    {"name": "Trip DB", "kind": "database", "responsibilities": ["Stores trip state"], "communicates_with": []},
                    {"name": "Geo Index", "kind": "database", "responsibilities": ["Supports geospatial lookups"], "communicates_with": []},
                    {"name": "Payment DB", "kind": "database", "responsibilities": ["Stores payment records"], "communicates_with": []},
                    {"name": "Event Bus", "kind": "queue", "responsibilities": ["Streams telemetry and events"], "communicates_with": ["Analytics Worker"]},
                    {"name": "Analytics Worker", "kind": "worker", "responsibilities": ["Builds forecasting data"], "communicates_with": []},
                ],
                "api_design": [
                    {"method": "POST", "path": "/api/v1/rides", "purpose": "Request a ride"},
                    {"method": "POST", "path": "/api/v1/rides/{ride_id}/accept", "purpose": "Accept a ride"},
                    {"method": "PATCH", "path": "/api/v1/rides/{ride_id}/status", "purpose": "Update ride status"},
                    {"method": "POST", "path": "/api/v1/drivers/location", "purpose": "Send location updates"},
                    {"method": "POST", "path": "/api/v1/payments/authorize", "purpose": "Authorize a trip payment"},
                ],
                "scaling_strategy": (
                    "Scale trip orchestration, location ingestion, and matching independently, "
                    "partition geospatial data by region, and use an event bus for non-blocking "
                    "telemetry and analytics. Add regional failover, idempotent writes, and strong SLO monitoring."
                ),
            }

        base_name = system_prompt.strip().title()
        return {
            "title": f"{base_name} Architecture",
            "description": (
                "Users enter through edge infrastructure that routes traffic into stateless "
                "application services. Core services coordinate cached reads, durable writes, "
                "and queue-backed background processing for asynchronous workloads."
            ),
            "components": [
                {"name": "User", "kind": "client", "responsibilities": ["Sends application requests"], "communicates_with": ["CDN"]},
                {"name": "CDN", "kind": "edge", "responsibilities": ["Caches static and hot content"], "communicates_with": ["Load Balancer"]},
                {"name": "Load Balancer", "kind": "network", "responsibilities": ["Distributes traffic across app instances"], "communicates_with": ["App Service"]},
                {"name": "App Service", "kind": "backend", "responsibilities": ["Executes business logic"], "communicates_with": ["Redis Cache", "Primary DB", "Message Queue"]},
                {"name": "Redis Cache", "kind": "cache", "responsibilities": ["Accelerates hot reads"], "communicates_with": ["Primary DB"]},
                {"name": "Primary DB", "kind": "database", "responsibilities": ["Stores authoritative data"], "communicates_with": ["Worker Service"]},
                {"name": "Message Queue", "kind": "queue", "responsibilities": ["Buffers async tasks"], "communicates_with": ["Worker Service"]},
                {"name": "Worker Service", "kind": "worker", "responsibilities": ["Processes background jobs"], "communicates_with": ["Analytics Store"]},
                {"name": "Analytics Store", "kind": "warehouse", "responsibilities": ["Supports reporting"], "communicates_with": []},
            ],
            "api_design": [
                {"method": "POST", "path": "/api/v1/resources", "purpose": "Create a resource"},
                {"method": "GET", "path": "/api/v1/resources/{resource_id}", "purpose": "Fetch a resource"},
                {"method": "PATCH", "path": "/api/v1/resources/{resource_id}", "purpose": "Update a resource"},
                {"method": "DELETE", "path": "/api/v1/resources/{resource_id}", "purpose": "Delete a resource"},
                {"method": "GET", "path": "/api/v1/health/dependencies", "purpose": "Check dependency health"},
            ],
            "scaling_strategy": (
                "Scale stateless services horizontally, put hot reads behind Redis and edge caches, "
                "move slower workloads to queue-backed workers, and protect the database with read "
                "replicas, backups, monitoring, and distributed tracing."
            ),
        }

    @staticmethod
    def _cache_key(system_prompt: str) -> str:
        digest = hashlib.sha256(system_prompt.strip().lower().encode("utf-8")).hexdigest()
        return f"architecture:{digest}"
