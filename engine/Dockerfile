FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir --upgrade "setuptools>=80.9.0" "wheel>=0.46.2" && \
    pip install --no-cache-dir .

FROM python:3.11-slim

RUN groupadd -r agent33 && useradd -r -g agent33 -d /app agent33
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ src/
COPY templates/ templates/
COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade "setuptools>=80.9.0" "wheel>=0.46.2" && \
    pip install --no-cache-dir -e .

USER agent33
EXPOSE 8000

CMD ["uvicorn", "agent33.main:app", "--host", "0.0.0.0", "--port", "8000"]
