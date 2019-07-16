CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
  DOCKER_REGISTRY_USER:=skaorca
endif

# Get image name and version from the release file
GIT_VERSION=$(shell git rev-parse --verify --short=8 HEAD)
ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	IMAGE=$(DOCKER_REGISTRY_USER)/$(NAME)
	DOCKER_REGISTRY_HOST=index.docker.io
else
	IMAGE=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(NAME)
endif
DEFAULT_TAG=$(IMAGE):$(VERSION)-$(GIT_VERSION)

.DEFAULT_GOAL := help

piplock:  ## Rebuild the Pipfile.lock file
	-@pipenv --rm 2>/dev/null || true
	pipenv lock -v --clear --dev

build:  ## Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build --pull $(DOCKER_BUILD_ARGS) \
	--build-arg DOCKER_REGISTRY_HOST=$(DOCKER_REGISTRY_HOST) \
	--build-arg DOCKER_REGISTRY_USER=$(DOCKER_REGISTRY_USER) \
	-t $(DEFAULT_TAG) .

tag_version:
	@echo "$(CBLUE)Tagging image:$(CEND) $(DEFAULT_TAG) $(CRED)->$(CEND) $(IMAGE):$(VERSION)"
	@docker tag $(DEFAULT_TAG) $(IMAGE):$(VERSION)

tag_latest:
	@echo "$(CBLUE)Tagging image:$(CEND) $(DEFAULT_TAG) $(CRED)->$(CEND) $(IMAGE):latest"
	@docker tag $(DEFAULT_TAG) $(IMAGE):latest

tag: tag_version tag_latest ## Tag images
	@echo "$(CBLUE)Tagging image:$(CEND) $(DEFAULT_TAG) $(CRED)->$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@docker tag $(DEFAULT_TAG) $(IMAGE):$(VERSION)-$(GIT_VERSION)

push: ## Push images
	@echo "$(CBLUE)Pushing image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	docker push $(IMAGE):$(VERSION)-$(GIT_VERSION)
	@echo "$(CBLUE)Pushing image:$(CEND) $(IMAGE):$(VERSION)"
	docker push $(IMAGE):$(VERSION)
	@echo "$(CBLUE)Pushing image:$(CEND) $(IMAGE):latest"
	docker push $(IMAGE):latest

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
