#
#  Makefile utility functions for the SDP Subarray Tango device
#

# ----------------------------------------------------------------------------
# Variables
# ----------------------------------------------------------------------------
PACKAGE_NAME:=$(patsubst "%",%, $(shell awk -F= '/^PACKAGE_NAME = ".*"/{print $$2}' SDPSubarray/release.py))
IMAGE_NAME:=$(patsubst "%",%, $(shell awk -F= '/^IMAGE_NAME = ".*"/{print $$2}' SDPSubarray/release.py))
VERSION:=$(patsubst "%",%, $(shell awk -F= '/^VERSION = ".*"/{print $$2}' SDPSubarray/release.py))
IMAGE_ROOT:=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)
IMAGE:=$(IMAGE_ROOT):$(VERSION)-buster-slim

# Image used for running tests.
DEV_IMAGE=nexus.engageska-portugal.pt/sdp-prototype/pytango-orca-dev:0.3.0-buster-slim


# ----------------------------------------------------------------------------
# Test targets
# ----------------------------------------------------------------------------

TEST_COMMAND=\
python3 -m pytest -vv \
	--pylint \
	--codestyle \
	--docstyle \
	--cov=SDPSubarray \
	--no-cov-on-fail \
	--cov-config=./setup.cfg \
	--cov-branch \
	--cov-report=term \
	--gherkin-terminal-reporter


.PHONY: test
test:  ## Run tests locally
	$(TEST_COMMAND)


.PHONY: test-in-dev-image
test-in-dev-image:  ## Run tests inside the a Docker development image.
	docker run --rm -t -v $(PWD):/app $(DEV_IMAGE) $(TEST_COMMAND)


# ----------------------------------------------------------------------------
# Docker helper targets
# ----------------------------------------------------------------------------


.PHONY: docker-build-test-image
docker-build-test-image:  ## Build a test image
	docker pull $(IMAGE)-test || true
	docker build --pull \
		--cache-from $(IMAGE)-test \
		--build-arg DOCKER_REGISTRY_HOST=$(DOCKER_REGISTRY_HOST) \
		--build-arg DOCKER_REGISTRY_USER=$(DOCKER_REGISTRY_USER) \
		-t $(IMAGE)-test .


.PHONY: docker-tag-release
docker-tag-release:  ## Tag the release version from the -test image.
	docker tag $(IMAGE)-test $(IMAGE)


.PHONY: docker-tag-latest
docker-tag-latest:  ## Tag the latest version from the -test image
	docker tag $(IMAGE)-test $(IMAGE_ROOT):latest


.PHONY: docker-push-test-image
docker-push-test-image:  ## Push the test version of the image
	docker push $(IMAGE)-test


.PHONY: docker-push-release-image
docker-push-release-image:  ## Push the release version of the image
	docker push $(IMAGE)


.PHONY: docker-push-latest-image
docker-push-latest-image:  ## Push the latest version of the image
	docker push $(IMAGE_ROOT):latest


.PHONY: docker-ls
docker-ls:  ## List images
	docker image ls --filter=reference="$(IMAGE_ROOT):*"


.PHONY: docker-rm
docker-rm:  ## Remove images
	docker image rm $(shell docker image ls --filter=reference="$(IMAGE_ROOT):*" --format '{{.Repository}}:{{.Tag}}')


# ----------------------------------------------------------------------------
# Python package helper targets
# ----------------------------------------------------------------------------


.PHONY: python-test-package
python-test-package:  ## Test the python package
	python3 setup.py test


.PHONY: python-test-package-in-dev-image
python-test-package-in-dev-image:  ## Test the python package inside a dev container
	docker run --rm -t -v $(PWD):/app $(DEV_IMAGE) python3 setup.py test


.PHONY: python-build
python-build:  ## Build the python package
	python3 setup.py sdist bdist_wheel


# ----------------------------------------------------------------------------
# Help target
# ----------------------------------------------------------------------------


.DEFAULT_GOAL := help
.PHONY: help
help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
