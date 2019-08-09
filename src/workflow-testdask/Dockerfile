
ARG BASE=ska-sdp-config:latest
FROM $BASE

RUN pipenv install distributed

COPY testdask.py .
CMD pipenv run python testdask.py
