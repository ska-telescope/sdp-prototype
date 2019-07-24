#
# Makefile providing some simple helper functions
#

CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
	DOCKER_REGISTRY_USER=sdp-prototype
#  	DOCKER_REGISTRY_USER:=skaorca
endif

ifeq ($(strip $(DOCKER_REGISTRY_HOST)),)
	DOCKER_REGISTRY_HOST=nexus.engageska-portugal.pt
#	DOCKER_REGISTRY_HOST=index.docker.io
endif

# If the first make argument is "test"
ifeq (test,$(firstword $(MAKECMDGOALS)))
  TEST_TARGET = true
endif
ifeq (test_only,$(firstword $(MAKECMDGOALS)))
  TEST_TARGET = true
endif

ifdef TEST_TARGET
  # .. then use the rest as arguments for the make target
  TEST_DIR := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TEST_DIR):;@:)
endif

IMAGE_PREFIX := $(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)
DEV_IMAGE = $(IMAGE_PREFIX)/pytango_ska_dev:latest

.DEFAULT_GOAL := help

.PHONY: test
test:  ## Run tests and linter (usage: make test <path)
	@docker run -t --rm \
		-v $(PWD):/app \
		$(DEV_IMAGE) \
		./scripts/run_test.sh \
		$(TEST_DIR) \
		--gherkin-terminal-reporter

.PHONY: test_only
test_only:  ## Run tests (usage: make test_only <path)
	@docker run -t --rm \
		-v $(PWD):/app \
		$(DEV_IMAGE) \
		./scripts/run_test.sh \
		$(TEST_DIR) \
		--test-only \
		--gherkin-terminal-reporter

.PHONY: shell
shell:  ## Start a shell inside a `pytango_ska_dev` container
	@docker run -it --rm \
		-v $(PWD):/app \
		$(DEV_IMAGE)

.PHONY: ls
ls:  ## List all ORCA images
	@docker image ls --filter=reference="$(IMAGE_PREFIX)/*:*"
	@docker image ls --filter=reference="skaorca/*:*"

.PHONY: rm
rm : ## Remove all ORCA images
	@echo "$(CBLUE)Removing images matching:$(CEND) $(IMAGE_PREFIX)/*:*"
	-@docker image rm -f $(shell docker image ls -q --filter=reference="$(IMAGE_PREFIX)/*:*")
#	@echo "$(CBLUE)Removing images matching:$(CEND) skaorca/*:*"
#	-@docker image rm -f $(shell docker image ls -q --filter=reference="skaorca/*:*")

.PHONY: help
help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | \
		awk 'BEGIN {FS = ":.*?## "}; \
		{printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
