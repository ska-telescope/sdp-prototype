ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango9.3.0:buster-slim

WORKDIR /app
COPY SDPSubarray /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --ignore-pipfile --dev

ENTRYPOINT ["python", "SDPSubarray"]
CMD ["1", "-v4"]
