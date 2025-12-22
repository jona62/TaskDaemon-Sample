# TaskDaemon Sample

A sample project demonstrating [TaskDaemon](https://github.com/jona62/TaskDaemon) with Python and C++ handlers.

## What This Demonstrates

- Rust API service queuing tasks to TaskDaemon
- Python handler for image processing (resize, thumbnail)
- C++ handler for text processing (word count)
- Handler SDKs from [TaskDaemon-Handlers](https://github.com/jona62/TaskDaemon-Handlers)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rust API      │────▶│   TaskDaemon    │────▶│  Python Handler │
│   (Axum)        │     │   (Queue)       │     │  (Pillow)       │
└─────────────────┘     └─────────────────┘     ├─────────────────┤
     POST /resize            Queue task         │  C++ Handler    │
     POST /thumbnail         Process async      │  (Word Count)   │
     POST /wordcount                            └─────────────────┘
```

## Quick Start

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
cd TaskDaemon-Sample
docker compose up --build
```

Services:
- API: http://localhost:8080
- TaskDaemon: http://localhost:3000

### With Monitoring

```bash
docker compose --profile monitoring up --build
```

Additional services:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

## Usage

```bash
# Resize an image
curl -X POST http://localhost:8080/resize \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/400", "width": 200, "height": 200}'

# Generate thumbnail
curl -X POST http://localhost:8080/thumbnail \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/400", "size": 100}'

# Word count (C++ handler)
curl -X POST http://localhost:8080/wordcount \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world from TaskDaemon"}'

# Check task status
curl http://localhost:8080/tasks/{task_id}

# Download processed image
curl -o output.png http://localhost:8080/images/{task_id}
```

## Project Structure

```
taskdaemon-sample/
├── api/                      # Rust web API (Axum)
│   └── src/main.rs
├── handlers/
│   ├── image/                # Python image handler
│   │   ├── Dockerfile
│   │   └── image_handler.py
│   └── wordcount/            # C++ word count handler
│       ├── Dockerfile
│       └── wordcount.cpp
├── libs/                     # Git submodules
│   ├── task-daemon/          # TaskDaemon server
│   └── taskdaemon-handlers/  # Handler SDKs
├── handlers.toml             # Handler configuration
└── docker-compose.yml
```

## Submodules

This project uses git submodules for TaskDaemon and Handler SDKs.

### Cloning

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
```

Or if already cloned:

```bash
git submodule update --init --recursive
```

### Updating

```bash
git submodule update --remote --merge
git add libs/
git commit -m "chore: update submodules"
```

### If submodule has local changes

```bash
cd libs/task-daemon
git checkout .
git clean -fd
cd ../..
git submodule update --remote --merge
```

## Related

- [TaskDaemon](https://github.com/jona62/TaskDaemon) - The task processing daemon
- [TaskDaemon-Handlers](https://github.com/jona62/TaskDaemon-Handlers) - Handler SDKs for all languages
