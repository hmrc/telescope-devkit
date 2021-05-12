SHELL := /usr/bin/env bash
PWD = $(shell pwd)
ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

DOCKER_AWS_VARS = -e AWS_REGION=${AWS_REGION} -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
DOCKER_IMAGE_NAME := mdtp-telemetry/telescope-devkit:latest

default: help

help: ## The help text you're reading
	@grep --no-filename -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

# Docker targets:

docker-build: ## Build the Python3 Docker image
	@echo "Building ${DOCKER_IMAGE_NAME}..."
	@DOCKER_BUILDKIT=1 docker build . -t ${DOCKER_IMAGE_NAME}
.PHONY: docker-build

docker-run: ## Run the telescope-devkit application in a Python3 container
	@docker run ${DOCKER_AWS_VARS} -v $(PWD):/app --rm ${DOCKER_IMAGE_NAME} -h
.PHONY: docker-run

docker-sh: ## Get a shell in a Python3 container
	@docker run ${DOCKER_AWS_VARS} -it -v $(PWD):/app --rm --entrypoint=/bin/bash ${DOCKER_IMAGE_NAME}
.PHONY: sh-py35

# Poetry targets:

poetry-build: ## Builds a tarball and a wheel Python packages
	@poetry build
.PHONY: poetry-build

poetry-update: ## Update the dependencies as according to the pyproject.toml file
	@poetry update -vvv
.PHONY: poetry-update

poetry-install: ## Install the dependencies as according to the pyproject.toml file
	@poetry install
.PHONY: poetry-install

install: docker-build ## Build Docker image and install a `telescope` symlink in /usr/local/bin
	@echo -n "Installing symlink in /usr/local/bin/telescope ..."
	@ln -sfn ${ROOT_DIR}/bin/telescope /usr/local/bin/telescope && echo " done."
.PHONY: install
