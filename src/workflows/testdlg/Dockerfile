FROM python:3.7

RUN pip install ska_sdp_config
RUN pip install daliuge

WORKDIR /app
COPY daliuge ./daliuge
ENTRYPOINT ["python", "-m", "daliuge.main"]
