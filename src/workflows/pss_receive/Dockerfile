FROM python:3.7

RUN pip install ska_sdp_config

WORKDIR /app
COPY pss_receive.py .
ENTRYPOINT ["python", "pss_receive.py"]
