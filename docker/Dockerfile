FROM python:3.12-slim

RUN pip install --no-cache-dir pytest \
    && useradd --create-home runner

USER runner
WORKDIR /app

CMD ["pytest", "-q", "--tb=short"]