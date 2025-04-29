include .env

.PHONY: help
help:
	@echo "Usage:"
	@sed -n "s/^##//p" ${MAKEFILE_LIST} | column -t -s ":" |  sed -e "s/^/ /"

## up: sync to server
.PHONY: up
up: setup
	@[ -n "$$DDUWASH_SERVER" ] || (echo "Missing DDUWASH_SERVER env var" && exit 1)
	rsync -avz api cv db .env.sample docker-compose.yml $$DDUWASH_SERVER
