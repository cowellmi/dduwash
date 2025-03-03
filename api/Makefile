include .env

## help: print this help message
.PHONY: help
help:
	@echo "Usage:"
	@sed -n "s/^##//p" ${MAKEFILE_LIST} | column -t -s ":" |  sed -e "s/^/ /"


## audit: tidy dependencies and format, vet and test all code
.PHONY: audit
audit:
	@echo "Tidying and verifying module dependencies..."
	go mod tidy
	go mod verify
	@echo "Formatting code..."
	go fmt ./...
	@echo "Vetting code..."
	go vet ./...
	staticcheck ./...
	@echo "Running tests..."
	go test -race -vet=off ./...
	

## build: build the cmd/api application
current_time = $(shell date --iso-8601=seconds)
git_description = $(shell git describe --always --dirty --tags --long;)
linker_flags = '-s -X main.BUILD_TIME=${current_time} -X main.VERSION=${git_description}'

.PHONY: build
build:
	@echo "Building cmd/api..."
	go build -ldflags=${linker_flags} -o=./bin/api ./cmd/api


## up: start the docker compose application
.PHONY: up
up:
	infisical run --projectId=${PROJECT_ID} -- docker-compose up --build


## run: run the cmd/api application
.PHONY: run
run:
	go run ./cmd/api


## db/psql: connect to the database using psql
.PHONY: db/psql
db/psql:
	psql ${DATABASE_URL}

# confirmation dialog helper
.PHONY: confirm
confirm:
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
