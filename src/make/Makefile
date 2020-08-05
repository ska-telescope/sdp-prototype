CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

.DEFAULT_GOAL := help

# Git hash

GIT_VERSION ?= $(shell git rev-parse --verify --short=8 HEAD)

# Docker registries for building and releasing the image. A different registry
# can be used to build the image to avoid pushing development versions to the
# release registry.

PREFIX_BUILD ?= registry.gitlab.com/ska-telescope/sdp-prototype
PREFIX_RELEASE ?= nexus.engageska-portugal.pt/sdp-prototype

# Image name with prefixes

NAME_BUILD := $(PREFIX_BUILD)/$(NAME)
NAME_RELEASE := $(PREFIX_RELEASE)/$(NAME)

# Image name with tags:
#
# - build: in the build registry, tagged with the version and git hash
# - release: in the release registry, tagged with the version
# - latest: in the release registry, tagged with 'latest'

TAG_BUILD := $(NAME_BUILD):$(VERSION)-$(GIT_VERSION)
TAG_RELEASE := $(NAME_RELEASE):$(VERSION)
TAG_LATEST := $(NAME_RELEASE):latest

build: ## Make the build image
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(TAG_BUILD)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build --pull -t $(TAG_BUILD) .

push: ## Push build image
	@echo "$(CBLUE)Pushing:$(CEND) $(TAG_BUILD)"
	docker push $(TAG_BUILD)

pull: ## Pull the build image
	docker pull $(TAG_BUILD) || true

tag_release: ## Tag the build image as the release image
	@echo "$(CBLUE)Tagging:$(CEND) $(TAG_BUILD) $(CRED)->$(CEND) $(TAG_RELEASE)"
	docker tag $(TAG_BUILD) $(TAG_RELEASE)

push_release: tag_release ## Push the release image
	@echo "$(CBLUE)Pushing:$(CEND) $(TAG_RELEASE)"
	docker push $(TAG_RELEASE)

tag_latest: ## Tag the build image as the latest image
	@echo "$(CBLUE)Tagging:$(CEND) $(TAG_BUILD) $(CRED)->$(CEND) $(TAG_LATEST)"
	docker tag $(TAG_BUILD) $(TAG_LATEST)

push_latest: tag_latest ## Push the latest image
	@echo "$(CBLUE)Pushing:$(CEND) $(LATEST)"
	docker push $(TAG_LATEST)

rm:  ## Remove all images built from this folder
	@echo "$(CBLUE)Removing images matching:$(CEND)"
	@echo "$(NAME_BUILD):*"
	@echo "$(NAME_RELEASE):*"
	-@docker image rm $(shell docker image ls --filter=reference="$(NAME_BUILD):*" --format '{{.Repository}}:{{.Tag}}') 2> /dev/null || true
	-@docker image rm $(shell docker image ls --filter=reference="$(NAME_RELEASE):*" --format '{{.Repository}}:{{.Tag}}') 2> /dev/null || true

help:  ## Show this help
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)NAME         $(CEND): $(NAME)"
	@echo "$(CBLUE)VERSION      $(CEND): $(VERSION)"
	@echo "$(CBLUE)GIT VERSION  $(CEND): $(GIT_VERSION)"
	@echo "$(CBLUE)BUILD IMAGE  $(CEND): $(TAG_BUILD)"
	@echo "$(CBLUE)RELEASE IMAGE$(CEND): $(TAG_RELEASE)"
	@echo "$(CBLUE)LATEST IMAGE $(CEND): $(TAG_LATEST)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "Imported targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ../make/Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo "Local targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build push pull tag_release push_release tag_latest push_latest rm help
