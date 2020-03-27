FROM python:3.7

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY processing_controller processing_controller
ENTRYPOINT ["python", "-m", "processing_controller"]
