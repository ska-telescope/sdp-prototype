FROM python:3.7

RUN pip install ska-sdp-config

WORKDIR /app
COPY processing_controller.py .
ENTRYPOINT [ "python", "processing_controller.py"]
