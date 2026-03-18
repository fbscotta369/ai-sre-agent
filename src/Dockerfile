FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip==24.0 \
    && pip install --no-cache-dir flask==3.0.0 gunicorn==21.2.0 requests==2.31.0 urllib3==2.2.0

COPY app.py .
COPY agent.py .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
