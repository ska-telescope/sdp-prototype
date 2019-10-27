FROM python:3.7

RUN pip install ska_sdp_config
RUN pip install distributed

WORKDIR /app
COPY testdask.py .
ENTRYPOINT ["python", "testdask.py"]
