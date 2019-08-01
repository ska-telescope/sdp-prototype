
ARG BASE=skaorca/pytango_ska_dev:latest
FROM $BASE

RUN pipenv install kubernetes

COPY dummy_workflow.py .
CMD python dummy_workflow.py
