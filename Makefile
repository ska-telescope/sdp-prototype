
# If the first make argument is "test"
ifeq (test,$(firstword $(MAKECMDGOALS)))
  TEST_TARGET = true
endif
ifeq (test_script,$(firstword $(MAKECMDGOALS)))
  TEST_TARGET = true
endif

ifdef TEST_TARGET
  # .. then use the rest as arguments for the make target
  TEST_DIR := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TEST_DIR):;@:)
endif

.DEFAULT_GOAL := help

test: ## Run test (usage: make test <path>)
	docker run -t --rm \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev:latest \
		python -m pytest \
        --gherkin-terminal-reporter \
        -vv \
        --cucumber-json=cucumber.json \
        $(TEST_DIR)

test_script:  ## Run tests using ./scripts/run_test.sh (usage: make test_script <path)
	@docker run -t --rm \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev:latest \
		./scripts/run_test.sh \
		$(TEST_DIR)

test_script_bdd:  ## Run BDD tests using ./scripts/run_test.sh (usage: make test_script_bdd <path)
	@docker run -t --rm \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev:latest \
		./scripts/run_test.sh \
		$(TEST_DIR) \
		--gherkin-terminal-reporter \
		--cucumber-json=cucumber.json

test_shell:  ## Start a test shell using the `skaorca/pytango_ska_dev` container
	@docker run -it --rm \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev:latest

list:  ## List all ORCA images
	@docker image ls --filter=reference="skaorca/*:*"

list_ska: ## List all ska-docker images
	@docker image ls --filter=reference="*/ska-docker/*:*"


help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: test test_shell run_test_script list list_ska
.PHONY: help
