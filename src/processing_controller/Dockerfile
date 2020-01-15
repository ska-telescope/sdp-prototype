FROM python:3.7

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY processing_controller.py workflows.json workflows_schema.json ./
ENTRYPOINT ["python", "processing_controller.py"]
