ARG BASE=ska-sdp-config:latest
FROM $BASE

RUN pipenv install distributed

COPY test_vis_receive.py .
CMD pipenv run python test_vis_receive.py
