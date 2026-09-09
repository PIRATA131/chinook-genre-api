FROM python:3.12-slim

WORKDIR /app

# Primero las dependencias: si el codigo cambia pero requirements.txt no,
# Docker reutiliza esta capa y la construccion es mucho mas rapida.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MODEL_DIR=/app/modelo

# Comando por defecto (lo sobreescribe docker-compose en cada servicio)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
