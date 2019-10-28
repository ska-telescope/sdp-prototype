FROM python:3.7

RUN pip install ska-sdp-config
RUN pip install jsonschema

WORKDIR /app
COPY processing_controller.py workflows.json workflows_schema.json ./
ENTRYPOINT [ "python", "processing_controller.py"]
