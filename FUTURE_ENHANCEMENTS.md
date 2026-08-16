# Future Enhancements & Scaling Roadmap

While the current architecture successfully handles the required load and burst traffic on a single node, scaling to "millions of events per month" across a distributed environment would require migrating certain components. 

Here is the technical roadmap for evolving this engine into a globally distributed system:

## 1. Distributed Queueing (Celery / Kafka / RabbitMQ)
**Current:** We use `FastAPI.BackgroundTasks` and `asyncio` for the worker pool.
**Future:** To horizontally scale across multiple pods or servers, the ingestion API should immediately push webhook events to a dedicated message broker (like RabbitMQ or Apache Kafka) or a distributed task queue (like Celery backed by Redis). This decouples ingestion from processing entirely and allows us to spin up dozens of isolated worker nodes.

## 2. Distributed Rate Limiting (Redis)
**Current:** The Sliding Window rate limiter lives in the memory of the single Python process (`collections.deque`).
**Future:** In a multi-node environment, worker A and worker B need to share the same rate-limit state so they don't collectively exceed the 10 requests / 60s limit. We would implement a Redis-backed Sliding Window or Token Bucket algorithm using atomic Lua scripts to guarantee exact rate limits across a fleet of workers.

## 3. Database Migration (PostgreSQL)
**Current:** SQLite (WAL mode) is incredibly fast but is inherently bound to a single disk.
**Future:** Migrate to a managed PostgreSQL cluster (e.g., AWS RDS or Supabase). This provides true connection pooling (via PgBouncer), horizontal read replicas, and eliminates the risk of `database is locked` contention during massive write spikes from multiple horizontally scaled web nodes.

## 4. Observability & Telemetry (OpenTelemetry)
**Current:** Standard Python `logging` to stdout/stderr.
**Future:** Instrument the application with OpenTelemetry to provide distributed tracing. By passing trace IDs from the webhook ingestion all the way through to the worker dispatch and Reconciler loop, we could visualize the exact lifecycle of a DM in a tool like Datadog or Grafana, setting up automated alerting for elevated 500 error rates.

## 5. Dead Letter Queues (DLQ)
**Current:** DMs that exhaust all retries are marked as `status = 'failed'` in the main database.
**Future:** Implement a strict Dead Letter Queue (DLQ). Permanently failed jobs would be moved out of the hot path into a cold-storage DLQ, allowing engineers to manually inspect the payloads, patch the bug, and replay the queue without cluttering the primary operational tables.
