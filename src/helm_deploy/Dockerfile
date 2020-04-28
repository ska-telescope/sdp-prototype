FROM python:3.7

ARG HELM_VERSION=3.2.0

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

RUN curl https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz | tar xz \
    && install linux-amd64/helm /usr/local/bin/helm \
    && rm -r linux-amd64

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY helm_deploy.py ./
ENTRYPOINT ["python", "helm_deploy.py"]
