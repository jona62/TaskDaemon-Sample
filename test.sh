#!/bin/bash

TASK_ID=$(curl -s -X POST http://localhost:8080/resize \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/400", "width": 200, "height": 200}' | jq -r '.task_id')

while true; do
  STATUS=$(curl -s http://localhost:8080/tasks/$TASK_ID | jq -r '.status')
  case $STATUS in
    completed)
      curl -s -o output.png http://localhost:8080/images/$TASK_ID
      echo "Saved: output.png"
      break
      ;;
    failed)
      echo "Failed"
      break
      ;;
    *)
      sleep 0.1
      ;;
  esac
done
