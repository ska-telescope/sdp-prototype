FROM python:3.7

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY pss_receive.py ./
ENTRYPOINT ["python", "pss_receive.py"]
