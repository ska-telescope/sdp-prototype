FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest AS buildenv
FROM nexus.engageska-portugal.pt/ska-docker/ska-python-runtime:latest AS runtime

USER root
RUN pip install -r requirements1.txt
RUN pip install -r requirements2.txt

USER tango
ENTRYPOINT ["python", "SDPSubarray"]
CMD ["1", "-v4"]
