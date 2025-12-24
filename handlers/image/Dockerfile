FROM python:3.11-slim
RUN pip install --no-cache-dir pillow requests
COPY libs/taskdaemon-handlers/python/taskdaemon /usr/local/lib/python3.11/site-packages/taskdaemon
COPY handlers/image/resize_handler.py /resize_handler.py
CMD ["python", "-u", "/resize_handler.py"]
