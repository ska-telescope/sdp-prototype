FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest

COPY requirements1.txt requirements2.txt /app/
WORKDIR /app
RUN pip3 install -r requirements1.txt
RUN pip3 install -r requirements2.txt
