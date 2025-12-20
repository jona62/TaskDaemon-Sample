# Image Processing Service

A sample Rust web service that offloads CPU-intensive image processing to Python handlers via TaskDaemon.

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
docker compose up --build
```

Services:
- API: http://localhost:8080
- TaskDaemon: http://localhost:3000

## Usage

```bash
# Resize an image
curl -X POST http://localhost:8080/resize \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/photo.jpg", "width": 800, "height": 600}'

# Generate thumbnail
curl -X POST http://localhost:8080/thumbnail \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/photo.jpg", "size": 150}'

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
├── api/                 # Rust web API
├── handlers/            # Task handlers
│   ├── image/           # Python image processing
│   └── wordcount/       # C++ word count
├── libs/                # Git submodules
│   └── taskdaemon-handlers/  # Handler SDKs
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker
- [TaskDaemon](https://github.com/jona62/TaskDaemon) cloned as sibling directory (`../task-daemon-rust`)

## Cloning

```bash
git clone --recurse-submodules https://github.com/jona62/TaskDaemon-Sample.git
```

Or if already cloned:

```bash
git submodule update --init --recursive
```

## Updating Submodules

```bash
git submodule update --remote --merge
git add libs/
git commit -m "chore: update submodules"
```
