# Image Processing Service

A sample Rust web service that offloads CPU-intensive image processing to Python handlers via TaskDaemon.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rust API      │────▶│   TaskDaemon    │────▶│  Python Handler │
│   (Axum)        │     │   (Queue)       │     │  (Pillow)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     POST /resize            Queue task           Resize image
     POST /thumbnail         Process async        Generate thumbnail
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

# Check task status
curl http://localhost:8080/tasks/{task_id}
```

## Project Structure

```
taskdaemon-sample/
├── api/                 # Rust web API
├── handlers/            # Python image processing handlers
├── libs/                # Git submodules
│   └── taskdaemon-handlers/  # Handler SDKs
├── docker-compose.yml
└── README.md
```

## Cloning

```bash
git clone --recurse-submodules https://github.com/youruser/taskdaemon-sample.git
```

Or if already cloned:

```bash
git submodule update --init --recursive
```

## Updating the SDK Submodule

```bash
cd libs/taskdaemon-handlers
git pull origin main
cd ../..
git add libs/taskdaemon-handlers
git commit -m "chore: update taskdaemon-handlers submodule"
```
