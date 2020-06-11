FROM python:3.7

ARG KUBE_VERSION=1.18.2
ARG HELM_VERSION=3.2.0

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /root

# Install kubectl

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl \
    && install kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Install helm

RUN curl -L https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz | tar xz \
    && install linux-amd64/helm /usr/local/bin/helm \
    && rm -r linux-amd64

# Install Python packages

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
CMD ["/bin/bash", "-c", "trap : INT TERM; sleep infinity & wait"]
