FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest AS buildenv
FROM nexus.engageska-portugal.pt/ska-docker/ska-python-runtime:latest AS runtime

USER root
RUN pip install .

USER tango
ENTRYPOINT ["python", "SDPMaster"]
CMD ["1", "-v4"]
