FROM python:3.13-slim
RUN pip install --no-cache-dir lxml==6.0.2
WORKDIR /opt/fmw
COPY scripts/task_runner.py scripts/workflow_*.py ./scripts/
COPY skills/feature-map-workflow/assets/task-modules.json ./skills/feature-map-workflow/assets/
COPY runtime/Dockerfile* runtime/compose*.yaml ./runtime/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-B"]
