#
# Makefile for building and publishing the `pytango_ska_dev` image.
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
NAME=$(shell awk -F= '/^name=/{print $$2}' release)
GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
VERSION=$(shell awk -F= '/^release=/{print $$2}' release)-$(GIT_VERSION)
IMAGE=$(DOCKER_REGISTRY_USER)/$(NAME)

IMAGES := $(shell docker images --format '{{.Repository}}:{{.Tag}}' | grep $(IMAGE))


.PHONY: all
all: build

.PHONY: build
build: build_version tag_latest

.PHONY: build_version
build_version:
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

.PHONY: clean
clean:
ifeq ($(strip $(IMAGES)),)
	@echo "$(CRED)No images need removing!$(CEND)"
else
	docker image rm $(IMAGES)
endif


