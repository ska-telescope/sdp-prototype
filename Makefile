
# If the first make argument is "test"
ifeq (test,$(firstword $(MAKECMDGOALS)))
  TEST_TARGET = true
endif
ifdef TEST_TARGET
  # .. then use the rest as arguments for the make target
  TEST_DIR := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TEST_DIR):;@:)
endif

.PHONY: test
test: ## Run test (usage make test <path>)
	docker run -t --rm \
		--entrypoint="" \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev:latest \
		python -m pytest \
        --gherkin-terminal-reporter \
        -vv \
        --cucumber-json=cucumber.json \
        $(TEST_DIR)

list:  ## List all ORCA images
	@docker image ls --filter=reference="skaorca/*:*"

list_ska: ## List all ska-docker images
	@docker image ls --filter=reference="*/ska-docker/*:*"
