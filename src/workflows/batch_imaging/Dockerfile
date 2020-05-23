FROM timcornwell/rascil-full

WORKDIR /rascil

RUN git clone https://gitlab.mpcdf.mpg.de/ift/nifty_gridder.git
RUN pip3 install ./nifty_gridder --user .

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY batch_imaging.py rascil_workflows.py ./
ENTRYPOINT ["python3", "batch_imaging.py"]
