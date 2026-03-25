

# SnapLink — Distributed URL Shortener

A high-performance, production-grade URL shortening service built with FastAPI, PostgreSQL sharding, Redis caching, and Kafka event streaming. **Capable of handling 1,500+ requests per second** on commodity hardware.

[![Performance](https://img.shields.io/badge/RPS-1497-success)](./LOAD_TEST_RESULTS.md)
[![Latency](https://img.shields.io/badge/P99-228ms-success)](./LOAD_TEST_RESULTS.md)
[![Uptime](https://img.shields.io/badge/Uptime-100%25-success)](./LOAD_TEST_RESULTS.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🎯 Performance Results

| Metric             | v2 (Async)       | v1 (Threaded)   | Target  |
| ------------------ | ---------------- | --------------- | ------- |
| **Throughput**     | **1,497 RPS**    | 1,094 RPS       | 1,000+  |
| **Total Requests** | 90,000           | 11,026          | —       |
| **P50 Latency**    | 129ms            | 38ms            | <500ms  |
| **P99 Latency**    | 228ms            | 98ms            | <500ms  |
| **Cache Hit Rate** | 100%             | 100%            | >90%    |
| **Success Rate**   | 100%             | 100%            | >99%    |
| **Duration**       | 60s              | 10s             | —       |

📊 **[View Full Load Test Results](./LOAD_TEST_RESULTS.md)**

---

## ✨ Features

- ⚡ **High-Performance Redirects** — Sub-230ms P99 latency under 1,500 RPS load
- 🔀 **Database Sharding** — Horizontal scalability via consistent hashing across 3 PostgreSQL nodes
- 💾 **Multi-Layer Caching** — Redis with look-aside + cache-null patterns (100% hit rate)
- 📊 **Real-Time Analytics** — Asynchronous click tracking via Kafka/Redpanda
- 🔭 **Observability** — Prometheus + Grafana with 10+ custom dashboards
- 🐳 **Fully Containerized** — Docker Compose orchestration across 13+ services

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐         ┌─────────────┐
│   FastAPI App    │────────▶│ Redis Cache │
│  (4 workers)     │         └─────────────┘
└────────┬─────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    ┌────────┐     ┌────────┐     ┌────────┐
    │ Shard0 │     │ Shard1 │     │ Shard2 │
    │  (PG)  │     │  (PG)  │     │  (PG)  │
    └────────┘     └────────┘     └────────┘

         ▼
    ┌──────────┐        ┌──────────────┐
    │ Redpanda │───────▶│ Analytics    │
    │  (Kafka) │        │  Worker      │
    └──────────┘        └──────────────┘
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full system design details.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- 8GB RAM minimum

### Run Locally

1. **Clone the repository**
```bash
git clone https://github.com/Rajneeshsharma125/snaplink.git
cd snaplink
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Seed the database**
```bash
python scripts/seed_db.py
```

4. **Access the app**
   - App: http://localhost:8000
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

---

## 🧪 Load Testing

```bash
# Warm up cache
python scripts/warmup_cache.py --url http://localhost:8000

# Run async load test (recommended)
python tests/load_generator.py --url http://localhost:8000 --rps 1500 --duration 60

# Analyze results
python scripts/analyze_results.py
```

---

## 🛠️ Tech Stack

| Layer           | Technology                     | Purpose                          |
| --------------- | ------------------------------ | -------------------------------- |
| **Application** | FastAPI, Python 3.11           | Async API framework              |
| **Database**    | PostgreSQL 16 (3 shards)       | Sharded persistent storage       |
| **Cache**       | Redis 7                        | High-speed in-memory cache       |
| **Messaging**   | Redpanda (Kafka-compatible)    | Async event streaming            |
| **Sharding**    | Consistent Hashing (uhashring) | Request distribution             |
| **Monitoring**  | Prometheus + Grafana           | Metrics & visualization          |
| **Deployment**  | Docker Compose, Render         | Container orchestration          |

---

## 📊 Screenshots

### Grafana — Total RPS
![Grafana Total RPS](screenshots/grafana_total_rps.png)

### Grafana — P99 Latency
![Grafana P99 Latency](screenshots/grafana_p99_latency.png)

### Grafana — Redis Hit Rate (100%)
![Redis Hit Rate](screenshots/grafana_redis_hit_rate.png)

### Prometheus — All Targets UP
![Prometheus Targets](screenshots/prometheus_targets_1.png)

---

## 🔧 Environment Variables

Create a `.env` file (see `.env.example`):

```env
DB_SHARD_0_URL=postgresql+asyncpg://user:password@db-shard-0:5432/url_shortener
DB_SHARD_1_URL=postgresql+asyncpg://user:password@db-shard-1:5432/url_shortener
DB_SHARD_2_URL=postgresql+asyncpg://user:password@db-shard-2:5432/url_shortener
REDIS_HOST=redis
REDIS_PORT=6379
KAFKA_BOOTSTRAP_SERVERS=redpanda:29092
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Rajneesh Sharma** — Final Year CSE (AI) | Ex-Adobe Product Intern | Backend Engineer

- GitHub: [@Rajneeshsharma125](https://github.com/Rajneeshsharma125)
- Email: rajneeshsharma45681@gmail.com
```

---

Paste this on GitHub, commit, and SnapLink is repo-ready. After Render deployment, just add the live URL under the badges at the top.
