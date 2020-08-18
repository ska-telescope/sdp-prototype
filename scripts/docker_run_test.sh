#/bin/sh

# Run a Docker container for testing code. It connects to the etcd instance
# created by docker_run_etcd.sh.

echo
echo Starting test container. The local directory will be mounted in the
echo container.
echo
echo First install the dependencies, e.g.:
echo  $ pip install -r requirements.txt -r requirements-test.txt
echo
echo Then run the tests, e.g.:
echo  $ python3 setup.py test
echo
echo If you get an error message about the etcd container below, you need to
echo start it first with docker_run_etcd.sh.
echo

docker run -it -v $(PWD):/app --rm --link etcd \
    --env SDP_CONFIG_HOST=etcd --env SDP_TEST_HOST=etcd \
    nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest
