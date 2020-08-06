NAME := ska-sdp-lmc
PDIR := ska_sdp_lmc
VERSION := $(patsubst '%',%, $(shell awk -F' = ' '/^VERSION =/{print $$2}' $(PDIR)/release.py))

include ../make/Makefile
