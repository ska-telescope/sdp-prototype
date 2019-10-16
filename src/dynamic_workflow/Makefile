#
#  Makefile utility functions for the SDP Subarray Tango device
#

NAME=helm_deploy
CLASS=helm_deploy
VERSION=$(patsubst "%",%, $(shell awk -F= '/^VERSION = ".*"/{print $$2}' $(CLASS)/release.py))

include ../make/Makefile


build_package:  ## Build the python package
	@python setup.py sdist bdist_wheel
