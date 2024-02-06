FROM python:3.10-slim
LABEL org.opencontainers.image.authors="samuel.dunesme@ens-lyon.fr"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# RUN git clone https://github.com/evs-gis/glourbee.git .
COPY ./ui ./ui
COPY ./glourbee ./glourbee
COPY ./setup.py ./setup.py

RUN pip3 install -e .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "ui/00_🏠_HomePage.py", "--server.port=8501", "--server.address=0.0.0.0"]