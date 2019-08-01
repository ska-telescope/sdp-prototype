
FROM skaorca/pytango_ska_dev:latest

RUN pipenv install

COPY . config_db
RUN (cd config_db; pipenv install .)

