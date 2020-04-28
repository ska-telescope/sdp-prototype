FROM python:3.7

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY test_dask.py ./
ENTRYPOINT ["python", "test_dask.py"]
