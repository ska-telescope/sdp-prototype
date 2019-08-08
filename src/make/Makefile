CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
	DOCKER_REGISTRY_USER=sdp-prototype
#  	DOCKER_REGISTRY_USER=skaorca
endif

ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	DOCKER_REGISTRY_HOST=nexus.engageska-portugal.pt
#	DOCKER_REGISTRY_HOST=index.docker.io
endif

ifeq ($(DOCKER_REGISTRY_HOST),index.docker.io)
	IMAGE:=$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)
else
	IMAGE:=$(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(IMAGE_NAME)
endif

DEFAULT_TAG=$(IMAGE):$(VERSION)

.DEFAULT_GOAL := help


# -----------------------------------------------------------------------------
# Docker Image targets
# -----------------------------------------------------------------------------

.PHONY: build-image
build-image:  ## Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Building image:$(CEND) $(IMAGE):$(VERSION)-$(GIT_VERSION)"
	@echo "$(CRED)$(LINE)$(CEND)"
	docker build \
	--pull \
	--build-arg DOCKER_REGISTRY_HOST=$(DOCKER_REGISTRY_HOST) \
	--build-arg DOCKER_REGISTRY_USER=$(DOCKER_REGISTRY_USER) \
	$(CACHE_FROM_ARG) \
	-t $(DEFAULT_TAG) .

.PHONY: push
push: ## Push default image (tagged as :$(VERSION)-(GIT_VERSION)
	docker push $(DEFAULT_TAG)

.PHONY: tag-latest
tag-latest:
	docker tag $(DEFAULT_TAG) $(IMAGE):latest

.PHONY: push-latest
push_latest: tag-latest ## Push the image tagged as :latest
	docker push $(IMAGE):latest

.PHONY: tag-version
tag-version:
	docker tag $(DEFAULT_TAG) $(IMAGE):$(VERSION)

.PHONY: pull-latest
pull-latest: ## Fetch the latest image
	docker pull $(IMAGE):latest

.PHONY: ls
ls:  ## List images built from this folder
	docker image ls --filter=reference="$(IMAGE):*"

.PHONY: rm
rm:  ## Remove all images built from this folder
	docker image rm $(shell docker image ls --filter=reference="$(IMAGE):*" --format '{{.Repository}}:{{.Tag}}')


# -----------------------------------------------------------------------------
# Python Package targets
# -----------------------------------------------------------------------------

.PHONY: build-package
build-package:  ## Build the python package.
	python3 setup.py sdist bdist_wheel

.PHONY: test-package
test-package:  ## Test the python package
	python3 setup.py test



# -----------------------------------------------------------------------------
# Utility targets
# -----------------------------------------------------------------------------

.PHONY: piplock
piplock:  ## Rebuild the Pipfile.lock file
	-@pipenv --rm 2>/dev/null || true
	pipenv lock -v --clear --dev


.PHONY: help
help:  ## Show this help.
	@echo "Imported targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ../make/Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo "Local targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

