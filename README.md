# TaskDaemon Sample

A Rust HTTP API submits prime-number jobs to [TaskDaemon](https://hub.docker.com/r/mshelia/taskdaemon). Four persistent C++ handler containers execute them using the [TaskDaemon C++ SDK](https://github.com/jona62/TaskDaemon-Handlers).

## Quick Start

Docker must be running. This sample gives TaskDaemon access to the host Docker socket so it can launch handler containers.

```bash
git clone https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose up --build
```

Compose builds the API and prime handler, starts TaskDaemon, and waits for its health check before starting the API. The default daemon image is `mshelia/taskdaemon:0.2.0-alpha`; set `TASKDAEMON_IMAGE` to use another compatible image.

The Docker Hub workflow uses the C++ SDK header already included in this sample and does not require access to the private daemon source submodule. To inspect the public SDK source, initialize only that submodule:

```bash
git submodule update --init libs/taskdaemon-handlers
```

The included C++ header matches SDK release `v0.1.2`, which is pinned by `libs/taskdaemon-handlers`.

Services are published on loopback:

- Sample API: http://localhost:8081
- TaskDaemon HTTP API and dashboard: http://localhost:8080
- Prometheus metrics: http://localhost:8080/metrics
- TaskDaemon gRPC: localhost:50051

If a port is occupied, set `SAMPLE_API_PORT`, `TASKDAEMON_HTTP_PORT`, or `TASKDAEMON_GRPC_PORT` before starting Compose. Containers continue to use ports 8081, 8080, and 50051 internally.

To build the daemon from the pinned source submodule instead, you need GitHub access to the private TaskDaemon repository:

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose -f docker-compose.local.yml up --build
```

For an existing clone, explicitly run `git submodule update --init --recursive` before the source build. The API Docker build uses Rust 1.91.0 and the checked-in `api/Cargo.lock` with `--locked`.

## Submit and Check Tasks

```bash
curl --fail-with-body -X POST http://localhost:8081/prime \
  -H "Content-Type: application/json" \
  -d '{"limit": 1000000}'
```

The response contains the queued task's ID:

```json
{"task_id":"550e8400-e29b-41d4-a716-446655440000"}
```

Query that ID to inspect completion and the result:

```bash
curl --fail-with-body http://localhost:8080/api/tasks/550e8400-e29b-41d4-a716-446655440000
```

The task starts as `pending` or `processing`, then becomes `completed` with `result.limit`, `result.count`, `result.largest`, and `result.duration_ms`, or `failed` with `last_error`. An empty pending queue does not prove that processing tasks have finished.

The handler accepts integer limits from 2 through 10,000,000. It rejects larger or invalid limits with a nonretryable error before allocating the sieve. A limit of 1,000,000 produces 78,498 primes, with 999,983 as the largest.

Priority belongs to TaskDaemon's `/queue` endpoint. To use it, start Compose with `DAEMON_TASK_SELECTION=priority`, then submit directly:

```bash
curl --fail-with-body -X POST http://localhost:8080/queue \
  -H "Content-Type: application/json" \
  -d '{"type":"prime","data":{"limit":1000000},"priority":100}'
```

Higher priority values are selected first. The sample `/prime` API accepts `limit` only.

## Configuration and Persistence

The defaults use four workers, four prime handler instances, batch size 5, and a 20-connection SQLite pool. Workers are asynchronous task executors. A larger batch changes how many queue claims each worker prefetches; it does not create more handler instances. `DAEMON_BATCH_SIZE` must be positive.

```toml
# handlers.toml
[handlers.prime]
image = "prime-handler:latest"
instances = 4
memory_limit = "64m"
handler_selection = "round-robin"
# Add timeout = 10 here to override the global timeout for this handler.
```

Compose accepts these environment overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DAEMON_WORKERS` | `4` | Worker count |
| `DAEMON_BATCH_SIZE` | `5` | Queue claim batch size |
| `DAEMON_DB_MAX_CONNECTIONS` | `20` | SQLite pool maximum |
| `DAEMON_QUEUE_TYPE` | `hybrid` | `hybrid`, `sqlite`, or `memory` |
| `DAEMON_TASK_SELECTION` | `fifo` | `fifo`, `lifo`, or `priority` |
| `DAEMON_TASK_TIMEOUT` | `30` | Global task timeout in seconds |
| `DAEMON_MAX_RETRIES` | `3` | Retry budget for retryable handler errors; `0` disables retries |

`hybrid` uses SQLite for durable storage and task claims, with a task lookup cache. `sqlite` also persists tasks; `memory` does not. SQLite data lives at `/data/task_queue.db` in the named `taskdaemon-data` volume and survives `docker compose down`. `docker compose down --volumes` deletes that data.

The prime handler omits its timeout setting, so it inherits `DAEMON_TASK_TIMEOUT`. An explicit handler `timeout` overrides the global value. Queue metrics are sampled once per second; `/health` queries the pending queue size directly. Use task statuses to verify completion.

## Smoke and Load Checks

With the sample already running, use Python 3 to submit and verify one task:

```bash
scripts/smoke-test.sh
```

The load check submits 100 tasks with four concurrent HTTP clients and waits for every returned ID to become `completed` with a valid result:

```bash
./load-test.sh
TASKS=500 CONCURRENCY=4 LIMIT=1000000 TIMEOUT=120 ./load-test.sh
```

For custom ports, set `API_URL=http://localhost:18081` and `DAEMON_URL=http://localhost:18080`. The checker reports submission time and total time, fails on HTTP errors, failed tasks, invalid results, or a deadline, and does not start services automatically. Workers execute while submission is in progress, so the reported throughput includes HTTP submission and status polling. It is not a prefilled-queue drain benchmark. Runtime depends on hardware and workload.

Run checker regression tests without Docker:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The CI workflow runs these regressions, builds the sample API and handler against the published daemon image, checks one smoke task and 100 load tasks, and removes its containers and data afterward. It initializes the public SDK submodule only.

## Monitoring

```bash
docker compose --profile monitoring up --build
```

Prometheus is available at http://localhost:9090 and Grafana at http://localhost:3001. The local Grafana login is `admin` / `admin`.
