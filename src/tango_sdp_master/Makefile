#
# Makefile for building and publishing the `tangods_sdp_master` image.
#

NAME=tangods_sdp_master
CLASS=SDPMaster
VERSION=0.2.0

include ../make/Makefile

.PHONY: register unregister

register:  ## register devices (usage: make register <number of devices>)
	@docker run --rm -t \
		-v $(PWD):/app \
		--entrypoint=python \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		$(BASE_IMAGE) \
		$(CLASS)/register.py

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
		--name=$(NAME) \
		--network=container:databaseds \
		-e TANGO_HOST=localhost:10000 \
		--entrypoint=python \
		$(IMAGE):latest \
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
		$(DEV_IMAGE) \
		python -m pytest \
		-vv \
		.

lint:  ## Run test and linter
	@docker run --rm -t \
		-v $(PWD):/app \
		$(DEV_IMAGE) \
		python -m pytest \
		--pylint \
		--pylint-rcfile=../../scripts/.pylintrc \
		--codestyle \
		--docstyle \
		-vv \
		.

test_shell:  ## Provide a test shell with the current code
	@docker run --rm -it \
		-v $(PWD):/app \
		--entrypoint=/bin/bash \
		$(DEV_IMAGE)
