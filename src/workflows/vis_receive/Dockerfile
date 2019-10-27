FROM python:3.7

RUN pip install ska_sdp_config

WORKDIR /app
COPY vis_receive.py .
ENTRYPOINT ["python", "vis_receive.py"]
