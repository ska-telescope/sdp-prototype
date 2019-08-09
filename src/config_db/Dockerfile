
FROM python:3.6

RUN pip install pipenv

COPY . config_db
COPY Pipfile .
RUN pipenv install config_db
