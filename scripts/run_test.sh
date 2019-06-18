#!/usr/bin/env bash
RED='\033[0;31m'
NC='\033[0m'

DIR="$1"
OPTIONS=("${@:2}")

if [[ -n "${OPTIONS[*]}" && "${OPTIONS[0]}" == "--tests-only" ]]; then
    OPTIONS=("${OPTIONS[@]:1}")
    CMD="python3 -m pytest -s -vv \
        --rootdir=. \
        ${OPTIONS[*]} \
        ${DIR}"
elif [[ -n "${OPTIONS[*]}" && "${OPTIONS[0]}" == "--no-cov" ]]; then
    OPTIONS=("${OPTIONS[@]:1}")
    CMD="python3 -m pytest -s -vv \
        --rootdir=. \
        --pylint \
        --pylint-rcfile=./scripts/.pylintrc \
        --codestyle \
        --docstyle \
        ${OPTIONS[*]} \
        ${DIR}"
elif [[ -n "${OPTIONS[*]}" ]]; then
    CMD="python3 -m pytest -s -vv \
        --rootdir=. \
        --pylint \
        --pylint-rcfile=./scripts/.pylintrc \
        --codestyle \
        --docstyle \
        --cov-config=./scripts/setup.cfg \
        --cov-append \
        --cov-branch \
        --no-cov-on-fail \
        --cov=${DIR} \
        ${OPTIONS[*]} \
        ${DIR}"
else
    CMD="python3 -m pytest -s -vv \
        --rootdir=. \
        --pylint \
        --pylint-rcfile=./scripts/.pylintrc \
        --codestyle \
        --docstyle \
        --cov-config=./scripts/setup.cfg \
        --cov-append \
        --cov-branch \
        --no-cov-on-fail \
        --cov=${DIR} \
        ${DIR}"
fi


echo -e "${RED}---------------------------------------${NC}"
echo -e "${CMD}"
echo -e "${RED}---------------------------------------${NC}"
eval "${CMD}"
