FROM quay.io/jupyter/scipy-notebook:python-3.11

USER root

# Dependencias del sistema (necesarias para Prophet, LightGBM y compilaciones)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Librerías del proyecto
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/jovyan/work
