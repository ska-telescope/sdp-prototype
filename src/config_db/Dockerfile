
FROM skaorca/pytango_ska_dev:latest

COPY . config_db
RUN pipenv install -r config_db/requirements.txt config_db && rm -rf config_db
