FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY . .

# Crear directorios de datos (el volumen persistente de Railway se monta en /data)
RUN mkdir -p /data data

# Exposer puerto
EXPOSE 8080

# Ejecutar aplicación - usa PORT del entorno o default 8080
ENTRYPOINT ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
