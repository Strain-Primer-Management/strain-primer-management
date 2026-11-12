# Development image. LEAD-ONLY FILE.
# For a production image build with: --build-arg REQUIREMENTS=requirements/prod.txt
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

ARG REQUIREMENTS=requirements/dev.txt
COPY requirements/ requirements/
RUN pip install -r ${REQUIREMENTS}

# Run as a normal user so files created in the container (e.g. migrations) are not owned by
# root on Linux hosts. Windows/macOS Docker Desktop handle ownership automatically.
ARG UID=1000
ARG GID=1000
RUN groupadd --gid ${GID} app && useradd --create-home --uid ${UID} --gid ${GID} app

COPY --chown=app:app . .
USER app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
