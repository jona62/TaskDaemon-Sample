FROM python:3.11-slim
RUN pip install --no-cache-dir pillow requests
COPY libs/taskdaemon-handlers/python/taskdaemon /usr/local/lib/python3.11/site-packages/taskdaemon
COPY handlers/image/image_handler.py /handler.py
CMD ["python", "-u", "/handler.py"]
