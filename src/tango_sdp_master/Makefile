#
# Makefile for building and publishing the `tangods_sdpmaster` image.
#
# Targets:
# 	build: Build the image. Creates two tags, :<current version> and :<latest>
# 	publish: Build and publish the image to Dockerhub / cloud.docker.com
#	clean: Remove the image from the local machine

CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
  DOCKER_REGISTRY_USER = skaorca
endif

# Get image name and version from the release file
NAME=tangods_sdp_master
GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
VERSION=0.1.0-$(GIT_VERSION)
IMAGE=$(DOCKER_REGISTRY_USER)/$(NAME)
IMAGES := $(shell docker images --format '{{.Repository}}:{{.Tag}}' | grep $(IMAGE))

# If the first make argument is "register"
ifeq (register,$(firstword $(MAKECMDGOALS)))
  REGISTER_TARGET = true
endif
ifdef REGISTER_TARGET
  # .. then use the rest as arguments for the make target
  NUM_DEVICES := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(NUM_DEVICES):;@:)
endif


.PHONY: all
all: build

.PHONY: build
build: build_version tag_latest

.PHONY: build_version
build_version:
	@echo "GIT $(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building Docker image:$(CEND) $(IMAGE):$(VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build -t ${IMAGE}:${VERSION} .

.PHONY: tag_latest
tag_latest:
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Tagging image:$(CEND) $(IMAGE):latest"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker tag $(IMAGE):$(VERSION) $(IMAGE):latest

.PHONY: publish
publish: build tag_latest
	@echo "$(CRED)* $(CBLUE)Publishing image(s) to Dockerhub ...$(CEND)"
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

.PHONY: register
register:  ## register devices (usage: make register)
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		SDPMaster/register.py

.PHONY: unregister
unregister:
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		SDPSubarray/register.py --delete

.PHONY: start_dev
start_dev:
	@docker run \
		--rm -t \
		-v $(PWD):/app \
		--name=sdpmaster \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		skaorca/pytango_ska_base:latest \
		SDPMaster 1 -v4

.PHONY: start
start:
	@docker run \
		--rm -t \
		--name=sdpmaster \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		skaorca/tangods_sdp_master:latest \
		SDPMaster 1 -v4


.PHONY: stop
stop:
	@docker stop sdpmaster

.PHONY: test
test:
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		skaorca/pytango_ska_dev \
		-m pytest -vv -s

.PHONY: test_prompt
test_prompt:
	@docker run --rm -it \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev


.PHONY: clean
clean:
ifeq ($(strip $(IMAGES)),)
	@echo "$(CRED)No images need removing!$(CEND)"
else
	docker image rm $(IMAGES)
endif

