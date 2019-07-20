# Makefile based on:
# https://github.com/ska-telescope/ska-docker/blob/master/docker-compose/Makefile

# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

COMPOSE_FILES := $(wildcard *.yml)
COMPOSE_FILE_ARGS := $(foreach yml,$(COMPOSE_FILES),-f $(yml))

# If the first make argument is "start" or "stop"...
ifeq (start,$(firstword $(MAKECMDGOALS)))
  SERVICE_TARGET = true
else ifeq (stop,$(firstword $(MAKECMDGOALS)))
  SERVICE_TARGET = true
endif
ifdef SERVICE_TARGET
  # .. then use the rest as arguments for the make target
  SERVICE := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(SERVICE):;@:)
endif

.DEFAULT_GOAL := help


#
# Never use the network=host mode when running CI jobs, and add extra
# distinguishing identifiers to the network name and container names to
# prevent collisions with jobs from the same project running at the same
# time.
#
ifneq ($(CI_JOB_ID),)
NETWORK_MODE := tangonet-$(CI_JOB_ID)
CONTAINER_NAME_PREFIX := $(CI_JOB_ID)-
else
CONTAINER_NAME_PREFIX :=
endif

ifeq ($(OS),Windows_NT)
    $(error Sorry, Windows is not supported yet)
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		DISPLAY ?= :0.0
		NETWORK_MODE ?= host
		XAUTHORITY_MOUNT := /tmp/.X11-unix:/tmp/.X11-unix
		XAUTHORITY ?= /hosthome/.Xauthority
		# /bin/sh (=dash) does not evaluate 'docker network' conditionals correctly
		SHELL := /bin/bash
	endif
	ifeq ($(UNAME_S),Darwin)
		IF_INTERFACE := $(shell netstat -nr | awk '{ if ($$1 ~/default/) { print $$6} }')
		DISPLAY := $(shell ifconfig $(IF_INTERFACE) | awk '{ if ($$1 ~/inet$$/) { print $$2} }'):0
		# network_mode = host doesn't work on MacOS, so fix to the internal network
		NETWORK_MODE ?= tangonet
		XAUTHORITY_MOUNT := $(HOME)/.Xauthority:/hosthome/.Xauthority:ro
		XAUTHORITY := /hosthome/.Xauthority
	endif
endif

ifeq ($(NETWORK_MODE),host)
	TANGO_HOST := $(shell hostname):10000
	MYSQL_HOST := $(shell hostname):3306
else
	TANGO_HOST := $(CONTAINER_NAME_PREFIX)databaseds:10000
	MYSQL_HOST := $(CONTAINER_NAME_PREFIX)tangodb:3306
endif

DOCKER_COMPOSE_ARGS := MYSQL_HOST=$(MYSQL_HOST) \
	TANGO_HOST=$(TANGO_HOST) \
	CONTAINER_NAME_PREFIX=$(CONTAINER_NAME_PREFIX) \
	NETWORK_MODE=$(NETWORK_MODE)

minimal: pull ## start the base tango system
ifneq ($(NETWORK_MODE),host)
	docker network inspect $(NETWORK_MODE) &> /dev/null || ([ $$? -ne 0 ] && docker network create $(NETWORK_MODE))
endif
	$(DOCKER_COMPOSE_ARGS) docker-compose -f tango_facility.yml up -d

pull:  ## Pull latest images defined in the compose files.
	$(DOCKER_COMPOSE_ARGS) docker-compose $(COMPOSE_FILE_ARGS) pull

up: minimal  ## start the base TANGO system and prepare all services
	$(DOCKER_COMPOSE_ARGS) docker-compose $(COMPOSE_FILE_ARGS) up --no-start

down:  ## stop all services and tear down the system
	$(DOCKER_COMPOSE_ARGS) docker-compose $(COMPOSE_FILE_ARGS) down
ifneq ($(NETWORK_MODE),host)
	docker network inspect $(NETWORK_MODE) &> /dev/null && ([ $$? -eq 0 ] && docker network rm $(NETWORK_MODE)) || true
endif

start: up ## start a service (usage: make start <servicename>)
	$(DOCKER_COMPOSE_ARGS) docker-compose $(COMPOSE_FILE_ARGS) start $(SERVICE)

stop:  ## stop a service (usage: make stop <servicename>)
	$(DOCKER_COMPOSE_ARGS) docker-compose $(COMPOSE_FILE_ARGS) stop $(SERVICE)

itango_prompt: start itango  ## Start an itango prompt
	docker exec -it itango itango3

clean:  ## Clean all tangodb entries
	docker volume rm $(BASEDIR)_tangodb

.PHONY: up down minimal start stop status clean pull help itango

help:   ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
