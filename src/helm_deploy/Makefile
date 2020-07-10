NAME := helm-deploy
VERSION := $(shell cat version.txt)

include ../make/Makefile

.PHONY: chart-repo

chart-repo:
	helm package charts/* -d chart-repo
	helm repo index chart-repo
