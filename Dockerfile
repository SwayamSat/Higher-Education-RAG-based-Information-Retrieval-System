FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for unstructured and pdf parsers
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# Install dependencies using pip
RUN pip install .

COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
