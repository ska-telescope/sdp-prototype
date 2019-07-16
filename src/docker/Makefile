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
IMAGES := $(shell docker image ls --format '{{.Repository}}:{{.Tag}}' --filter=reference="$(IMAGE)*:*")


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

tag: tag_version tag_latest  ## Tag current image as :latest and :$(VERISON)

push: tag  ## Push images (to dockerhub)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Pushing images to Dockerhub ...$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker push $(IMAGE):$(VERSION)-$(GIT_VERSION)
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

pull: ## Pull the latest image version
	@docker pull $(IMAGE):latest

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

list_all:  ## List skaorca/pytango_* images
	@docker image ls --filter=reference="skaorca/pytango_*:*"

list:  ## List images built from this folder
	@docker image ls --filter=reference="$(IMAGE):*"

list_old:  ## List old images build from this folder
	@echo "$(OLD_IMAGES)"

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

help:  ## Show this help.
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)NAME        $(CEND): $(NAME)"
	@echo "$(CBLUE)IMAGE       $(CEND): $(IMAGE)"
	@echo "$(CBLUE)VERSION     $(CEND): $(VERSION)"
	@echo "$(CBLUE)GIT VERSION $(CEND): $(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Targets:$(CEND)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ../Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: build clean_build tag_version tag_latest tag
.PHONY: push pull refresh_pipenv info list_old list_all rm rm_old help
