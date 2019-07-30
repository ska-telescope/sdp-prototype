ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango-9.3.0:buster-slim

WORKDIR /app
COPY /SDPSubarray /app/SDPSubarray

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --ignore-pipfile --dev

COPY wait-for-it.sh wait-for-it.sh

ENTRYPOINT ["python", "SDPSubarray"]
CMD ["1", "-v4"]
