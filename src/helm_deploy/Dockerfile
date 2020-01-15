FROM python:3.7

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

ARG HELMVER=3.0.2
RUN \
  curl https://get.helm.sh/helm-v${HELMVER}-linux-amd64.tar.gz | tar xz  && \
  mv linux-amd64/helm /usr/local/bin/helm

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY helm_deploy.py .
ENTRYPOINT ["python", "helm_deploy.py"]
