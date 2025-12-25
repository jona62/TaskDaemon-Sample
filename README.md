# TaskDaemon Sample

A sample project demonstrating [TaskDaemon](https://hub.docker.com/r/mshelia/taskdaemon) with a C++ handler for computing prime numbers.

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
git clone https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose up
```

Services:

- API: http://localhost:8081
- TaskDaemon: http://localhost:8080
- Metrics: http://localhost:8080/metrics

### Local Development

To build TaskDaemon from source (requires submodule access):

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose -f docker-compose.local.yml up --build
```

## Usage

```bash
# Find all primes up to 10 million
curl -X POST http://localhost:8081/prime \
  -H "Content-Type: application/json" \
  -d '{"limit": 10000000}'

# With priority (when using priority task selection)
curl -X POST http://localhost:8081/prime \
  -H "Content-Type: application/json" \
  -d '{"limit": 10000000, "priority": 100}'
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
handler_selection = "round-robin"  # or "first-available", "random"
```

### docker-compose.yml

```yaml
taskdaemon:
  image: mshelia/taskdaemon:latest
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
├── handlers.toml             # Handler configuration
├── docker-compose.yml        # Uses Docker Hub image
└── docker-compose.local.yml  # Builds from source
```

## Related

- [TaskDaemon on Docker Hub](https://hub.docker.com/r/mshelia/taskdaemon)
- [TaskDaemon-Handlers](https://github.com/jona62/TaskDaemon-Handlers) - Handler SDKs for all languages
