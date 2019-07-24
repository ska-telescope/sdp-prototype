ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_ska_base:latest

WORKDIR /app
COPY . /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --ignore-pipfile --dev

ENTRYPOINT ["python", "SDPMaster"]
CMD ["1", "-v4"]
