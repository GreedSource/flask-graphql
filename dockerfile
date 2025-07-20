FROM python:3.11-slim-bookworm

# No generar archivos .pyc y habilitar stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Merida

# Crear entorno virtual manualmente
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar solo lo esencial
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    gcc \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar solo el código fuente necesario
COPY server/ server/

# Comando para correr la app (ajústalo según tu entrypoint)
CMD ["python", "app.py"]
