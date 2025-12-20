import json
import sys
from io import BytesIO
import requests
from PIL import Image

def process_task(task):
    task_type = task["task_type"]
    data = task["task_data"]
    
    # Download image
    resp = requests.get(data["image_url"], timeout=30)
    img = Image.open(BytesIO(resp.content))
    
    if task_type == "resize":
        img = img.resize((data["width"], data["height"]), Image.LANCZOS)
    elif task_type == "thumbnail":
        size = data["size"]
        img.thumbnail((size, size), Image.LANCZOS)
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    
    # In production, upload to S3/storage and return URL
    return {
        "status": "processed",
        "original_size": [img.width, img.height],
        "bytes": len(buffer.getvalue())
    }

for line in sys.stdin:
    task = json.loads(line)
    try:
        result = process_task(task)
        response = {"status": "success", "result": result}
    except Exception as e:
        response = {"status": "error", "error": str(e), "retryable": False}
    print(json.dumps(response), flush=True)
