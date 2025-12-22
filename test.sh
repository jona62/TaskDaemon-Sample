#!/bin/bash

mkdir -p output

SIZES="100x100 200x150 300x200 400x300 800x600"
declare -a TASKS

# Fire all requests
echo "Queuing tasks..."
for size in $SIZES; do
  width=${size%x*}
  height=${size#*x}
  
  TASK_ID=$(curl -s -X POST http://localhost:8080/resize \
    -H "Content-Type: application/json" \
    -d "{\"image_url\": \"https://picsum.photos/400\", \"width\": $width, \"height\": $height}" | jq -r '.task_id')
  
  TASKS+=("$TASK_ID:$size")
  echo "  $size -> $TASK_ID"
done

# Retrieve all images
echo "Downloading results..."
for entry in "${TASKS[@]}"; do
  TASK_ID=${entry%:*}
  size=${entry#*:}
  
  # Poll until completed or failed
  while true; do
    STATUS=$(curl -s http://localhost:8080/tasks/$TASK_ID | jq -r '.status')
    case $STATUS in
      completed)
        curl -s -o "output/resize_${size}.png" http://localhost:8080/images/$TASK_ID
        echo "  Saved: output/resize_${size}.png"
        break
        ;;
      failed)
        echo "  $size: failed"
        break
        ;;
      *)
        sleep 0.5
        ;;
    esac
  done
done

echo "Done. Results in ./output/"
