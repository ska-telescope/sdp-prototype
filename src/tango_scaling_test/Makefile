#
# Makefile for building and running Tango scaling tests.
#
# Targets:
# 	prompt: Obtain a bash prompt into a ubuntu container with Tango
#           developent libraries installed. This container has access to the
#           code by bind mounting the local directory into the container,
#           and expects to connect to a Tango database container (which can be
#           started using the provided docker-compose file.
#	itango: Obtain an iTagno prompt connected to a Tango database container
#           that can be used as an interactive way of testing tango devices.
#           As with the 'prompt' target, this assumes that a Tango database
#           container has been started.
#

CRED=\033[0;31m
CBLUE=\033[0;34m
CEND=\033[0m
LINE:=$(shell printf '=%.0s' {1..70})

# Set default docker registry user.
ifeq ($(strip $(DOCKER_REGISTRY_USER)),)
  DOCKER_REGISTRY_USER = skaorca
endif

NAME=tango_python_dev
VERSION=latest
IMAGE:=$(DOCKER_REGISTRY_USER)/$(NAME)

IMAGE:=$(DOCKER_REGISTRY_USER)/$(NAME)
TANGO_DB_ID:=$(shell docker ps -f name=tango_database -f status=running -q)
EMPTY:=
IMAGES:=$(shell docker images --format '{{.Repository}}:{{.Tag}}' | grep $(IMAGE):latest)
DEV_CONTAINER:=$(shell docker ps -f name=tango_dev_prompt -q)
IMAGES:=$(strip $(IMAGES))


ifeq ($(IMAGES),$(EMPTY))
	IMAGE_EXISTS = 0
else
	IMAGE_EXISTS = 1
endif
ifeq ($(strip $(TANGO_DB_ID)),)
	TANGO_DB_EXISTS = 0
else
	TANGO_DB_EXISTS = 1
endif
ifeq ($(strip $(DEV_CONTAINER)),)
	DEV_CONTAINER_STARTED = 0
else
	DEV_CONTAINER_STARTED = 1
endif


help:
	@echo "-$(strip $(DEV_CONTAINER))-"
	@echo "-$(DEV_CONTAINER)-"
	@echo "$(DEV_CONTAINER_STARTED)"
	@echo "--------------"
	@echo "$(IMAGES)"
	@echo "$(strip $(IMAGES))"
	@echo "$(IMAGE_EXISTS)"

.PHONY: prompt
prompt:
ifeq ($(IMAGE_EXISTS),0)
	@echo "$(CRED)ERROR: Image '$(IMAGE):latest' not found!$(CEND)"
	@echo "$(IMAGES)"
endif
ifeq ($(TANGO_DB_EXISTS),0)
	@echo "$(CRED)ERROR: Unable to start prompt, tango_database containernot found!$(CEND)"
endif
ifeq ($(DEV_CONTAINER_STARTED),1)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Connecting dev container to obtain a bash prompt"\
	 	  "(type 'exit' to quit)$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@docker exec -it $(DEV_CONTAINER) /bin/bash
else
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Starting interactive prompt (type 'exit' to quit)$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@docker run --rm -ti \
		--name tango_dev_prompt \
		--network=container:$(TANGO_DB_ID) \
		-v $(PWD):$(PWD):rw \
		-w $(PWD) \
		-e TANGO_HOST=localhost:10000 \
		-e HOME=$(PWD) \
		--entrypoint=/bin/bash \
		$(IMAGE):$(VERSION)
endif

.PHONY: itango
itango:
ifeq ($(IMAGE_EXISTS),0)
	@echo "$(CRED)ERROR: Image '$(IMAGE):latest' not found!$(CEND)"
endif
ifeq ($(TANGO_DB_EXISTS),0)
	@echo "$(CRED)ERROR: Unable to start prompt, tango_database containernot found!$(CEND)"
endif
ifeq ($(DEV_CONTAINER_STARTED),1)
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Connecting dev container to start iTango (type 'exit' to quit)$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@docker exec -it $(DEV_CONTAINER) itango3
else
	@echo "$(CRED)$(LINE)$(CEND)"
	@echo "$(CBLUE)Starting iTango prompt (type 'exit' to quit)$(CEND)"
	@echo "$(CRED)$(LINE)$(CEND)"
	@docker run --rm -ti \
		--name tango_dev_prompt \
		--network=container:$(TANGO_DB_ID) \
		-v $(PWD):$(PWD):rw \
		-w $(PWD) \
		-e TANGO_HOST=localhost:10000 \
		-e HOME=$(PWD) \
		--entrypoint=/usr/bin/itango3 \
		$(IMAGE):$(VERSION)
endif
