FROM ska-sdp-config

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

ARG HELMVER=2.14.2
RUN \
  curl https://get.helm.sh/helm-v${HELMVER}-linux-amd64.tar.gz | tar xz  && \
  mv linux-amd64/helm /usr/local/bin/helm

RUN pip install ska_sdp_config
## Copy the Pipfile
#COPY Pipfile Pipfile
#COPY Pipfile.lock Pipfile.lock
#
## Install Python deps
#RUN pipenv install --deploy --ignore-pipfile --dev

COPY workflow_switcher.py .
CMD python workflow_switcher.py
