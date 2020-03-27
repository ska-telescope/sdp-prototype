FROM python:3.7

RUN pip install ska_sdp_config>=0.0.7

WORKDIR /app
COPY test_realtime.py .
ENTRYPOINT ["python", "test_realtime.py"]
