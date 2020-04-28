FROM python:3.7

WORKDIR /app
COPY requirements.txt .
COPY test_receive_addresses.py .
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "test_receive_addresses.py"]
