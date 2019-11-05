FROM python:3.7

RUN pip install ska_sdp_config
RUN pip install kubernetes

WORKDIR /app
COPY teststate.py .
ENTRYPOINT ["python", "teststate.py"]
