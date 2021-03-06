#
# Makefile utility functions for the SDP Master Tango device
#

NAME=tangods_sdp_master
CLASS=SDPMaster
VERSION=$(patsubst "%",%, $(shell awk -F= '/^VERSION = ".*"/{print $$2}' $(CLASS)/release.py))

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
		$(BASE_IMAGE) \
		$(CLASS)/register.py $(NUM_DEVICES)

unregister:  ## Unregister devices
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		$(BASE_IMAGE) \
		$(CLASS)/register.py --delete

.PHONY: start_dev start stop

start_dev:  ## Start the device from the current code
	@docker run \
		--rm -t \
		-v $(PWD):/app \
		--name=$(NAME)_dev \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		$(IMAGE):latest \
		$(CLASS) 1 -v4

start_shell:  ## Start the device from the current code
	@docker run \
		--rm -it \
		-v $(PWD):/app \
		--name=$(NAME)_shell \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=/bin/bash \
		$(IMAGE):latest

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
		$(DEV_IMAGE) \
		python -m pytest \
		--pylint \
		--codestyle \
		--docstyle \
		--cov=SDPMaster \
	    --cov-report=term \
    	--cov-config=./setup.cfg \
		-vv \
		--gherkin-terminal-reporter \
		.

test_shell:  ## Provide a test shell with the current code
	@docker run --rm -it \
		-v $(PWD):/app \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=/bin/bash \
		$(DEV_IMAGE)

dev_shell:  ## Provide a development shell with the current code
	@docker run --rm -it \
		-v $(PWD):/app \
		$(DEV_IMAGE)

build_package:  ## Build the python package
	@python setup.py sdist bdist_wheel
