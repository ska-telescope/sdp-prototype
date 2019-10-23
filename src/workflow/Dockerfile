
FROM python:3.6

RUN pip install ska_sdp_config  distributed

COPY *.py ./
ENTRYPOINT [ "python", "switcher.py" ]
