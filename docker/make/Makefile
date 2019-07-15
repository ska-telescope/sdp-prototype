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
VERSION=$(shell awk -F= '/^release=/{print $$2}' release)
IMAGE=$(DOCKER_REGISTRY_USER)/$(NAME)

.DEFAULT_GOAL := help

build:  ## Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build --pull $(DOCKER_BUILD_ARGS) -t ${IMAGE}:${VERSION}-$(GIT_VERSION) .

clean_build: refresh_pipenv build ## Refresh the Pipfile and build the image

SOURCE:=$(IMAGE):$(VERSION)-$(GIT_VERSION)
ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	TARGET=$(IMAGE)
else
	TARGET=$(DOCKER_REGISTRY_HOST)/$(IMAGE)
endif

tag_version:
	@echo "$(CBLUE)Tagging image:$(CEND) $(SOURCE) $(CRED)->$(CEND) $(TARGET):$(VERSION)"
	@docker tag $(SOURCE) $(TARGET):$(VERSION)

tag_latest:
	@echo "$(CBLUE)Tagging image:$(CEND) $(SOURCE) $(CRED)->$(CEND) $(TARGET):latest"
	@docker tag $(SOURCE) $(TARGET):latest

tag: tag_version tag_latest
	@echo "$(CBLUE)Tagging image:$(CEND) $(SOURCE) $(CRED)->$(CEND) $(TARGET):$(VERSION)-$(GIT_VERSION)"
	@docker tag $(SOURCE) $(TARGET):$(VERSION)-$(GIT_VERSION)

push: tag  ## Push images
ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	@echo "$(CBLUE)Pushing images to Dockerhub ...$(CEND)"
else
	@echo "$(CBLUE)Pushing images to $(DOCKER_REGISTRY_HOST) ...$(CEND)"
endif
	docker push $(TARGET):$(VERSION)-$(GIT_VERSION)
	docker push $(TARGET):$(VERSION)
	docker push $(TARGET):latest


pull: ## Pull the latest image version
	@docker pull $(IMAGE):latest

refresh_pipenv:
	-@pipenv --rm 2>/dev/null || true
	pipenv lock -v --clear --dev

ls:  ## List images built from this folder
	@echo "$(CBLUE)Local & Dockerhub images:$(CEND)"
	@docker image ls --filter=reference="$(IMAGE):*"
	@echo ""
	@echo "$(CBLUE)SKA Nexus images:$(CEND)"
	@docker image ls --filter=reference="*/$(IMAGE):*"

rm:  ## Remove all images built from this folder
	-@docker image rm $(shell docker image ls --filter=reference="$(IMAGE):*" --format '{{.Repository}}:{{.Tag}}') 2> /dev/null || true
	-@docker image rm $(shell docker image ls -q --filter=reference="*/$(IMAGE):*" --format '{{.Repository}}:{{.Tag}}') 2> /dev/null || true

help:  ## Show this help.
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)NAME        $(CEND): $(NAME)"
	@echo "$(CBLUE)IMAGE       $(CEND): $(IMAGE)"
	@echo "$(CBLUE)VERSION     $(CEND): $(VERSION)"
	@echo "$(CBLUE)GIT VERSION $(CEND): $(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Targets:$(CEND)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ../make/Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build clean_build tag_version tag_latest tag
.PHONY: push pull refresh_pipenv info list_old list_all rm rm_old help
