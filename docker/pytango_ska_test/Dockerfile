FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest AS buildenv

USER root
COPY requirements.txt /app
WORKDIR /app
RUN pip3 install -r requirements.txt
