FROM python:3.7

RUN pip install ska_sdp_config

WORKDIR /app
COPY test_receive_addresses.py .
ENTRYPOINT ["python", "test_receive_addresses.py"]
