FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest AS buildenv
FROM nexus.engageska-portugal.pt/ska-docker/ska-python-runtime:latest AS runtime
USER root 
#RUN apt-get upgrade && apt-get install bash
RUN pip3 install jsonschema
RUN pip3 install -U lmcbaseclasses==0.5.1 --extra-index-url https://nexus.engageska-portugal.pt/repository/pypi/simple
USER tango
ENTRYPOINT ["python", "SDPSubarray"]
CMD ["1", "-v4"]
