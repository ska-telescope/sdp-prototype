FROM python:3.7

COPY requirements.txt *.whl ./
RUN pip install -r requirements.txt -f .

WORKDIR /app
COPY processing_controller processing_controller
ENTRYPOINT ["python", "-m", "processing_controller"]
