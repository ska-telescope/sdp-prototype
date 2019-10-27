FROM python:3.7

RUN pip install ska_sdp_config

WORKDIR /app
COPY testdeploy.py .
ENTRYPOINT ["python", "testdeploy.py"]
