FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "gunicorn -w 1 -b 0.0.0.0:${PORT:-8000} app.main:app"]
