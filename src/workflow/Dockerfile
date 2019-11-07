
FROM python:3.6

RUN pip install ska_sdp_config distributed daliuge

COPY *.py ./
COPY daliuge ./daliuge

ENTRYPOINT [ "python", "switcher.py" ]
