CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
	DOCKER_REGISTRY_USER:=sdp-prototype
#  	DOCKER_REGISTRY_USER:=skaorca
endif

ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	DOCKER_REGISTRY_HOST:=nexus.engageska-portugal.pt
#	DOCKER_REGISTRY_HOST=index.docker.io
endif

IMAGE=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(NAME)
BASE_IMAGE:=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/pytango_ska_base:latest
DEV_IMAGE:=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/pytango_ska_dev:latest

ifeq ($(strip $(GIT_VERSION)),)
	GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
endif

DEFAULT_TAG=$(IMAGE):$(VERSION)-$(GIT_VERSION)

.DEFAULT_GOAL := help

piplock:  ## Rebuild the Pipfile.lock file
	-@pipenv --rm 2>/dev/null || true
	pipenv lock -v --clear --dev

CACHE_IMAGE:=$(shell docker image ls -q --filter=reference="$(IMAGE):latest")
ifeq ($(CACHE_IMAGE),)
	CACHE_FROM_ARG =
else
	CACHE_FROM_ARG = --cache-from $(IMAGE):latest
endif

build:  ## Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build \
	--pull \
	--build-arg DOCKER_REGISTRY_HOST=$(DOCKER_REGISTRY_HOST) \
	--build-arg DOCKER_REGISTRY_USER=$(DOCKER_REGISTRY_USER) \
	$(CACHE_FROM_ARG) \
	-t $(DEFAULT_TAG) .

push: ## Push default image (tagged as :$(VERSION)-(GIT_VERSION)
	@echo "$(CBLUE)Pushing:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	docker push $(DEFAULT_TAG)

tag_latest:
	@echo "$(CBLUE)Tagging:$(CEND) $(DEFAULT_TAG) $(CRED)->$(CEND) $(IMAGE):latest"
	@docker tag $(DEFAULT_TAG) $(IMAGE):latest

push_latest: tag_latest ## Push the image tagged as :latest
	@echo "$(CBLUE)Pushing:$(CEND) $(IMAGE):latest"
	@docker push $(IMAGE):latest

tag_version:
	@echo "$(CBLUE)Tagging:$(CEND) $(DEFAULT_TAG) $(CRED)->$(CEND) $(IMAGE):$(VERSION)"
	@docker tag $(DEFAULT_TAG) $(IMAGE):$(VERSION)

push_version: tag_version  ## Push the image tagged as :$(VERSION) (without the git sha)
	@echo "$(CBLUE)Pushing:$(CEND) $(IMAGE):$(VERSION)"
	@docker push $(IMAGE):$(VERSION)

pull: ## Fetch the latest image
	@echo "$(IMAGE)"
	@docker pull $(IMAGE):latest

pull_default: ## Fetch the default Git versioned image
	@docker pull $(DEFAULT_TAG) || true

ls:  ## List images built from this folder
	@echo "$(CBLUE)Images matching:$(CEND) $(IMAGE):*"
	@docker image ls --filter=reference="$(IMAGE):*"

rm:  ## Remove all images built from this folder
	@echo "$(CBLUE)Removing images matching:$(CEND) $(IMAGE):*"
	-@docker image rm $(shell docker image ls --filter=reference="$(IMAGE):*" --format '{{.Repository}}:{{.Tag}}') 2> /dev/null || true

help:  ## Show this help.
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)NAME        $(CEND): $(NAME)"
	@echo "$(CBLUE)IMAGE       $(CEND): $(IMAGE)"
	@echo "$(CBLUE)VERSION     $(CEND): $(VERSION)"
	@echo "$(CBLUE)GIT VERSION $(CEND): $(GIT_VERSION)"
	@echo "$(CBLUE)DEFAULT TAG $(CEND): $(DEFAULT_TAG)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "Imported targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ../make/Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo "Local targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build clean_build tag_version tag_latest tag
.PHONY: push pull refresh_pipenv info list_old list_all rm rm_old help
