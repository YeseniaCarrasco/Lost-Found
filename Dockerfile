FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Build the SQLite database (schema + demo data) into the image.
RUN python seed.py --reset

# One worker so every request in an instance shares the same SQLite file.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
