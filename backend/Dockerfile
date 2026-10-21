# Usamos la versión oficial de Python (ligera)
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y fuerza a que la salida de consola sea inmediata
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para compilar ciertos paquetes (como psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero solo el archivo de requerimientos (aprovecha la caché de Docker)
COPY requirements.txt .

# Instalamos las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY . .