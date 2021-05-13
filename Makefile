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

app-build: ## Build the telescope-devkit Docker image
	@bin/telescope app-build
.PHONY: app-build

app-update: ## Updates the local telescope-devkit git copy and re-builds the Docker image
	@bin/telescope app-update
.PHONY: app-update

app-shell: ## Launch a shell in a telescope-devkit container
	@bin/telescope app-shell
.PHONY: app-shell

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

install: app-build ## Build Docker image and install a `telescope` symlink in /usr/local/bin
	@echo -n "Installing symlink in /usr/local/bin/telescope ..."
	@sudo ln -sfn ${ROOT_DIR}/bin/telescope /usr/local/bin/telescope && echo " done."
.PHONY: install
