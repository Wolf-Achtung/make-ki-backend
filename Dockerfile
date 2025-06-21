FROM python:3.10-slim

# System-Update und grundlegende Tools installieren
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# Arbeitsverzeichnis setzen
WORKDIR /app

# Projektdateien kopieren
COPY . .

# Abhängigkeiten installieren
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Gunicorn für Produktion verwenden
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]

