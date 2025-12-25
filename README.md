# TaskDaemon Sample

A sample project demonstrating [TaskDaemon](https://github.com/jona62/TaskDaemon) with a C++ handler for computing prime numbers.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rust API      │────▶│   TaskDaemon    │────▶│  C++ Handler    │
│   (Axum)        │     │   (Queue)       │     │  (Prime Sieve)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     POST /prime             Queue task          Compute primes
```

## Quick Start

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose up --build
```

Services:
- API: http://localhost:8081
- TaskDaemon: http://localhost:8080
- Metrics: http://localhost:8080/metrics

## Usage

```bash
# Find all primes up to 10 million
curl -X POST http://localhost:8081/prime \
  -H "Content-Type: application/json" \
  -d '{"limit": 10000000}'
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Configuration

### handlers.toml

```toml
[handlers.prime]
image = "prime-handler:latest"
instances = 100                    # Number of container instances
timeout = 10                       # Task timeout in seconds
handler_selection = "round-robin"  # or "first-available"
```

### docker-compose.yml

```yaml
taskdaemon:
  environment:
    - DAEMON_WORKERS=100           # Worker threads
    - DAEMON_QUEUE_TYPE=hybrid     # In-memory queue with SQLite persistence
    - DAEMON_TASK_SELECTION=fifo   # Task ordering: fifo, lifo, priority
    - DAEMON_DB_MAX_CONNECTIONS=50 # SQLite connection pool
```

## Handler

The C++ handler uses the [TaskDaemon C++ SDK](https://github.com/jona62/TaskDaemon-Handlers) and the Sieve of Eratosthenes algorithm to find prime numbers. Computing primes up to 10 million takes ~100ms, making it ideal for demonstrating concurrent task processing.

```cpp
#include "taskdaemon.hpp"

Result handle(const Task& task) {
    int limit = task.task_data.value("limit", 1000000);
    auto primes = sieve_primes(limit);
    return success({{"count", primes.size()}});
}

int main() {
    run(handle);
}
```

## Project Structure

```
taskdaemon-sample/
├── api/                      # Rust web API (Axum)
│   └── src/main.rs
├── handlers/
│   └── prime/                # C++ prime number handler
│       ├── Dockerfile
│       └── prime.cpp
├── libs/                     # Git submodules
│   └── task-daemon/
├── handlers.toml             # Handler configuration
└── docker-compose.yml
```

## Related

- [TaskDaemon](https://github.com/jona62/TaskDaemon) - The task processing daemon
- [TaskDaemon-Handlers](https://github.com/jona62/TaskDaemon-Handlers) - Handler SDKs for all languages
