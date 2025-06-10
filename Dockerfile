FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential libmagic-dev poppler-utils tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
