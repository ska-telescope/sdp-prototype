#
# Makefile for building and publishing the `tangods_sdp_subarray` image.
#

CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
  DOCKER_REGISTRY_USER = skaorca
endif

# Get image name and version from the release file
NAME=tangods_sdp_subarray
VERSION=0.2.0
GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
IMAGE=$(DOCKER_REGISTRY_USER)/$(NAME)
IMAGES := $(shell docker image ls --format '{{.Repository}}:{{.Tag}}' --filter=reference="$(IMAGE)*:*")


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

.DEFAULT_GOAL := help


build:  ## Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build -t ${IMAGE}:${VERSION}-$(GIT_VERSION) .

clean_build: refresh_pipenv build ## Refresh the Pipfile and build the image

tag_version:
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Tagging image:$(CEND) ${IMAGE}:${VERSION}-$(GIT_VERSION) -> $(IMAGE):$(VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker tag ${IMAGE}:${VERSION}-$(GIT_VERSION) ${IMAGE}:${VERSION}

tag_latest:
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Tagging image:$(CEND) ${IMAGE}:${VERSION}-$(GIT_VERSION) -> $(IMAGE):latest"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker tag ${IMAGE}:${VERSION}-$(GIT_VERSION) $(IMAGE):latest

tag: tag_version tag_latest  ## Create image tags :latest, :$(VERSION)

push: tag  ## Push images (to dockerhub)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Pushing images to Dockerhub ...$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker push $(IMAGE):$(VERSION)-$(GIT_VERSION)
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

refresh_pipenv:
	-@pipenv --rm 2>/dev/null || true
	pipenv lock -v --clear --dev

OLD_IMAGES = $(IMAGES)
OLD_IMAGES := $(filter-out $(IMAGE):latest, $(OLD_IMAGES))
OLD_IMAGES := $(filter-out $(IMAGE):$(VERSION), $(OLD_IMAGES))
OLD_IMAGES := $(filter-out $(IMAGE):$(VERSION)-$(GIT_VERSION), $(OLD_IMAGES))

info: ## Print information on images
	@echo "NAME = $(NAME)"
	@echo "IMAGE = $(IMAGE)"
	@echo "VERSION = $(VERSION)"
	@echo "GIT_VERSION = $(GIT_VERSION)"
	@echo "IMAGES = $(IMAGES)"
	@echo "OLD_IMAGES =$(OLD_IMAGES)"

list:  ## List images built from this folder
	@docker image ls --filter=reference="$(IMAGE):*"

rm:  ## Remove all images built from this folder
ifeq ($(strip $(IMAGES)),)
	@echo "$(CRED)No images to remove!$(CEND)"
else
	docker image rm $(IMAGES)
endif

rm_old:  ## Remove old images built from this folder
ifeq ($(strip $(OLD_IMAGES)),)
	@echo "$(CRED)No images to remove!$(CEND)"
else
	docker image rm $(OLD_IMAGES)
endif

register:  ## register devices (usage: make register <number of devices>)
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		SDPSubarray/register.py $(NUM_DEVICES)

unregister:  ## Unregister devices
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		SDPSubarray/register.py --delete

start_dev:  ## Start the device from the current code
	@docker run \
		--rm -t \
		-v $(PWD):/app \
		--name=sdpsubarray \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		skaorca/pytango_ska_base:latest \
		SDPSubarray 1 -v4

start:  ## Start the device from the current Docker image
	@docker run \
		--rm -t \
		--name=sdpsubarray \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		skaorca/tangods_sdp_subarray:latest \
		SDPSubarray 1 -v4


stop:  ## Stop the device
	@docker stop sdpsubarray


test:  ## Run tests for the device
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		skaorca/pytango_ska_dev \
		-m pytest \
		-vv \
		--cucumber-json=cucumber.json \
		--gherkin-terminal-reporter

ci_test: # Test command run by the CI
	python -m pytest \
		-vv \
		--gherkin-terminal-reporter \
		--cucumber-json=cucumber.json \
		.

test_shell:  ## Provide a test shell with the current code
	@docker run --rm -it \
		-v $(PWD):/app \
		--entrypoint=/bin/bash \
		skaorca/pytango_ska_dev

help:  ## Show this help.
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)NAME        $(CEND): $(NAME)"
	@echo "$(CBLUE)IMAGE       $(CEND): $(IMAGE)"
	@echo "$(CBLUE)VERSION     $(CEND): $(VERSION)"
	@echo "$(CBLUE)GIT VERSION $(CEND): $(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Targets:$(CEND)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build clean_build tag_version tag_latest tag refresh_pipenv
.PHONY: info rm rm_old register unregister start_dev start stop
.PHONY: test ci_test test_shell help
