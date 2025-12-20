import base64
from io import BytesIO
import requests
from PIL import Image
from taskdaemon import run, Task, Success, Error

def handler(task: Task) -> Success | Error:
    data = task.task_data
    
    # Download image
    resp = requests.get(data["image_url"], timeout=30)
    img = Image.open(BytesIO(resp.content))
    
    if task.task_type == "resize":
        img = img.resize((data["width"], data["height"]), Image.LANCZOS)
    elif task.task_type == "thumbnail":
        size = data["size"]
        img.thumbnail((size, size), Image.LANCZOS)
    
    # Encode as base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return Success({
        "size": [img.width, img.height],
        "format": "png",
        "data": b64
    })

if __name__ == "__main__":
    run(handler)
