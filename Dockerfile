# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    libleptonica-dev \
    libtesseract-dev \
    poppler-utils \
    pngquant \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
