#
# Makefile for building and publishing the `tangods_sdp_subarray` image.
#

NAME=tangods_sdp_subarray
CLASS=SDPSubarray
VERSION=0.2.0

include ../make/Makefile

# If the first make argument is "register"
ifeq (register,$(firstword $(MAKECMDGOALS)))
  REGISTER_TARGET = true
endif
ifdef REGISTER_TARGET
  # .. then use the rest as arguments for the make target
  NUM_DEVICES := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(NUM_DEVICES):;@:)
endif

.PHONY: register unregister

register:  ## register devices (usage: make register <number of devices>)
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		$(CLASS)/register.py $(NUM_DEVICES)

unregister:  ## Unregister devices
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		skaorca/pytango_ska_base:latest \
		$(CLASS)/register.py --delete

.PHONY: start_dev start stop

start_dev:  ## Start the device from the current code
	@docker run \
		--rm -t \
		-v $(PWD):/app \
		--name=$(NAME) \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		skaorca/pytango_ska_base:latest \
		$(CLASS) 1 -v4

start:  ## Start the device from the current Docker image
	@docker run \
		--rm -t \
		--name=$(NAME) \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		-d \
		$(IMAGE):latest \
		$(CLASS) 1 -v4

stop:  ## Stop the device
	@docker stop $(NAME)

.PHONY: test lint ci_test test_shell

test:  ## Run tests for the device
	@docker run --rm -t \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev \
		python -m pytest \
		-vv \
		--gherkin-terminal-reporter \
		.

lint:  ## Run test and linter
	@docker run --rm -t \
		-v $(PWD):/app \
		skaorca/pytango_ska_dev \
		python -m pytest \
		--pylint \
		--pylint-rcfile=../../scripts/.pylintrc \
		--codestyle \
		--docstyle \
		-vv \
		--gherkin-terminal-reporter \
		.

test_shell:  ## Provide a test shell with the current code
	@docker run --rm -it \
		-v $(PWD):/app \
		--entrypoint=/bin/bash \
		skaorca/pytango_ska_dev
