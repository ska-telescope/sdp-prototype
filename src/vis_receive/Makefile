#
# Makefile for building and publishing the `sdp_vis_receive` image.
#

# ----------------------------------------------------------------------------
# Variables
# ----------------------------------------------------------------------------
IMAGE_NAME:=vis-receive
VERSION:=$(shell awk -F= '/.*/{print $$1}' VERSION)
IMAGE:=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)

# ----------------------------------------------------------------------------
# Docker helper targets
# ----------------------------------------------------------------------------

.PHONY: build
build:  ## Build the docker image
	docker pull $(IMAGE):buildenv || true
	docker build --pull --cache-from $(IMAGE):buildenv --target buildenv \
		-t $(IMAGE):buildenv .

	docker pull $(IMAGE):latest || true
	docker build --cache-from $(IMAGE):latest --cache-from $(IMAGE):buildenv \
		-t $(IMAGE):latest .

.PHONY: ls
ls:  ## List docker images
	docker image ls --filter=reference="$(IMAGE)"

# ----------------------------------------------------------------------------
# Help target
# ----------------------------------------------------------------------------


.DEFAULT_GOAL := help
.PHONY: help
help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
