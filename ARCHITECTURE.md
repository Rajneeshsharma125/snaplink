Don't paste that in GitHub — that's PowerShell syntax (`@" "@` and `Out-File`). It'll look broken in the GitHub editor.

For GitHub, just paste the **clean markdown content** — no PowerShell wrapper:

---

```
# SnapLink Architecture

## Overview
SnapLink is a distributed URL shortener built with FastAPI, designed to handle high throughput with low latency.

## Components

### API Layer
- **FastAPI** async endpoints for URL shortening and redirection
- JWT-based authentication
- Input validation and error handling

### Database Layer
- **PostgreSQL** sharded across 3 nodes
- Consistent hashing for shard routing
- Each shard handles ~33% of the keyspace

### Caching Layer
- **Redis** in-memory cache
- 100% cache hit rate under load
- TTL-based expiry for stale URLs

### Async Analytics
- **Kafka** for async click event streaming
- Worker consumes events and writes to analytics DB
- Decoupled from critical path — zero latency impact

### Monitoring
- **Prometheus** for metrics scraping
- **Grafana** dashboards for RPS, latency (P50/P99), cache hit rate

## Request Flow
1. Client sends POST /shorten
2. API hashes URL → determines shard via consistent hashing
3. Checks Redis cache first
4. On miss → writes to correct PostgreSQL shard
5. Returns short URL
6. On redirect → Redis hit → instant response
7. Click event published to Kafka asynchronously
```

---

Paste only this into the GitHub editor and commit!
