# # Use official Python slim image
# FROM python:3.10-slim

# # Set working directory
# WORKDIR /app

# # Install required system packages
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libmagic-dev \
#     poppler-utils \
#     tesseract-ocr \
#     && rm -rf /var/lib/apt/lists/*

# # Copy project files
# COPY . .

# # Install Python dependencies
# RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# # Expose FastAPI port
# EXPOSE 8000

# # Run the app with Uvicorn
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
      build-essential libmagic-dev poppler-utils tesseract-ocr \
      && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 80                       # keep 80 for both roles
COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

