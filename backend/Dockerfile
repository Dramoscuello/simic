FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libxml2 \
    libxslt1.1 \
    fonts-dejavu-core \
    tesseract-ocr \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

COPY icfes-reaper-cron /etc/cron.d/icfes-reaper
RUN chmod 0644 /etc/cron.d/icfes-reaper

RUN mkdir -p /app/data/chroma_db /var/log/SIMIC

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
