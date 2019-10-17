FROM ska-sdp-config

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*


RUN pip install ska_sdp_config
## Copy the Pipfile
#COPY Pipfile Pipfile
#COPY Pipfile.lock Pipfile.lock
#
## Install Python deps
#RUN pipenv install --deploy --ignore-pipfile --dev

COPY switcher.py .
COPY test_vis_receive.py .
COPY testdask.py .
COPY testdeploy.py .
ENTRYPOINT python switcher.py
