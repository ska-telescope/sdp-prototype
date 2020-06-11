FROM python:3.7

COPY requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /app
COPY vis_receive.py ./
ENTRYPOINT ["python", "vis_receive.py"]
