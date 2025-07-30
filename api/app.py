#!/usr/bin/env python3
# Add CORS support and typing
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import re
import os
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        redis_client = redis.Redis.from_url(REDIS_URL)
    else:
        redis_client = None
except ImportError:
    redis_client = None
import logging
import structlog
from pathlib import Path
from time import time
from collections import defaultdict, deque

# Import manifest and enrichment
from scripts.generate_doc import load_manifest
from scripts.enrich_manifest import enrich_manifest, load_schema
from jsonschema import validate, ValidationError

# Setup structlog for JSON output
# Configure standard logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
StructLogger = structlog.stdlib.LoggerFactory()
structlog.configure(
    logger_factory=StructLogger,
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Setup Jinja2 environment
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)
tpl = env.get_template("connector.md.j2")

app = FastAPI(title="Data Hub Connector Docs API")

@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    logger.info("health_check")
    return {"status": "ok"}

# Allow public access from docs site / localhost; adjust origins if needed
# Configure CORS allowed origins via ALLOWED_ORIGINS env var
origins_env = os.getenv("ALLOWED_ORIGINS", "")
if origins_env:
    allow_origins = [o.strip() for o in origins_env.split(",")]
else:
    allow_origins = ["http://127.0.0.1:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- simple in-memory rate limiter ----
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 5      # max requests per window per IP
_ip_hits: dict[str, deque] = defaultdict(deque)

def rate_limited(ip: str) -> bool:
    """Return True if IP exceeded rate, else False (and record hit)."""
    now = time()
    if redis_client:
        key = f"rate:{ip}"
        redis_client.zadd(key, {now: now})
        redis_client.zremrangebyscore(key, 0, now - RATE_LIMIT_WINDOW)
        redis_client.expire(key, RATE_LIMIT_WINDOW)
        count = redis_client.zcard(key)
        if count >= RATE_LIMIT_MAX:
            return True
        return False
    q = _ip_hits[ip]
    while q and now - q[0] > RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX:
        return True
    q.append(now)
    return False

# -------------------------------------------------------------
# Main endpoint
# -------------------------------------------------------------
@app.get("/doc/{slug}")
def get_doc(slug: str, ai: bool = False, request: Request | None = None):
    # rate-limit check
    client_ip = request.client.host if request else "unknown"
    # Mask IP for logging (PII protection)
    if client_ip != "unknown":
        parts = client_ip.split('.')
        log_ip = '.'.join(parts[:3] + ['x']) if len(parts) == 4 else client_ip
    else:
        log_ip = client_ip
    logger.info("doc_requested", slug=slug, ai=ai, client_ip=log_ip)
    if rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests/minute.")
    """
    Return connector documentation markdown for given slug.
    Optional AI enrichment with ?ai=true.
    """
    # Find manifest file
    manifest_path = None
    for ext in ("yaml", "yml", "json"):
        p = Path("manifests") / f"{slug}.{ext}"
        if p.exists():
            manifest_path = p
            break

    if manifest_path:
        data = load_manifest(manifest_path)
        # Validate manifest schema
        schema = load_schema()
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid manifest schema: {e}")
    else:
        # Create minimal stub manifest and let AI enrich it
        display_name = re.sub(r"[_-]+", " ", slug).strip().title()
        data = {
            "slug": slug,
            "displayName": display_name,
        }

    # AI enrichment
    if ai:
        data = enrich_manifest(data)
    # Render markdown
    markdown_content = tpl.render(**data)
    return {"slug": slug, "markdown": markdown_content} 