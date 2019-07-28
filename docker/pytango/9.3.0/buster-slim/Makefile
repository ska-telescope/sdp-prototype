IMAGE_TAG=buster-slim
IMAGE_NAME=pytango-9.3.0

ifeq ($(strip $(GIT_VERSION)),)
	GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
endif

ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
  	DOCKER_REGISTRY_USER=skaorca
#	DOCKER_REGISTRY_USER=sdp-prototype
endif

#ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
#  	DOCKER_REGISTRY_HOST=index.docker.io
#	DOCKER_REGISTRY_HOST=nexus.engageska-portugal.pt
#endif


ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	IMAGE=$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)
else
	IMAGE=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)
endif

.DEFAULT_GOAL := help

.PHONY: build
build:  ## Build images
	# Build the buildenv stage.
	docker pull $(IMAGE):buildenv || true
	docker build --cache-from $(IMAGE):buildenv \
		--target=buildenv -t $(IMAGE):buildenv .

#	# Build the runtime (final) stage
#	docker pull $(REPO)/$(IMAGE):latest || true
#	docker build \
#		--cache-from $(REPO)/$(IMAGE):builder \
#		--cache-from $(REPO)/$(IMAGE):latest \
#		-t $(REPO)/$(IMAGE):latest \
#		-t $(REPO)/$(IMAGE):$(DOCKER_IMAGE_VERSION) \
#		.

ls:  ## List images built from this folder
	docker image ls --filter=reference="$(IMAGE):*"


.PHONY: help
help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
